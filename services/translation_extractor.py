from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor

from modules.pdf_extractor import PdfExtractor
from config import config
from utils.file_utils import remove_file
from utils.logging_config import get_logger

logger = get_logger(__name__)


class TranslationExtractor:
    """提取逻辑：负责PDF内容的提取"""

    def __init__(self, executor: ThreadPoolExecutor):
        self.executor = executor

    def extract_pdf_content(self, task, input_filepath, page_range, extract_chapter=True, output_path=None, tmp_dir=None, ocr_mode=False, ocr_engine='paddleocr', ocr_lang='ch', translator_type='aiping', source_lang=None, ocr_llm_model=None):
        """提取PDF内容

        Args:
            task: 任务对象
            input_filepath: 输入文件路径
            page_range: 页码范围，格式如"1-5,7,9-10"或空字符串表示所有页
            extract_chapter: 是否提取章节信息 (默认: True)
            output_path: 输出文件路径，用于确定临时图像目录位置
            tmp_dir: 临时文件目录，优先使用
            ocr_mode: 是否启用OCR模式提取扫描版PDF (默认: False)
            ocr_engine: OCR引擎类型 (默认: 'paddleocr')
            ocr_lang: OCR识别语言 (默认: 'ch')
            source_lang: 源语言代码，用于LLM OCR提示 (默认: None)
            ocr_llm_model: LLM OCR模型名称 (默认: None)

        Returns:
            tuple: (text_blocks, tables, extracted_images, chapters, all_page_nums)
        """
        # 使用lazy import确保测试@patch能生效
        from services.translation_service import PdfExtractor as _PdfExtractor
        from services.translation_service import remove_file as _remove_file
        from services.translation_service import os as _os
        logger.info(f"任务 {task.task_id} extract_pdf_content方法接收到的extract_chapter值: {extract_chapter}")
        task.update_phase_progress('extraction', 0, '正在提取PDF文本...')

        # 1.1 创建PdfExtractor实例
        logger.info(f"任务 {task.task_id} 开始创建PdfExtractor实例")
        pdf_extractor = _PdfExtractor(
            input_filepath,
            ocr_mode=ocr_mode,
            ocr_engine=ocr_engine,
            ocr_lang=ocr_lang,
            translator_type=translator_type,
            source_lang=source_lang,
            ocr_llm_model=ocr_llm_model,
        )
        total_pages = pdf_extractor.total_pages
        logger.info(f"任务 {task.task_id} 获取总页数完成: {total_pages}")

        if task.is_canceled():
            # 清理临时文件
            _remove_file(input_filepath)
            logger.info(f"任务 {task.task_id} 被取消，已清理临时文件")
            return None

        # 1.2 解析页码范围
        target_pages = self._parse_page_range(page_range, total_pages)
        sorted_target_pages = sorted(target_pages)
        logger.info(f"任务 {task.task_id} 需要翻译的页码: {sorted_target_pages}")

        # 1.3 确定临时图像目录
        # 优先使用 tmp_dir，其次是 output_path 所在目录
        temp_images_dir = tmp_dir
        if not temp_images_dir and output_path:
            temp_images_dir = _os.path.dirname(output_path)
            if not temp_images_dir:
                temp_images_dir = _os.getcwd()
        if temp_images_dir:
            logger.info(f"使用临时图像目录: {temp_images_dir}")

        # 1.4 根据页码范围提取PDF文本
        logger.info(f"任务 {task.task_id} 开始提取PDF文本")
        ocr_progress_callback = None
        if ocr_mode:
            # 步骤1+2已合并为逐页处理，进度直接按页数计算
            def _ocr_progress_cb(msg_type, payload):
                step = payload.get('step', 1)
                step_name = payload.get('step_name', '')
                pages_done = payload.get('pages_done', 0)
                total_pages = payload.get('total_pages', 1)

                if msg_type == 'step_start':
                    ocr_progress = 0.0
                elif msg_type == 'step_complete':
                    ocr_progress = 1.0
                else:
                    ocr_progress = pages_done / max(total_pages, 1)

                phase_percent = int(ocr_progress * 100)

                if msg_type == 'step_start':
                    msg = f"OCR提取: {step_name}开始"
                elif msg_type == 'step_complete':
                    msg = f"OCR提取: {step_name}完成"
                else:
                    msg = f"OCR提取: {step_name} {pages_done}/{total_pages}页"

                task.update_phase_progress('extraction', phase_percent, msg)

            ocr_progress_callback = _ocr_progress_cb
        extracted_content, missing_pages = pdf_extractor.extract(pages=list(target_pages), extract_chapter=extract_chapter, temp_images_dir=temp_images_dir, progress_callback=ocr_progress_callback)
        if missing_pages:
            task.add_warning(f"OCR提取失败，以下页面内容缺失: {missing_pages}", context={"process": "extraction", "missing_pages": missing_pages})
            logger.warning(f"任务 {task.task_id} OCR提取失败，以下页面内容缺失: {missing_pages}")
        if missing_pages and set(missing_pages) >= set(target_pages):
            logger.warning(f"任务 {task.task_id} 所有目标页面OCR提取均失败")
            task.update_phase_progress('extraction', 100, '所有页面OCR提取失败')
            return None
        logger.info(f"任务 {task.task_id} PDF文本提取完成")

        # 保存提取的图像信息
        extracted_images = extracted_content.images
        logger.info(f"任务 {task.task_id} 提取到 {len(extracted_images)} 个图像")

        # 提取表格信息
        tables = extracted_content.tables
        logger.info(f"任务 {task.task_id} 提取到 {len(tables)} 个表格")

        # 添加blocks信息日志
        logger.info(f"任务 {task.task_id} 提取到的blocks信息: 总页数={extracted_content.total_pages}")
        # 不再使用'blocks'键，而是直接使用pages属性
        total_blocks = sum(len(page.text_blocks) for page in extracted_content.pages)
        logger.info(f"任务 {task.task_id} 共提取到 {total_blocks} 个完整文本块")

        # 检查是否有实际提取到的页面（处理页码范围不存在的情况）
        if not extracted_content.pages:
            logger.warning(f"任务 {task.task_id} 没有找到需要翻译的文本块")
            task.update_phase_progress('extraction', 100, '没有找到需要翻译的文本块')
            return None

        # 检查提取的页面是否与目标页码匹配（处理测试中模拟提取器的情况）
        has_matching_pages = any(page.page_num in target_pages for page in extracted_content.pages)
        if not has_matching_pages:
            logger.warning(f"任务 {task.task_id} 没有找到需要翻译的文本块")
            task.update_phase_progress('extraction', 100, '没有找到需要翻译的文本块')
            return None

        # 收集所有页码（包括没有文本块的页面）
        all_page_nums = sorted(set(page.page_num for page in extracted_content.pages))
        logger.info(f"任务 {task.task_id} 所有页码: {all_page_nums}")

        # 收集所有页面的所有块，方便上下文查找
        # 只收集正文块，简化后续流程
        text_blocks = []
        total_body_blocks = 0
        total_non_body_blocks = 0
        page_count = len(extracted_content.pages)
        for i, page in enumerate(extracted_content.pages):
            if not ocr_mode:
                phase_percent = int((i + 1) / page_count * 100)
                task.update_phase_progress('extraction', phase_percent, f'正在提取第 {page.page_num} 页...')

            page_body_count = 0
            page_non_body_count = 0
            for text_block in page.text_blocks:
                if text_block.is_body_text:
                    text_blocks.append(text_block)
                    page_body_count += 1
                else:
                    page_non_body_count += 1
            total_body_blocks += page_body_count
            total_non_body_blocks += page_non_body_count
            logger.info(f"任务 {task.task_id} 第 {page.page_num} 页提取统计: 总块数={len(page.text_blocks)}, 正文块={page_body_count}, 非正文块={page_non_body_count}")

        logger.info(f"任务 {task.task_id} 提取完成统计: 总页数={page_count}, 正文块总数={total_body_blocks}, 非正文块总数={total_non_body_blocks}")
        pages_without_body = [page.page_num for page in extracted_content.pages if not any(tb.is_body_text for tb in page.text_blocks)]
        if pages_without_body:
            logger.warning(f"任务 {task.task_id} 以下页面无正文块，可能存在内容丢失: {pages_without_body}")
            task.add_warning(f"以下页面无正文内容: {pages_without_body}", context={"process": "extraction"})

        if not text_blocks or len(text_blocks) <= 0:
            logger.warning(f"任务 {task.task_id} 没有找到需要翻译的文本块")
            task.update_phase_progress('extraction', 100, '没有找到需要翻译的文本块')
            return None

        # 获取章节信息
        chapters = []
        if extract_chapter and hasattr(pdf_extractor, 'get_chapters'):
            chapters = pdf_extractor.get_chapters()
            logger.info(f"任务 {task.task_id} 获取到 {len(chapters)} 个章节")
        elif not extract_chapter:
            logger.info(f"任务 {task.task_id} 跳过章节提取")

        return text_blocks, tables, extracted_images, chapters, all_page_nums

    def _parse_page_range(self, page_range_str: str | None, total_pages: int) -> set:
        """解析页码范围字符串，返回页码集合

        Args:
            page_range_str (str): 页码范围字符串，格式如"1-5,7,9-10"
            total_pages (int): PDF总页数

        Returns:
            set: 包含所有指定页码的集合
        """
        if page_range_str and len(page_range_str) > 1000:
            raise ValueError("页码范围字符串过长，最大允许 1000 字符")
        if not page_range_str:
            return set(range(1, total_pages + 1))

        pages = set()
        ranges = page_range_str.split(',')

        for r in ranges:
            r = r.strip()
            if '-' in r:
                try:
                    start, end = map(int, r.split('-'))
                    start = max(1, start)
                    end = min(total_pages, end)
                    if start <= end:
                        pages.update(range(start, end + 1))
                except ValueError:
                    continue
            else:
                try:
                    page = int(r)
                    if 1 <= page <= total_pages:
                        pages.add(page)
                except ValueError:
                    continue

        return pages
