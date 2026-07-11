from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from typing import Set

from modules.aiping_translator import AipingTranslator
from modules.silicon_flow_translator import SiliconFlowTranslator
from modules.qianfan_translator import QianfanTranslator
from modules.semantic_analyzer_factory import SemanticAnalyzerFactory

from config import config
from utils.logging_config import get_logger
from utils.file_utils import remove_file

# ---------------------------------------------------------------------------
# Re-exports for test @patch backward compatibility
# Tests patch paths like 'services.translation_service.PdfGenerator'
# ---------------------------------------------------------------------------
import os as _os  # noqa: F811
from modules.pdf_generator import PdfGenerator  # noqa: F401
from modules.docx_generator import DocxGenerator  # noqa: F401
from modules.markdown_generator import create_markdown_generator  # noqa: F401
from modules.pdf_extractor import PdfExtractor  # noqa: F401
from utils.text_processing import (  # noqa: F401
    merge_semantic_blocks,
    split_translated_result,
    merge_semantic_blocks_with_llm,
    merge_semantic_blocks_with_llm_two_phase,
)
from utils.file_utils import create_zip, remove_file  # noqa: F401

# ---------------------------------------------------------------------------
# Sub-module classes
# ---------------------------------------------------------------------------
from services.translation_extractor import TranslationExtractor
from services.translation_content import TranslationContentTranslator
from services.translation_table import TranslationTableHandler, _get_cell_span  # noqa: F401
from services.translation_output import TranslationOutputGenerator

logger = get_logger(__name__)


class TranslationService:
    """翻译业务服务类，负责协调PDF文档的完整翻译流程"""

    def __init__(self):
        """初始化TranslationService对象"""
        # 创建可复用的线程池实例
        self.executor = ThreadPoolExecutor(max_workers=config.MAX_WORKERS)
        # 组合子模块
        self.extractor = TranslationExtractor(self.executor)
        self.content_translator = TranslationContentTranslator(self.executor)
        self.table_handler = TranslationTableHandler(self.executor)
        self.output_generator = TranslationOutputGenerator()

    # ======================================================================
    # 核心方法（保留在TranslationService中）
    # ======================================================================

    def parse_page_range(self, page_range_str: str | None, total_pages: int) -> Set[int]:
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

    def get_translator(self, translator_type, model=None):
        """根据翻译服务类型创建翻译器实例

        Args:
            translator_type (str): 翻译服务类型（aiping/silicon_flow/qianfan）
            model (str, optional): 翻译模型名称，None表示使用默认配置

        Returns:
            Translator: 翻译器实例
        """
        if translator_type == 'aiping':
            if not config.AIPING_API_KEY:
                raise ValueError("aiping翻译API配置不完整")
            return AipingTranslator(config.AIPING_API_KEY, config.AIPING_API_URL, model or config.AIPING_MODEL)
        elif translator_type == 'silicon_flow':
            if not config.SILICON_FLOW_API_KEY:
                raise ValueError("硅基流动翻译API配置不完整")
            return SiliconFlowTranslator(config.SILICON_FLOW_API_KEY, config.SILICON_FLOW_API_URL, model or config.SILICON_FLOW_MODEL)
        elif translator_type == 'qianfan':
            if not config.QIANFAN_API_KEY:
                raise ValueError("百度千帆翻译API配置不完整")
            return QianfanTranslator(config.QIANFAN_API_KEY, config.QIANFAN_API_URL, model or config.QIANFAN_MODEL)
        else:
            raise ValueError(f"不支持的翻译服务类型: {translator_type}")

    def get_semantic_analyzer(self, analyzer_type, model=None):
        """根据分析器类型创建语义分析器实例

        Args:
            analyzer_type (str): 分析器类型（aiping/silicon_flow/qianfan）
            model (str, optional): 模型名称，None表示使用默认配置

        Returns:
            SemanticAnalyzer: 语义分析器实例
        """
        if analyzer_type == 'aiping':
            if not config.AIPING_API_KEY:
                raise ValueError("aiping语义分析API配置不完整")
            return SemanticAnalyzerFactory.create_analyzer(
                "aiping",
                config.AIPING_API_KEY,
                config.AIPING_API_URL,
                model or config.AIPING_MODEL
            )
        elif analyzer_type == 'silicon_flow':
            if not config.SILICON_FLOW_API_KEY:
                raise ValueError("硅基流动语义分析API配置不完整")
            return SemanticAnalyzerFactory.create_analyzer(
                "silicon_flow",
                config.SILICON_FLOW_API_KEY,
                config.SILICON_FLOW_API_URL,
                model or config.SILICON_FLOW_MODEL
            )
        elif analyzer_type == 'qianfan':
            if not config.QIANFAN_API_KEY:
                raise ValueError("百度千帆语义分析API配置不完整")
            return SemanticAnalyzerFactory.create_analyzer(
                "qianfan",
                config.QIANFAN_API_KEY,
                config.QIANFAN_API_URL,
                model or config.QIANFAN_MODEL
            )
        else:
            raise ValueError("无效的语义分析器类型")

    def _create_translators(self, task, translator_type, translation_model=None):
        """创建翻译器和语义分析器实例

        Args:
            task: 任务对象
            translator_type: 翻译服务类型
            translation_model: 翻译模型名称 (默认: None, 使用配置)

        Returns:
            tuple: (translator, semantic_analyzer)
        """
        logger.info(f"任务 {task.task_id} 开始创建翻译器")
        translator = self.get_translator(translator_type, model=translation_model)
        logger.info(f"任务 {task.task_id} 翻译器创建完成")

        logger.info(f"任务 {task.task_id} 开始创建语义分析器")
        semantic_analyzer = self.get_semantic_analyzer(translator_type, model=translation_model)
        logger.info(f"任务 {task.task_id} 语义分析器创建完成，类型: {translator_type}")

        return translator, semantic_analyzer

    def process_translation(self, task, input_filepath, source_lang, target_lang, translator_type, unique_id, filename, doc_type=config.DEFAULT_DOC_TYPE, glossary="", page_range="", output_format="pdf", semantic_merge=True, use_llm_merging=False, chapter_split=True, ocr_mode=False, ocr_engine='paddleocr', ocr_lang='ch', ocr_llm_model=None, translation_model=None):
        """异步翻译任务处理函数

        Args:
            task: 任务对象
            input_filepath: 输入文件路径
            source_lang: 源语言
            target_lang: 目标语言
            translator_type: 翻译服务类型
            unique_id: 唯一ID
            filename: 原始文件名
            doc_type: 文档类型 (默认: 配置的DEFAULT_DOC_TYPE)
            glossary: 术语表
            page_range: 页码范围，格式如"1-5,7,9-10"或空字符串表示所有页
            output_format: 输出格式，可选值: "pdf", "docx", "both"
            semantic_merge: 是否启用语义块合并 (默认: True)
            use_llm_merging: 是否使用大模型进行语义块合并 (默认: True)
            chapter_split: 是否按章节翻译Markdown (默认: True)
            ocr_llm_model: LLM OCR模型名称 (默认: None, 使用配置)
        """
        try:
            logger.info(f"开始处理任务 {task.task_id}，文件: {filename}")
            logger.info(f"后端接收到的chapter_split值: {chapter_split}")
            # 更新任务状态为处理中
            task.set_status('processing')

            # 清理输出目录中的旧文件
            self.cleanup_output_directory()

            # 提取PDF内容
            extract_result = self.extract_pdf_content(
                task, input_filepath, page_range,
                ocr_mode=ocr_mode, ocr_engine=ocr_engine, ocr_lang=ocr_lang,
                translator_type=translator_type,
                extract_chapter=chapter_split,
                source_lang=source_lang,
                ocr_llm_model=ocr_llm_model
            )
            if not extract_result:
                return

            text_blocks, tables, extracted_images, chapters, all_page_nums = extract_result

            # 创建翻译器和语义分析器
            translator, semantic_analyzer = self._create_translators(task, translator_type, translation_model=translation_model)
            if task.is_canceled():
                self.cleanup_on_cancel(task, input_filepath)
                return

            # 翻译文本内容
            translated_content = self._translate_content(task, text_blocks, semantic_merge, use_llm_merging, translator, semantic_analyzer, source_lang, target_lang, doc_type, glossary, all_page_nums, output_format)
            if not translated_content:
                return

            # 翻译表格内容
            translated_tables = self.translate_tables(
                task, tables, translator, source_lang, target_lang, doc_type, glossary
            )
            if translated_tables is None:
                return
            translated_content['tables'] = translated_tables

            if task.is_canceled():
                self.cleanup_on_cancel(task, input_filepath)
                return

            if not task.update_phase_progress('generation', 0, '正在生成输出文件...'):
                self.cleanup_on_cancel(task, input_filepath)
                return

            # 生成输出文件
            output_files = self._generate_outputs(task, input_filepath, unique_id, filename, output_format, translated_content, extracted_images, target_lang, translator_type, chapters, chapter_split, target_pages=all_page_nums)
            if task.is_canceled():
                self.cleanup_on_cancel(task, input_filepath)
                return

            task.update_phase_progress('generation', 100, '输出文件生成完成')

            # 完成任务
            self._complete_task(task, input_filepath, output_files, is_cli=False)

            # 清理OCR临时图片目录（所有输出文件生成完成后）
            self._cleanup_ocr_temp_images(extracted_images)

        except Exception as e:
            # 记录错误信息到日志
            logger.error(f"任务 {task.task_id} 处理失败: {str(e)}", exc_info=True)
            # 设置任务错误状态
            task.set_error(f"翻译失败: {str(e)}")
            # 清理临时文件
            if 'input_filepath' in locals():
                remove_file(input_filepath)
                logger.info(f"任务 {task.task_id} 失败，已清理临时文件")
            # 清理OCR临时图片目录
            if 'extracted_images' in locals():
                self._cleanup_ocr_temp_images(extracted_images)

    def process_translation_sync(self, task, input_filepath, source_lang, target_lang, translator_type, unique_id, filename, doc_type=config.DEFAULT_DOC_TYPE, glossary="", page_range="", output_format="pdf", semantic_merge=True, use_llm_merging=False, chapter_split=True, ocr_mode=False, ocr_engine='paddleocr', ocr_lang='ch', translation_model=None, layout_model=None, glossary_model=None, ocr_llm_model=None, progress_callback=None, is_cli=False, output_path=None, output_filename=None, tmp_dir=None):
        """同步翻译任务处理函数

        Args:
            task: 任务对象
            input_filepath: 输入文件路径
            source_lang: 源语言
            target_lang: 目标语言
            translator_type: 翻译服务类型
            unique_id: 唯一ID
            filename: 原始文件名
            doc_type: 文档类型 (默认: 配置的DEFAULT_DOC_TYPE)
            glossary: 术语表
            page_range: 页码范围，格式如"1-5,7,9-10"或空字符串表示所有页
            output_format: 输出格式，可选值: "pdf", "docx", "markdown"
            semantic_merge: 是否启用语义块合并 (默认: True)
            use_llm_merging: 是否使用大模型进行语义块合并 (默认: False)
            chapter_split: 是否按章节翻译Markdown (默认: True)
            progress_callback: 进度回调函数，接收(progress, message)参数
            is_cli: 是否为CLI模式，CLI模式下不删除源文件
            output_path: 自定义输出路径，默认使用配置的OUTPUT_FOLDER
            output_filename: 自定义输出文件名，默认使用自动生成的文件名
            tmp_dir: 临时文件目录，用于存放中间文件

        Returns:
            str: 输出文件名，失败返回None
        """
        try:
            logger.info(f"开始同步处理任务 {task.task_id}，文件: {filename}")

            # 更新任务状态为处理中
            task.set_status('processing')

            # 清理输出目录中的旧文件（仅当使用默认输出目录时）
            if not output_path:
                self.cleanup_output_directory()

            # 提取PDF内容
            extract_result = self.extract_pdf_content(
                task, input_filepath, page_range,
                ocr_mode=ocr_mode, ocr_engine=ocr_engine, ocr_lang=ocr_lang,
                translator_type=translator_type,
                extract_chapter=chapter_split,
                source_lang=source_lang,
                ocr_llm_model=ocr_llm_model
            )
            if not extract_result:
                logger.error(f"任务 {task.task_id} PDF内容提取失败")
                return None

            text_blocks, tables, extracted_images, chapters, all_page_nums = extract_result

            if progress_callback:
                progress_callback(task.progress, task.message)

            # 创建翻译器和语义分析器
            translator, semantic_analyzer = self._create_translators(task, translator_type, translation_model=translation_model)
            if task.is_canceled():
                self.cleanup_on_cancel(task, input_filepath)
                return None

            if progress_callback:
                progress_callback(task.progress, task.message)

            # 翻译文本内容
            translated_content = self._translate_content(task, text_blocks, semantic_merge, use_llm_merging, translator, semantic_analyzer, source_lang, target_lang, doc_type, glossary, all_page_nums, output_format)
            if not translated_content:
                logger.error(f"任务 {task.task_id} 文本翻译失败")
                return None

            if progress_callback:
                progress_callback(task.progress, task.message)

            # 翻译表格内容
            translated_tables = self.translate_tables(
                task, tables, translator, source_lang, target_lang, doc_type, glossary
            )
            if translated_tables is None:
                logger.error(f"任务 {task.task_id} 表格翻译失败")
                return None
            translated_content['tables'] = translated_tables

            if progress_callback:
                progress_callback(task.progress, task.message)

            if task.is_canceled():
                self.cleanup_on_cancel(task, input_filepath)
                return None

            if not task.update_phase_progress('generation', 0, '正在生成输出文件...'):
                self.cleanup_on_cancel(task, input_filepath)
                return None

            if progress_callback:
                progress_callback(task.progress, task.message)

            # 生成输出文件
            output_files = self._generate_outputs(task, input_filepath, unique_id, filename, output_format, translated_content, extracted_images, target_lang, translator_type, chapters, chapter_split, output_path, output_filename, tmp_dir, target_pages=all_page_nums, layout_model=layout_model)

            if task.is_canceled():
                self.cleanup_on_cancel(task, input_filepath)
                return None

            task.update_phase_progress('generation', 100, '输出文件生成完成')

            if progress_callback:
                progress_callback(task.progress, task.message)

            # 完成任务
            self._complete_task(task, input_filepath, output_files, is_cli=is_cli)

            if progress_callback:
                progress_callback(task.progress, task.message)

            # 清理OCR临时图片目录（所有输出文件生成完成后）
            self._cleanup_ocr_temp_images(extracted_images)

            # 返回所有输出文件
            return output_files if output_files else None

        except Exception as e:
            # 记录错误信息到日志
            logger.error(f"任务 {task.task_id} 处理失败: {str(e)}", exc_info=True)
            # 设置任务错误状态
            task.set_error(f"翻译失败: {str(e)}")
            # 清理临时文件（CLI模式下不删除源文件）
            if 'input_filepath' in locals() and not is_cli:
                remove_file(input_filepath)
                logger.info(f"任务 {task.task_id} 失败，已清理临时文件")
            elif 'input_filepath' in locals() and is_cli:
                logger.info(f"任务 {task.task_id} 失败，CLI模式下保留源文件")
            # 清理OCR临时图片目录
            if 'extracted_images' in locals():
                self._cleanup_ocr_temp_images(extracted_images)
            return None

    def _complete_task(self, task, input_filepath, output_files, is_cli=False):
        """完成任务，更新进度并设置结果

        Args:
            task: 任务对象
            input_filepath: 输入文件路径
            output_files: 输出文件名列表
            is_cli: 是否为CLI模式，CLI模式下不删除源文件
        """
        logger.info(f"任务 {task.task_id} 准备清理临时文件")
        if not task.update_phase_progress('clean', 0, '正在清理临时文件...'):
            self.cleanup_on_cancel(task, input_filepath)
            return

        # 清理临时文件（CLI模式下不删除源文件）
        if not is_cli:
            remove_file(input_filepath)
            logger.info(f"任务 {task.task_id} 已清理临时文件")
        else:
            logger.info(f"任务 {task.task_id} 为CLI模式，保留源文件")

        if not task.update_phase_progress('clean', 100, '临时文件清理完成'):
            self.cleanup_on_cancel(task, input_filepath)
            return

        # 设置任务结果
        if output_files:
            # 如果有多个输出文件，返回第一个作为主要结果，其他作为附加结果
            task.set_result(output_files[0])
            if len(output_files) > 1:
                # 添加所有剩余文件作为附件
                for attachment in output_files[1:]:
                    task.add_attachment(attachment)
            logger.info(f"任务 {task.task_id} 完成，输出文件: {', '.join(output_files)}")
        else:
            logger.warning(f"任务 {task.task_id} 未生成任何输出文件")

    # ======================================================================
    # 委派方法 - 提取
    # ======================================================================

    def extract_pdf_content(self, task, input_filepath, page_range, extract_chapter=True, output_path=None, tmp_dir=None, ocr_mode=False, ocr_engine='paddleocr', ocr_lang='ch', translator_type='aiping', source_lang=None, ocr_llm_model=None):
        return self.extractor.extract_pdf_content(
            task, input_filepath, page_range,
            extract_chapter=extract_chapter,
            output_path=output_path,
            tmp_dir=tmp_dir,
            ocr_mode=ocr_mode,
            ocr_engine=ocr_engine,
            ocr_lang=ocr_lang,
            translator_type=translator_type,
            source_lang=source_lang,
            ocr_llm_model=ocr_llm_model,
        )

    # ======================================================================
    # 委派方法 - 内容翻译
    # ======================================================================

    def translate_content(self, task, text_blocks, semantic_merge, use_llm_merging, translator, semantic_analyzer, source_lang, target_lang, doc_type, glossary):
        return self.content_translator.translate_content(
            task, text_blocks, semantic_merge, use_llm_merging, translator, semantic_analyzer, source_lang, target_lang, doc_type, glossary
        )

    def _translate_content(self, task, text_blocks, semantic_merge, use_llm_merging, translator, semantic_analyzer, source_lang, target_lang, doc_type, glossary, all_page_nums, output_format='pdf'):
        return self.content_translator._translate_content(
            task, text_blocks, semantic_merge, use_llm_merging, translator, semantic_analyzer, source_lang, target_lang, doc_type, glossary, all_page_nums, output_format
        )

    def translate_merged_block(self, task, merged_block, index, translator, source_lang, target_lang, doc_type, glossary, total_blocks):
        return self.content_translator.translate_merged_block(
            task, merged_block, index, translator, source_lang, target_lang, doc_type, glossary, total_blocks
        )

    def process_merged_blocks(self, task, merged_blocks, translator, source_lang, target_lang, doc_type, glossary):
        return self.content_translator.process_merged_blocks(
            task, merged_blocks, translator, source_lang, target_lang, doc_type, glossary
        )

    def _is_translation_unchanged(self, translated_text: str, original_text: str) -> bool:
        return self.content_translator._is_translation_unchanged(translated_text, original_text)

    def translate_original_block(self, task, block_info, index, translator, source_lang, target_lang, doc_type, glossary, total_blocks):
        return self.content_translator.translate_original_block(
            task, block_info, index, translator, source_lang, target_lang, doc_type, glossary, total_blocks
        )

    def process_original_blocks(self, task, text_blocks, translator, source_lang, target_lang, doc_type, glossary):
        return self.content_translator.process_original_blocks(
            task, text_blocks, translator, source_lang, target_lang, doc_type, glossary
        )

    # ======================================================================
    # 委派方法 - 表格翻译
    # ======================================================================

    def translate_tables(self, task, tables, translator, source_lang, target_lang, doc_type, glossary):
        return self.table_handler.translate_tables(
            task, tables, translator, source_lang, target_lang, doc_type, glossary
        )

    def _process_table_translation(self, task, tables, translator, source_lang, target_lang, doc_type, glossary):
        return self.table_handler._process_table_translation(
            task, tables, translator, source_lang, target_lang, doc_type, glossary
        )

    def _build_translated_tables(self, task, tables, cell_results):
        return self.table_handler._build_translated_tables(task, tables, cell_results)

    def translate_table_cell(self, task, table_idx, row_idx, col_idx, cell, translator, source_lang, target_lang, doc_type, glossary, table_pages):
        return self.table_handler.translate_table_cell(
            task, table_idx, row_idx, col_idx, cell, translator, source_lang, target_lang, doc_type, glossary, table_pages
        )

    def translate_table_row(self, task, table_idx, row_idx, row_cells, translator, source_lang, target_lang, doc_type, glossary, table_pages):
        return self.table_handler.translate_table_row(
            task, table_idx, row_idx, row_cells, translator, source_lang, target_lang, doc_type, glossary, table_pages
        )

    def build_translated_row(self, task, row_idx, row, table_idx, cell_results):
        return self.table_handler.build_translated_row(task, row_idx, row, table_idx, cell_results)

    # ======================================================================
    # 委派方法 - 输出生成
    # ======================================================================

    def generate_output_files(self, task, input_filepath, unique_id, filename, output_format, translated_content, extracted_images, target_lang, translator_type='aiping', chapters=None, chapter_split=True, output_path=None, output_filename=None, tmp_dir=None, target_pages=None, layout_model=None):
        """生成输出文件（重写为调用委派方法以确保测试@patch生效）

        NOTE: 此方法保持于TranslationService中以维护测试backward compatibility。
        TranslationOutputGenerator中保留了独立版本供直接调用。
        """
        logger.info(f"任务 {task.task_id} 开始生成输出文件")
        logger.info(f"任务 {task.task_id} translated_content包含blocks信息: {('blocks' in translated_content)}")
        if 'blocks' in translated_content:
            total_blocks = sum(len(page.text_blocks) for page in translated_content['blocks'])
            logger.info(f"任务 {task.task_id} 传递给生成器的blocks信息: 总页数={len(translated_content['blocks'])}, 总blocks数={total_blocks}")

        output_files = []

        total_steps = 0
        if output_format in ['pdf', 'pdf_docx', 'all']:
            total_steps += 1
        if output_format in ['docx', 'pdf_docx', 'all']:
            total_steps += 1
        if output_format in ['md', 'markdown', 'all']:
            total_steps += 1
        completed_steps = 0

        # 使用self.xxx_output()委派方法，确保测试@patch('services.translation_service.TranslationService.generate_xxx')能生效
        if output_format in ['pdf', 'pdf_docx', 'all']:
            task.update_phase_progress('generation', int(completed_steps / total_steps * 100), '正在生成输出文件: PDF...')
            pdf_filename = self.generate_pdf_output(task, input_filepath, unique_id, filename, translated_content, target_lang, output_path, output_filename, target_pages=target_pages)
            output_files.append(pdf_filename)
            completed_steps += 1

        if output_format in ['docx', 'pdf_docx', 'all']:
            task.update_phase_progress('generation', int(completed_steps / total_steps * 100), '正在生成输出文件: DOCX...')
            docx_filename = self.generate_docx_output(task, unique_id, filename, translated_content, extracted_images, target_lang, output_path, output_filename)
            output_files.append(docx_filename)
            completed_steps += 1

        if output_format in ['md', 'markdown', 'all']:
            task.update_phase_progress('generation', int(completed_steps / total_steps * 100), '正在生成输出文件: Markdown...')
            logger.info(f"任务 {task.task_id} 开始生成Markdown输出")
            try:
                md_filename = self.generate_markdown_output(task, unique_id, filename, translated_content, extracted_images, target_lang, translator_type, chapters, chapter_split, output_path, output_filename, tmp_dir)
                output_files.append(md_filename)
                completed_steps += 1
            except Exception as e:
                logger.error(f"任务 {task.task_id} Markdown文档生成失败: {str(e)}")
                raise Exception(f"Markdown文档生成失败: {str(e)}")

        return output_files

    def _generate_outputs(self, task, input_filepath, unique_id, filename, output_format, translated_content, extracted_images, target_lang, translator_type, chapters, chapter_split, output_path=None, output_filename=None, tmp_dir=None, target_pages=None, layout_model=None):
        """生成输出文件（调用委派方法以确保测试@patch生效）

        NOTE: 此方法保持于TranslationService中以维护测试backward compatibility。
        """
        logger.info(f"任务 {task.task_id} 准备传递 {len(extracted_images)} 个图像到输出文件生成")
        for i, image in enumerate(extracted_images):
            logger.info(f"任务 {task.task_id} 图像 {i+1}: 页码={image.page_num}, 路径={image.image_path}, 边界框={image.bbox}")

        logger.info(f"任务 {task.task_id} 开始调用 generate_output_files 方法")
        output_files = self.generate_output_files(
            task, input_filepath, unique_id, filename, output_format, translated_content, extracted_images, target_lang, translator_type, chapters, chapter_split, output_path, output_filename, tmp_dir, target_pages, layout_model
        )
        logger.info(f"任务 {task.task_id} generate_output_files 方法执行完成，返回 {len(output_files)} 个输出文件")

        return output_files

    def generate_pdf_output(self, task, input_filepath, unique_id, filename, translated_content, target_lang, output_path=None, output_filename=None, target_pages=None):
        return self.output_generator.generate_pdf_output(
            task, input_filepath, unique_id, filename, translated_content, target_lang, output_path, output_filename, target_pages=target_pages
        )

    def generate_docx_output(self, task, unique_id, filename, translated_content, extracted_images, target_lang, output_path=None, output_filename=None):
        return self.output_generator.generate_docx_output(
            task, unique_id, filename, translated_content, extracted_images, target_lang, output_path, output_filename
        )

    def generate_markdown_output(self, task, unique_id, filename, translated_content, extracted_images, target_lang, translator_type, chapters, chapter_split, output_path=None, output_filename=None, tmp_dir=None):
        return self.output_generator.generate_markdown_output(
            task, unique_id, filename, translated_content, extracted_images, target_lang, translator_type, chapters, chapter_split, output_path, output_filename, tmp_dir
        )

    def _get_markdown_generator_config(self, translator_type):
        return self.output_generator._get_markdown_generator_config(translator_type)

    def _generate_chapter_zip(self, task, unique_id, filename, md_filename, output_path=None, output_filename=None, tmp_dir=None):
        return self.output_generator._generate_chapter_zip(
            task, unique_id, filename, md_filename, output_path, output_filename, tmp_dir
        )

    def _generate_single_zip(self, task, unique_id, filename, md_filepath, output_path=None, output_filename=None, tmp_dir=None):
        return self.output_generator._generate_single_zip(
            task, unique_id, filename, md_filepath, output_path, output_filename, tmp_dir
        )

    def _cleanup_temp_images(self, unique_id, output_path=None, tmp_dir=None):
        return self.output_generator._cleanup_temp_images(unique_id, output_path, tmp_dir)

    def _cleanup_ocr_temp_images(self, extracted_images):
        return self.output_generator._cleanup_ocr_temp_images(extracted_images)

    def cleanup_resources(self, task, input_filepath, output_filepath=None):
        return self.output_generator.cleanup_resources(task, input_filepath, output_filepath)

    def cleanup_on_cancel(self, task, input_filepath):
        return self.output_generator.cleanup_on_cancel(task, input_filepath)

    def cleanup_output_directory(self):
        return self.output_generator.cleanup_output_directory()


# 创建翻译服务实例
translation_service = TranslationService()
