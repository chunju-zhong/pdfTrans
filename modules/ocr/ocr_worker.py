# -*- coding: utf-8 -*-
import copy
import logging
import multiprocessing
import os
import queue
import threading
import time

import psutil

logger = logging.getLogger(__name__)

STATUS_HEARTBEAT = 'heartbeat'
STATUS_STEP_START = 'step_start'
STATUS_STEP_PROGRESS = 'step_progress'
STATUS_STEP_COMPLETE = 'step_complete'
STATUS_PAGE_RESULT = 'page_result'


class OcrRetryableError(RuntimeError):
    pass


class OcrFatalError(RuntimeError):
    pass


def _heartbeat_sender(status_queue, stop_event):
    while not stop_event.is_set():
        try:
            mem_mb = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
            status_queue.put((STATUS_HEARTBEAT, {
                'pid': os.getpid(),
                'memory_mb': round(mem_mb, 1),
                'timestamp': time.time(),
            }))
        except Exception:
            logger.debug("Heartbeat sender failed", exc_info=True)
        stop_event.wait(15)


def _setup_subprocess_logger(name):
    _log = logging.getLogger(name)
    _log.setLevel(logging.INFO)
    _fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    _fh = logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'app.log'))
    _fh.setFormatter(_fmt)
    _sh = logging.StreamHandler()
    _sh.setFormatter(_fmt)
    _log.addHandler(_fh)
    _log.addHandler(_sh)
    _log.propagate = False
    return _log


def _ocr_worker_func(pdf_path, pages, temp_images_dir, lang, use_gpu,
                     result_queue, status_queue, ocr_params, skip_pages=None):
    thread_params = ocr_params.get('thread_params', {}) if ocr_params else {}
    os.environ['FLAGS_fraction_of_gpu_memory_to_use'] = '0.5'
    os.environ['CPU_NUM'] = thread_params.get('CPU_NUM', '2')
    os.environ['OMP_NUM_THREADS'] = thread_params.get('OMP_NUM_THREADS', '2')
    os.environ['MKL_NUM_THREADS'] = thread_params.get('MKL_NUM_THREADS', '2')
    _gpu_enabled = ocr_params.get('use_gpu', False) if ocr_params else False
    if not _gpu_enabled:
        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
        os.environ['PADDLE_WITH_GPU'] = 'OFF'
        os.environ['PADDLE_ONLY_CPU'] = '1'
    os.environ['DNNL_VERBOSE'] = '0'
    os.environ['KMP_AFFINITY'] = 'disabled'
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    os.environ['MKL_THREADING_LAYER'] = 'sequential'
    os.environ['OPENBLAS_NUM_THREADS'] = thread_params.get('OPENBLAS_NUM_THREADS', '2')

    if ocr_params is None:
        ocr_params = {}
    ocr_params['cpu_threads'] = int(thread_params.get('OMP_NUM_THREADS', '2'))

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'app.log')),
            logging.StreamHandler()
        ]
    )

    _setup_subprocess_logger('modules.ocr.paddle_extractor')
    _setup_subprocess_logger('modules.ocr.ocr_worker')

    stop_event = threading.Event()
    heartbeat_thread = threading.Thread(
        target=_heartbeat_sender,
        args=(status_queue, stop_event),
        daemon=True,
    )
    heartbeat_thread.start()

    try:
        from modules.ocr.paddle_extractor import PaddleOcrExtractor
        memory_params = ocr_params.get('memory_params', {}) if ocr_params else {}
        skip_table = ocr_params.get('skip_table', False) if ocr_params else False

        def status_callback(msg_type, payload):
            try:
                status_queue.put((msg_type, payload))
            except Exception:
                pass

        extractor = PaddleOcrExtractor(
            lang=lang,
            use_gpu=_gpu_enabled,
            memory_params=memory_params,
            skip_table=skip_table,
            ocr_params=ocr_params,
        )
        result = extractor.extract_from_pdf(
            pdf_path, pages=pages, temp_images_dir=temp_images_dir,
            status_callback=status_callback,
            skip_pages=skip_pages,
        )
        result_queue.put(('success', result.to_dict()))
    except Exception as e:
        logger.error(f"OCR子进程异常: {str(e)}", exc_info=True)
        result_queue.put(('error', str(e)))
    finally:
        stop_event.set()
        heartbeat_thread.join(timeout=3)


def _degrade_params(current_params, attempt):
    from modules.ocr.system_profiler import get_ocr_params

    if current_params is None:
        current_params = get_ocr_params(page_count=1)

    degraded = copy.deepcopy(current_params)

    thread_params = dict(degraded.get('thread_params', {}))
    for key in ('CPU_NUM', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
        current_val = int(thread_params.get(key, '2'))
        thread_params[key] = str(max(1, current_val - 1 - attempt))
    degraded['thread_params'] = thread_params

    memory_params = dict(degraded.get('memory_params', {}))
    memory_params['memory_factor'] = round(memory_params.get('memory_factor', 0.55) * 0.8, 2)
    for cap_key in ('memory_cap_layout', 'memory_cap_table', 'memory_cap_formula'):
        if cap_key in memory_params:
            memory_params[cap_key] = int(memory_params[cap_key] * 0.8)
    degraded['memory_params'] = memory_params

    current_dpi = degraded.get('render_dpi', 120)
    degraded['render_dpi'] = max(72, current_dpi - 20)

    timeout_params = dict(degraded.get('timeout_params', {}))
    current_max_total = timeout_params.get('max_total_time', 1800)
    timeout_params['max_total_time'] = int(current_max_total * 2.0)
    degraded['timeout_params'] = timeout_params

    degraded['skip_table'] = attempt >= 1
    degraded['skip_formula'] = attempt >= 2

    logger.info(
        "参数降级(第%d次重试): 线程=%s, DPI=%d, 内存因子=%.2f, 超时=%ds, skip_table=%s, skip_formula=%s",
        attempt + 1,
        thread_params.get('CPU_NUM'),
        degraded['render_dpi'],
        memory_params['memory_factor'],
        timeout_params['max_total_time'],
        degraded['skip_table'],
        degraded['skip_formula'],
    )
    return degraded


def _estimate_page_count(pdf_path):
    try:
        import fitz
        with fitz.open(pdf_path) as doc:
            return len(doc)
    except Exception:
        return 10


def _terminate_process(process):
    process.terminate()
    process.join(timeout=5)
    if process.is_alive():
        process.kill()
        process.join()


def _assemble_extraction(completed_pages, total_pages, all_page_nums):
    """从流式累积的页面结果组装最终 PdfExtraction

    Args:
        completed_pages: dict[int, dict] 页码 -> {text_blocks, tables, images}
        total_pages: PDF总页数
        all_page_nums: 所有目标页码列表

    Returns:
        PdfExtraction
    """
    from models.extraction import PdfPage, PdfExtraction, TextBlock, PdfTable, PdfImage

    pdf_pages = []
    all_tables = []
    all_images = []

    for page_num in all_page_nums:
        page_data = completed_pages.get(page_num, {})
        text_blocks = [TextBlock.from_dict(d) for d in page_data.get('text_blocks', [])]
        for i, tb in enumerate(text_blocks):
            tb.block_no = i
        pdf_pages.append(PdfPage(page_num=page_num, text_blocks=text_blocks))

        page_tables = [PdfTable.from_dict(d) for d in page_data.get('tables', [])]
        all_tables.extend(page_tables)

        page_images = [PdfImage.from_dict(d) for d in page_data.get('images', [])]
        all_images.extend(page_images)

    for i, table in enumerate(all_tables):
        table.table_idx = i
    for i, img in enumerate(all_images):
        img.image_idx = i

    return PdfExtraction(
        total_pages=total_pages,
        pages=pdf_pages,
        tables=all_tables,
        images=all_images,
    )


def _run_ocr_once(pdf_path, pages, temp_images_dir, lang, use_gpu,
                  heartbeat_timeout, max_total_time, ocr_params,
                  config_max_total_time=None, stall_timeout=1800,
                  progress_callback=None, skip_pages=None):
    """运行一次OCR子进程，支持流式结果累积和断点续传

    Returns:
        tuple[dict[int, dict], list[int]]: (completed_pages, completed_page_nums)
            completed_pages: 页码 -> {text_blocks, tables, images} (dict格式)
            completed_page_nums: 已完成的页码列表
    """
    ctx = multiprocessing.get_context('spawn')
    result_queue = ctx.Queue()
    status_queue = ctx.Queue()

    process = ctx.Process(
        target=_ocr_worker_func,
        args=(pdf_path, pages, temp_images_dir, lang, use_gpu,
              result_queue, status_queue, ocr_params, skip_pages),
        daemon=True,
    )

    process.start()
    start_time = time.time()
    last_heartbeat_time = time.time()
    last_progress_time = time.time()
    last_pages_done = -1
    last_progress = None
    completed_pages = {}

    while True:
        elapsed = time.time() - start_time
        if elapsed > max_total_time:
            _terminate_process(process)
            if completed_pages:
                logger.warning(
                    "OCR超时但已有%d页结果，保留部分结果",
                    len(completed_pages),
                )
                return completed_pages, sorted(completed_pages.keys())
            raise OcrRetryableError(
                f"OCR处理超过最大时间（{max_total_time}秒），已终止子进程"
            )

        # 非阻塞检查 result_queue
        try:
            status, data = result_queue.get_nowait()
            if status == 'success':
                # 子进程完成，合并流式结果（流式结果可能更完整）
                logger.info("OCR子进程完成确认，已累积%d页流式结果", len(completed_pages))
                # 等待子进程退出
                process.join(timeout=10)
                return completed_pages, sorted(completed_pages.keys())
            elif status == 'error':
                if completed_pages:
                    logger.warning(
                        "OCR子进程报错但已有%d页结果，保留部分结果: %s",
                        len(completed_pages), data,
                    )
                    process.join(timeout=5)
                    return completed_pages, sorted(completed_pages.keys())
                raise OcrRetryableError(f"OCR处理失败: {data}")
        except queue.Empty:
            pass

        if not process.is_alive():
            # 子进程已退出，再次检查 result_queue
            try:
                status, data = result_queue.get(timeout=5)
                if status == 'success':
                    logger.info("OCR子进程完成确认，已累积%d页流式结果", len(completed_pages))
                    return completed_pages, sorted(completed_pages.keys())
                elif status == 'error':
                    if completed_pages:
                        logger.warning(
                            "OCR子进程报错但已有%d页结果，保留部分结果: %s",
                            len(completed_pages), data,
                        )
                        return completed_pages, sorted(completed_pages.keys())
                    raise OcrRetryableError(f"OCR处理失败: {data}")
            except queue.Empty:
                pass

            # 子进程退出且无结果
            if process.exitcode != 0:
                if completed_pages:
                    logger.warning(
                        "OCR子进程异常退出(exitcode=%d)但已有%d页结果，保留部分结果",
                        process.exitcode, len(completed_pages),
                    )
                    return completed_pages, sorted(completed_pages.keys())
                raise OcrRetryableError(
                    f"OCR子进程异常退出（exitcode={process.exitcode}），"
                    "可能是内存不足导致段错误。建议关闭部分识别功能或增加系统内存。"
                )
            if completed_pages:
                logger.warning(
                    "OCR子进程退出但已有%d页结果，保留部分结果",
                    len(completed_pages),
                )
                return completed_pages, sorted(completed_pages.keys())
            raise OcrRetryableError("OCR子进程未返回结果，可能已崩溃")

        try:
            msg_type, payload = status_queue.get(timeout=5)
            last_heartbeat_time = time.time()
            if msg_type == STATUS_HEARTBEAT:
                logger.debug(
                    "OCR子进程心跳: pid=%d, 内存=%.0fMB",
                    payload.get('pid', 0),
                    payload.get('memory_mb', 0),
                )
            elif msg_type == STATUS_PAGE_RESULT:
                page_num = payload.get('page_num')
                completed_pages[page_num] = {
                    'text_blocks': payload.get('text_blocks', []),
                    'tables': payload.get('tables', []),
                    'images': payload.get('images', []),
                }
                logger.debug("流式收到第%d页结果，已累积%d页", page_num, len(completed_pages))
            elif msg_type == STATUS_STEP_START:
                logger.info(
                    "OCR步骤%d开始: %s, 共%d页",
                    payload.get('step', 0),
                    payload.get('step_name', ''),
                    payload.get('total_pages', 0),
                )
                if progress_callback: progress_callback('step_start', payload)
            elif msg_type == STATUS_STEP_PROGRESS:
                last_progress = payload
                pages_done = payload.get('pages_done', 0)
                total_pages = payload.get('total_pages', 0)
                logger.info(
                    "OCR步骤%d进度: %d/%d页, 当前第%d页",
                    payload.get('step', 0),
                    pages_done,
                    total_pages,
                    payload.get('page_num', 0),
                )
                if progress_callback: progress_callback('step_progress', payload)
                if pages_done > 0 and total_pages > 0 and config_max_total_time is not None:
                    elapsed = time.time() - start_time
                    avg_time_per_page = elapsed / pages_done
                    remaining_pages = total_pages - pages_done
                    estimated_remaining = avg_time_per_page * remaining_pages * 1.5
                    needed_total = elapsed + estimated_remaining
                    dynamic_cap = config_max_total_time * 2
                    if needed_total > max_total_time and needed_total <= dynamic_cap:
                        old_max = max_total_time
                        max_total_time = needed_total
                        logger.info(
                            "动态延长OCR超时: %ds -> %ds (已完成%d/%d页, 平均%.1fs/页, 预估剩余%.0fs)",
                            old_max, max_total_time,
                            pages_done, total_pages,
                            avg_time_per_page, estimated_remaining,
                        )
                if pages_done > last_pages_done:
                    last_progress_time = time.time()
                    last_pages_done = pages_done
            elif msg_type == STATUS_STEP_COMPLETE:
                logger.info(
                    "OCR步骤%d完成: %s, 耗时%.1f秒",
                    payload.get('step', 0),
                    payload.get('step_name', ''),
                    payload.get('duration_sec', 0),
                )
                if progress_callback: progress_callback('step_complete', payload)
        except queue.Empty:
            pass

        # 心跳超时和停滞超时仅在子进程存活时检查
        if process.is_alive():
            heartbeat_silence = time.time() - last_heartbeat_time
            if heartbeat_timeout > 0 and heartbeat_silence > heartbeat_timeout:
                logger.error(
                    "OCR子进程心跳中断%.0f秒(超过阈值%d秒)，判定子进程死机。最后进度: %s",
                    heartbeat_silence,
                    heartbeat_timeout,
                    last_progress,
                )
                _terminate_process(process)
                if completed_pages:
                    logger.warning(
                        "心跳超时但已有%d页结果，保留部分结果",
                        len(completed_pages),
                    )
                    return completed_pages, sorted(completed_pages.keys())
                raise OcrRetryableError(
                    f"OCR子进程心跳中断{heartbeat_silence:.0f}秒，判定死机已终止。"
                    f"最后进度: {last_progress}"
                )

            stall_duration = time.time() - last_progress_time
            if stall_duration > stall_timeout:
                logger.error(
                    "OCR进度停滞%.0f秒(超过阈值%d秒)，判定异常已终止。最后进度: %s",
                    stall_duration, stall_timeout, last_progress,
                )
                _terminate_process(process)
                if completed_pages:
                    logger.warning(
                        "进度停滞但已有%d页结果，保留部分结果",
                        len(completed_pages),
                    )
                    return completed_pages, sorted(completed_pages.keys())
                raise OcrRetryableError(
                    f"OCR进度停滞{stall_duration:.0f}秒，判定异常已终止"
                )


def run_ocr_in_subprocess(pdf_path, pages=None, temp_images_dir=None,
                          lang='ch', use_gpu=False, timeout=None,
                          heartbeat_timeout=None, max_total_time=None,
                          ocr_params=None, max_retries=None, retry_backoff=None,
                          progress_callback=None):
    if not os.path.exists(pdf_path):
        raise OcrFatalError(f"PDF文件不存在: {pdf_path}")

    from config import config

    if max_retries is None:
        max_retries = getattr(config, 'OCR_MAX_RETRIES', 2)
    if retry_backoff is None:
        retry_backoff = getattr(config, 'OCR_RETRY_BACKOFF', 5.0)

    if ocr_params is None:
        dynamic_enabled = getattr(config, 'OCR_DYNAMIC_PARAMS', True)
        if dynamic_enabled:
            from modules.ocr.system_profiler import get_ocr_params
            page_count = len(pages) if pages else _estimate_page_count(pdf_path)
            ocr_params = get_ocr_params(page_count=page_count)

    config_max_total_time = getattr(config, 'OCR_MAX_TOTAL_TIME', 7200)
    stall_timeout = getattr(config, 'OCR_STALL_TIMEOUT', 1800)

    if ocr_params:
        timeout_params = ocr_params.get('timeout_params', {})
        if heartbeat_timeout is None:
            heartbeat_timeout = timeout_params.get('heartbeat_timeout', 0)
        if max_total_time is None:
            max_total_time = timeout_params.get('max_total_time', 1800)
    else:
        if heartbeat_timeout is None:
            heartbeat_timeout = 0
        if max_total_time is None:
            max_total_time = timeout if timeout else 600

    max_total_time = min(max_total_time, config_max_total_time)

    # 确定所有目标页码
    if pages:
        all_page_nums = sorted(pages)
    else:
        try:
            import fitz
            with fitz.open(pdf_path) as doc:
                all_page_nums = list(range(1, len(doc) + 1))
        except Exception:
            all_page_nums = None

    total_pages = len(all_page_nums) if all_page_nums else _estimate_page_count(pdf_path)

    last_error = None
    current_params = ocr_params
    current_backoff = retry_backoff
    completed_pages = {}
    completed_page_nums = []

    for attempt in range(max_retries + 1):
        try:
            # 计算剩余需要处理的页面
            remaining_pages = [p for p in (all_page_nums or []) if p not in completed_pages] if all_page_nums else None

            if remaining_pages is not None and len(remaining_pages) == 0:
                logger.info("所有页面已通过流式回传完成，无需再次处理")
                break

            new_pages, new_page_nums = _run_ocr_once(
                pdf_path, remaining_pages, temp_images_dir, lang, use_gpu,
                heartbeat_timeout, max_total_time, current_params,
                config_max_total_time=config_max_total_time,
                stall_timeout=stall_timeout,
                progress_callback=progress_callback,
                skip_pages=completed_page_nums if completed_page_nums else None,
            )

            # 合并结果
            completed_pages.update(new_pages)
            completed_page_nums = sorted(completed_pages.keys())

            if attempt > 0:
                logger.info("OCR第%d次重试成功，新增%d页，累计%d页", attempt, len(new_page_nums), len(completed_page_nums))

            # 检查是否所有页面都已完成
            if all_page_nums and set(all_page_nums).issubset(set(completed_page_nums)):
                break
            # 如果无法确定总页数（all_page_nums is None），成功返回即视为完成
            if all_page_nums is None and new_page_nums:
                break

        except OcrRetryableError as e:
            last_error = e
            if attempt < max_retries:
                logger.warning(
                    "OCR第%d次尝试失败: %s，已有%d页结果，%.1f秒后重试（剩余%d次）",
                    attempt + 1,
                    str(e),
                    len(completed_page_nums),
                    current_backoff,
                    max_retries - attempt,
                )
                time.sleep(current_backoff)
                current_params = _degrade_params(current_params, attempt)
                degraded_timeout = current_params.get('timeout_params', {}).get('max_total_time')
                if degraded_timeout:
                    max_total_time = degraded_timeout
                current_backoff = current_backoff * 1.5
            else:
                logger.error(
                    "OCR已重试%d次仍失败，最后错误: %s，已保留%d页结果",
                    max_retries,
                    str(e),
                    len(completed_page_nums),
                )
        except OcrFatalError:
            raise

    if not completed_pages:
        raise last_error

    # 从流式结果组装最终 PdfExtraction
    if all_page_nums:
        missing_pages = [p for p in all_page_nums if p not in completed_pages]
        if missing_pages:
            logger.warning("OCR完成但以下页面缺失: %s", missing_pages)
    else:
        all_page_nums = sorted(completed_pages.keys())

    return _assemble_extraction(completed_pages, total_pages, all_page_nums)
