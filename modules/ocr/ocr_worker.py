# -*- coding: utf-8 -*-
"""OCR子进程工作器

将OCR提取任务放在独立子进程中运行，避免主进程因段错误崩溃。
子进程完成后自动退出，释放所有模型内存。
"""

import logging
import multiprocessing
import queue

logger = logging.getLogger(__name__)


def _ocr_worker_func(pdf_path, pages, temp_images_dir, lang, use_gpu, result_queue):
    """子进程工作函数

    Args:
        pdf_path: PDF文件路径
        pages: 页码列表
        temp_images_dir: 临时图像目录
        lang: OCR语言
        use_gpu: 是否使用GPU
        result_queue: 结果队列
    """
    # Set PaddlePaddle environment variables BEFORE importing paddle
    import os
    os.environ['FLAGS_fraction_of_gpu_memory_to_use'] = '0.5'
    os.environ['CPU_NUM'] = '2'
    
    # Intel MKL/DNN 纯 CPU 强制环境变量 - 禁止矢量加速/GPU 尝试
    os.environ['OMP_NUM_THREADS'] = '2'
    os.environ['MKL_NUM_THREADS'] = '2'
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
    os.environ['DNNL_VERBOSE'] = '0'
    os.environ['PADDLE_WITH_GPU'] = 'OFF'
    os.environ['PADDLE_ONLY_CPU'] = '1'
    os.environ['KMP_AFFINITY'] = 'disabled'
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    os.environ['MKL_THREADING_LAYER'] = 'sequential'
    os.environ['OPENBLAS_NUM_THREADS'] = '2'

    # 子进程日志配置（spawn 模式不继承父进程 logging）
    # 必须在导入 paddleocr 之前配置，否则所有 logger.info() 静默丢弃
    import logging as _logging
    _logging.basicConfig(
        level=_logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            _logging.FileHandler('app.log'),
            _logging.StreamHandler()
        ]
    )

    # 纵深防御：为 paddle_extractor logger 显式配置独立 handler，
    # 防止 PPStructureV3 破坏根 logger 或禁用传播后日志丢失
    _pe_logger = _logging.getLogger('modules.ocr.paddle_extractor')
    _pe_logger.setLevel(_logging.INFO)
    _pe_format = _logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    _pe_fh = _logging.FileHandler('app.log')
    _pe_fh.setFormatter(_pe_format)
    _pe_sh = _logging.StreamHandler()
    _pe_sh.setFormatter(_pe_format)
    _pe_logger.addHandler(_pe_fh)
    _pe_logger.addHandler(_pe_sh)
    _pe_logger.propagate = True

    # 为 ocr_worker logger 显式配置 handler
    _ow_logger = _logging.getLogger('modules.ocr.ocr_worker')
    _ow_logger.setLevel(_logging.INFO)
    _ow_handler_format = _logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    _ow_fh = _logging.FileHandler('app.log')
    _ow_fh.setFormatter(_ow_handler_format)
    _ow_logger.addHandler(_ow_fh)
    _ow_sh = _logging.StreamHandler()
    _ow_sh.setFormatter(_ow_handler_format)
    _ow_logger.addHandler(_ow_sh)
    _ow_logger.propagate = True

    try:
        from modules.ocr.paddle_extractor import PaddleOcrExtractor
        extractor = PaddleOcrExtractor(lang=lang, use_gpu=False)
        result = extractor.extract_from_pdf(pdf_path, pages=pages, temp_images_dir=temp_images_dir)
        # Serialize result to dict for pickling
        result_queue.put(('success', result.to_dict()))
    except Exception as e:
        logger.error(f"OCR子进程异常: {str(e)}", exc_info=True)
        result_queue.put(('error', str(e)))


def run_ocr_in_subprocess(pdf_path, pages=None, temp_images_dir=None,
                          lang='ch', use_gpu=False, timeout=600):
    """在子进程中运行OCR提取

    Args:
        pdf_path: PDF文件路径
        pages: 页码列表（1-based）
        temp_images_dir: 临时图像目录
        lang: OCR语言
        use_gpu: 是否使用GPU
        timeout: 超时时间（秒），默认600秒

    Returns:
        PdfExtraction: 提取结果

    Raises:
        RuntimeError: OCR子进程崩溃或超时
    """
    ctx = multiprocessing.get_context('spawn')
    result_queue = ctx.Queue()

    process = ctx.Process(
        target=_ocr_worker_func,
        args=(pdf_path, pages, temp_images_dir, lang, use_gpu, result_queue),
        daemon=True
    )

    process.start()
    process.join(timeout=timeout)

    if process.is_alive():
        process.terminate()
        process.join(timeout=5)
        if process.is_alive():
            process.kill()
            process.join()
        raise RuntimeError(f"OCR处理超时（{timeout}秒），已终止子进程")

    if process.exitcode != 0:
        raise RuntimeError(
            f"OCR子进程异常退出（exitcode={process.exitcode}），"
            "可能是内存不足导致段错误。建议关闭部分识别功能或增加系统内存。"
        )

    try:
        status, data = result_queue.get(timeout=5)
    except queue.Empty:
        raise RuntimeError("OCR子进程未返回结果，可能已崩溃")

    if status == 'error':
        raise RuntimeError(f"OCR处理失败: {data}")

    # Reconstruct PdfExtraction from dict
    from models.extraction import PdfExtraction
    return PdfExtraction.from_dict(data)
