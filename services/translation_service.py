import os
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import fitz  # PyMuPDF

from modules.pdf_extractor import PdfExtractor
from modules.aiping_translator import AipingTranslator
from modules.silicon_flow_translator import SiliconFlowTranslator
from modules.pdf_generator import PdfGenerator
from modules.docx_generator import DocxGenerator
from modules.markdown_generator import MarkdownGenerator, create_markdown_generator
from modules.semantic_analyzer_factory import SemanticAnalyzerFactory

from models.text_block import TextBlock
from models.extraction import PdfPage

from utils.text_processing import merge_semantic_blocks, split_translated_result, merge_semantic_blocks_with_llm, merge_semantic_blocks_with_llm_two_phase
from utils.file_utils import remove_file, create_zip
from utils.logging_config import get_logger

from config import config

logger = get_logger(__name__)

# 翻译业务服务
class TranslationService:
    """翻译业务服务类，负责处理PDF文档的翻译流程"""
    
    def __init__(self):
        """初始化TranslationService对象"""
        # 创建可复用的线程池实例
        self.executor = ThreadPoolExecutor(max_workers=config.MAX_WORKERS)
    
    def parse_page_range(self, page_range_str, total_pages):
        """解析页码范围字符串，返回页码集合
        
        Args:
            page_range_str (str): 页码范围字符串，格式如"1-5,7,9-10"
            total_pages (int): PDF总页数
            
        Returns:
            set: 包含所有指定页码的集合
        """
        if not page_range_str:
            return set(range(1, total_pages + 1))
        
        pages = set()
        ranges = page_range_str.split(',')
        
        for r in ranges:
            r = r.strip()
            if '-' in r:
                # 处理页码范围，如1-5
                try:
                    start, end = map(int, r.split('-'))
                    # 确保页码在有效范围内
                    start = max(1, start)
                    end = min(total_pages, end)
                    if start <= end:
                        pages.update(range(start, end + 1))
                except ValueError:
                    continue
            else:
                # 处理单个页码，如7
                try:
                    page = int(r)
                    if 1 <= page <= total_pages:
                        pages.add(page)
                except ValueError:
                    continue
        
        return pages
    
    def get_translator(self, translator_type):
        """根据翻译服务类型创建翻译器实例

        Args:
            translator_type (str): 翻译服务类型（aiping/silicon_flow）
            
        Returns:
            Translator: 翻译器实例
        """
        if translator_type == 'aiping':
            # 创建aiping翻译器实例
            if not config.AIPING_API_KEY:
                raise ValueError("aiping翻译API配置不完整")
            return AipingTranslator(config.AIPING_API_KEY, config.AIPING_API_URL, config.AIPING_MODEL)
        elif translator_type == 'silicon_flow':
            # 创建硅基流动翻译器实例
            if not config.SILICON_FLOW_API_KEY:
                raise ValueError("硅基流动翻译API配置不完整")
            return SiliconFlowTranslator(config.SILICON_FLOW_API_KEY, config.SILICON_FLOW_API_URL, config.SILICON_FLOW_MODEL)
        else:
            raise ValueError(f"不支持的翻译服务类型: {translator_type}")
    
    def get_semantic_analyzer(self, analyzer_type):
        """根据分析器类型创建语义分析器实例

        Args:
            analyzer_type (str): 分析器类型（aiping/default）
            
        Returns:
            SemanticAnalyzer: 语义分析器实例
        """
        if analyzer_type == 'aiping':
            # 创建aiping语义分析器实例
            if not config.AIPING_API_KEY:
                raise ValueError("aiping语义分析API配置不完整")
            return SemanticAnalyzerFactory.create_analyzer(
                "aiping", 
                config.AIPING_API_KEY, 
                config.AIPING_API_URL, 
                config.AIPING_MODEL
            )
        elif analyzer_type == 'silicon_flow':
            # 创建默认语义分析器实例（硅基流动使用标准OpenAI格式）
            if not config.SILICON_FLOW_API_KEY:
                raise ValueError("硅基流动语义分析API配置不完整")
            return SemanticAnalyzerFactory.create_analyzer(
                "silicon_flow", 
                config.SILICON_FLOW_API_KEY, 
                config.SILICON_FLOW_API_URL, 
                config.SILICON_FLOW_MODEL
            )
        else:
            raise ValueError("无效的语义分析器类型")

    def handle_same_language(self, task, input_filepath, unique_id, filename, page_range, output_path=None):
        """处理源语言和目标语言相同的情况，直接拷贝原始PDF页面

        Args:
            task: 任务对象
            input_filepath: 输入文件路径
            unique_id: 唯一ID
            filename: 原始文件名
            page_range: 页码范围，格式如"1-5,7,9-10"或空字符串表示所有页
            output_path: 自定义输出路径，默认使用配置的OUTPUT_FOLDER

        Returns:
            str: 输出文件名
        """
        logger.info(f"任务 {task.task_id} 源语言和目标语言相同，直接拷贝原始页")
        task.update_phase_progress('generation', 0, '正在准备输出文件...')
        
        # 生成输出文件路径
        output_filename = f"translated_{unique_id}_{filename}"
        output_filepath = os.path.join(output_path if output_path else config.OUTPUT_FOLDER, output_filename)
        
        # 使用 PdfExtractor 的 total_pages 属性获取总页数
        with fitz.open(input_filepath) as doc:
            total_pages = len(doc)
        
        # 解析页码范围，获取需要拷贝的页码集合
        target_pages = self.parse_page_range(page_range, total_pages)
        logger.info(f"任务 {task.task_id} 总页数: {total_pages}, 需要拷贝的页码: {sorted(target_pages)}")
        
        # 如果页码范围为空或包含所有页面，直接拷贝整个文件
        if len(target_pages) == 0 or len(target_pages) == total_pages:
            logger.info(f"任务 {task.task_id} 页码范围为空或包含所有页面，直接拷贝整个文件")
            shutil.copy(input_filepath, output_filepath)
        else:
            # 使用PyMuPDF库只拷贝指定的页面
            logger.info(f"任务 {task.task_id} 开始拷贝指定页码的页面")
            
            # 打开原始PDF
            with fitz.open(input_filepath) as original_doc:
                # 创建新的PDF文档
                new_doc = fitz.open()
                
                # 拷贝指定的页面
                page_list = sorted(target_pages)
                for idx, page_num in enumerate(page_list):
                    # 转换为原始文档的索引（从0开始）
                    original_page_idx = page_num - 1
                    # 跳过超出范围的页码
                    if original_page_idx < 0 or original_page_idx >= len(original_doc):
                        logger.warning(f"任务 {task.task_id} 页码 {page_num} 超出原始文档范围，跳过")
                        continue
                    # 克隆页面到新文档
                    new_doc.insert_pdf(original_doc, from_page=original_page_idx, to_page=original_page_idx)
                    
                    # 更新进度
                    phase_percent = int((idx + 1) / len(page_list) * 100)
                    task.update_phase_progress('generation', phase_percent, f'正在拷贝第 {page_num} 页...')
                # 保存新文档
                new_doc.save(output_filepath)
                new_doc.close()
            
            logger.info(f"任务 {task.task_id} 拷贝指定页码的页面完成，共拷贝 {len(target_pages)} 页")
        
        task.update_phase_progress('clean', 0, '正在清理临时文件...')
        # 清理临时文件
        remove_file(input_filepath)
        logger.info(f"任务 {task.task_id} 已清理临时文件")
        
        task.update_phase_progress('clean', 100, '翻译完成！')
        # 设置任务结果
        task.set_result(output_filename)
        logger.info(f"任务 {task.task_id} 完成，输出文件: {output_filename}")
        return output_filename

    def extract_pdf_content(self, task, input_filepath, page_range, extract_chapter=True, output_path=None, tmp_dir=None):
        """提取PDF内容
        
        Args:
            task: 任务对象
            input_filepath: 输入文件路径
            page_range: 页码范围，格式如"1-5,7,9-10"或空字符串表示所有页
            extract_chapter: 是否提取章节信息 (默认: True)
            output_path: 输出文件路径，用于确定临时图像目录位置
            tmp_dir: 临时文件目录，优先使用

        Returns:
            tuple: (text_blocks, tables, extracted_images, chapters)
        """
        logger.info(f"任务 {task.task_id} extract_pdf_content方法接收到的extract_chapter值: {extract_chapter}")
        task.update_phase_progress('extraction', 0, '正在提取PDF文本...')
        
        # 1.1 创建PdfExtractor实例
        logger.info(f"任务 {task.task_id} 开始创建PdfExtractor实例")
        pdf_extractor = PdfExtractor(input_filepath)
        total_pages = pdf_extractor.total_pages
        logger.info(f"任务 {task.task_id} 获取总页数完成: {total_pages}")
        
        if task.is_canceled():
            # 清理临时文件
            remove_file(input_filepath)
            logger.info(f"任务 {task.task_id} 被取消，已清理临时文件")
            return None
        
        # 1.2 解析页码范围
        target_pages = self.parse_page_range(page_range, total_pages)
        sorted_target_pages = sorted(target_pages)
        logger.info(f"任务 {task.task_id} 需要翻译的页码: {sorted_target_pages}")
        
        # 1.3 确定临时图像目录
        # 优先使用 tmp_dir，其次是 output_path 所在目录
        temp_images_dir = tmp_dir
        if not temp_images_dir and output_path:
            temp_images_dir = os.path.dirname(output_path)
            if not temp_images_dir:
                temp_images_dir = os.getcwd()
        if temp_images_dir:
            logger.info(f"使用临时图像目录: {temp_images_dir}")
        
        # 1.4 根据页码范围提取PDF文本
        logger.info(f"任务 {task.task_id} 开始提取PDF文本")
        extracted_content = pdf_extractor.extract(pages=list(target_pages), extract_chapter=extract_chapter, temp_images_dir=temp_images_dir)
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
        
        # 收集所有页面的所有块，方便上下文查找
        # 只收集正文块，简化后续流程
        text_blocks = []
        page_count = len(extracted_content.pages)
        for i, page in enumerate(extracted_content.pages):
            phase_percent = int((i + 1) / page_count * 100)
            task.update_phase_progress('extraction', phase_percent, f'正在提取第 {page.page_num} 页...')
            
            # 页面的text_blocks已经是按垂直位置排序的
            for text_block in page.text_blocks:
                # 只添加正文块
                if text_block.is_body_text:
                    text_blocks.append(text_block)
        
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
        
        return text_blocks, tables, extracted_images, chapters


    def translate_merged_block(self, task, merged_block, index, translator, source_lang, target_lang, doc_type, glossary, total_blocks):
        """翻译单个合并块

        Args:
            task: 任务对象
            merged_block: 合并块
            index: 合并块索引
            translator: 翻译器实例
            source_lang: 源语言
            target_lang: 目标语言
            doc_type: 文档类型
            glossary: 术语表
            total_blocks: 总块数

        Returns:
            tuple: (translated_merged_block, block_results, page_num)
        """
        logger.info(f"任务 {task.task_id} 处理合并块 {index+1}/{total_blocks}")
        logger.info(f"任务 {task.task_id} 合并块 {index+1} 原文: {merged_block.block_text}")
        
        translation_result = translator.translate(
            merged_block.block_text,
            source_lang,
            target_lang,
            doc_type=doc_type,
            glossary=glossary
        )
        merged_translation = translation_result.content
        logger.info(f"任务 {task.task_id} 合并块 {index+1} 翻译结果: {merged_translation}")
        
        # 检查是否被截断
        if translation_result.truncated:
            logger.warning(f"任务 {task.task_id} 合并块 {index+1} 翻译被截断: {translation_result.truncation_info}")
            # 添加警告到任务对象
            task.add_warning("翻译被截断", {
                "process": "translation",
                "block_index": index,
                "token_usage": translation_result.token_usage,
                "finish_reason": translation_result.finish_reason
            })
        
        # 保存合并后的翻译结果
        from models.merged_block import MergedBlock
        
        first_block = merged_block.original_blocks[0]
        first_text_block = first_block
        page_num = merged_block.page_num
        logger.info(f"合并块 {index+1} 第一个原始块字体大小: {first_text_block.font_size}, 文本: '{first_text_block.block_text[:50]}...'")
        
        # 创建新的 MergedBlock 对象，使用翻译后的文本作为 block_text
        translated_merged_block = MergedBlock(
            block_text=merged_translation,
            original_blocks=merged_block.original_blocks,
            max_width=merged_block.max_width,
            max_height=merged_block.max_height
        )
        
        # 记录合并块中所有原始块的字体大小
        for j, block_info in enumerate(merged_block.original_blocks):
            text_block = block_info
            logger.info(f"合并块 {index+1} 原始块 {j+1} 字体大小: {text_block.font_size}, 文本: '{text_block.block_text[:50]}...'")
        
        # 拆分翻译结果
        original_blocks = merged_block.original_blocks
        translated_block_texts = split_translated_result(merged_translation, original_blocks)
        logger.info(f"任务 {task.task_id} 合并块 {index+1} 拆分结果: {translated_block_texts}")
        
        # 获取合并块的最大宽度和高度
        max_width = merged_block.max_width
        max_height = merged_block.max_height
        
        # 准备拆分后的结果
        block_results = []
        for j, block_text in enumerate(translated_block_texts):
            original_block_info = original_blocks[j]
            text_block = original_block_info  # 获取TextBlock对象
            page_num = original_block_info.page_num
            
            # 更新原始文本框为合并时得到的最大文本框
            original_bbox = text_block.block_bbox
            if max_width > 0 and max_height > 0:
                # 计算新的边界框，保持左上角坐标不变，使用最大宽度和高度
                new_bbox = (original_bbox[0], original_bbox[1], 
                            original_bbox[0] + max_width, 
                            original_bbox[1] + max_height)
            else:
                new_bbox = original_bbox
            
            # 使用 copy() 方法创建翻译后的 TextBlock 对象
            translated_text_block = text_block.copy()
            translated_text_block.block_text = block_text
            translated_text_block.block_bbox = new_bbox
            translated_text_block.page_num = page_num
            
            # 更新样式信息 - 使用每个拆分块的原始样式
            translated_text_block.update_style(
                font=text_block.font,
                font_size=text_block.font_size,
                color=text_block.color,
                flags=text_block.flags
            )
            
            # 记录每个拆分块使用的原始样式
            logger.info(f"任务 {task.task_id} 拆分块 {j+1} 使用原始样式: 字体={text_block.font}, 字体大小={text_block.font_size}")
            
            block_results.append((page_num, translated_text_block))
        
        return translated_merged_block, block_results, page_num

    def process_merged_blocks(self, task, merged_blocks, translator, source_lang, target_lang, doc_type, glossary):
        """处理语义合并后的块

        Args:
            task: 任务对象
            merged_blocks: 合并后的块
            translator: 翻译器实例
            source_lang: 源语言
            target_lang: 目标语言
            doc_type: 文档类型
            glossary: 术语表

        Returns:
            tuple: (page_translated_blocks_dict, merged_translations, translated_blocks)
        """
        total_original_blocks = len([block for merged_block in merged_blocks for block in merged_block.original_blocks])
        translated_blocks = 0
        total_blocks = len(merged_blocks)
        
        # 动态构建页面级别的翻译结果字典
        page_translated_blocks_dict = {}
        # 线程安全的结果收集
        merged_translations = []
        results_lock = threading.Lock()
        
        # 获取所有唯一的页码
        unique_pages = set()
        for block in merged_blocks:
            unique_pages.add(block.page_num)
        total_pages = len(unique_pages)
        processed_pages = set()
        
        # 使用类的线程池实例并行翻译
        # 提交所有翻译任务
        future_to_block = {self.executor.submit(self.translate_merged_block, task, block, i, translator, source_lang, target_lang, doc_type, glossary, total_blocks): (block, i) 
                         for i, block in enumerate(merged_blocks)}
        
        # 收集所有结果，保存原始索引
        results = {}
        completed_blocks = 0
        
        for future in as_completed(future_to_block):
            try:
                block, index = future_to_block[future]
                translated_merged_block, block_results, page_num = future.result()
                
                with results_lock:
                    # 保存结果和原始索引
                    results[index] = (translated_merged_block, block_results)
                    
                    # 标记当前页面为已处理
                    if page_num not in processed_pages:
                        processed_pages.add(page_num)
                        processed_page_count = len(processed_pages)
                    
                    completed_blocks += 1
                    phase_percent = int((completed_blocks / total_blocks) * 100)
                    task.update_phase_progress('translation', phase_percent, f'正在翻译文本: {completed_blocks}/{total_blocks}')
                    
            except Exception as e:
                logger.error(f"任务 {task.task_id} 翻译合并块时出错: {str(e)}")
                # 继续处理其他块
                continue
        
        # 所有任务完成后，按原始顺序处理结果
        for index in sorted(results.keys()):
            translated_merged_block, block_results = results[index]
            
            # 添加到合并结果列表（按原始顺序）
            merged_translations.append(translated_merged_block)
            
            # 处理拆分后的结果
            for page_num, translated_text_block in block_results:
                # 动态创建页面对象（如果不存在）
                if page_num not in page_translated_blocks_dict:
                    page_translated_blocks_dict[page_num] = PdfPage(page_num, [])
                # 添加到对应页面的翻译结果中
                page_translated_blocks_dict[page_num].text_blocks.append(translated_text_block)
                translated_blocks += 1
        
        return page_translated_blocks_dict, merged_translations, translated_blocks

    def translate_original_block(self, task, block_info, index, translator, source_lang, target_lang, doc_type, glossary, total_blocks):
        """翻译单个原始块

        Args:
            task: 任务对象
            block_info: 原始块信息
            index: 块索引
            translator: 翻译器实例
            source_lang: 源语言
            target_lang: 目标语言
            doc_type: 文档类型
            glossary: 术语表
            total_blocks: 总块数

        Returns:
            tuple: (page_num, translated_text_block, translated_merged_block)
        """
        text_block = block_info
        page_num = block_info.page_num
        
        logger.info(f"任务 {task.task_id} 处理原始块 {index+1}/{total_blocks}")
        logger.info(f"任务 {task.task_id} 原始块 {index+1} 原文: {text_block.block_text}")
        
        logger.info(f"任务 {task.task_id} 原始块 {index+1} 是正文块，开始翻译")
        # 调用翻译API
        translation_result = translator.translate(
            text_block.block_text,
            source_lang,
            target_lang,
            doc_type=doc_type,
            glossary=glossary
        )
        translated_text = translation_result.content
        logger.info(f"任务 {task.task_id} 原始块 {index+1} 翻译结果: {translated_text}")
        
        # 检查是否被截断
        if translation_result.truncated:
            logger.warning(f"任务 {task.task_id} 原始块 {index+1} 翻译被截断: {translation_result.truncation_info}")
            # 添加警告到任务对象
            task.add_warning("翻译被截断", {
                "process": "translation",
                "block_index": index,
                "token_usage": translation_result.token_usage,
                "finish_reason": translation_result.finish_reason
            })
        
        # 保存翻译结果，用于Word生成
        from models.merged_block import MergedBlock
        
        # 计算块的宽度和高度
        bbox = text_block.block_bbox
        width = bbox[2] - bbox[0] if len(bbox) >= 4 else 0
        height = bbox[3] - bbox[1] if len(bbox) >= 4 else 0
        
        # 创建新的 MergedBlock 对象，使用翻译后的文本作为 block_text
        translated_merged_block = MergedBlock(
            block_text=translated_text,
            original_blocks=[block_info],
            max_width=width,
            max_height=height
        )
        
        # 使用 copy() 方法创建翻译后的 TextBlock 对象
        translated_text_block = text_block.copy()
        translated_text_block.block_text = translated_text
        
        # 更新样式信息
        translated_text_block.update_style(
            font=text_block.font,
            font_size=text_block.font_size,
            color=text_block.color,
            flags=text_block.flags
        )
        
        return page_num, translated_text_block, translated_merged_block

    def process_original_blocks(self, task, text_blocks, translator, source_lang, target_lang, doc_type, glossary):
        """直接处理原始块（不进行语义合并）

        Args:
            task: 任务对象
            text_blocks: 所有原始块
            translator: 翻译器实例
            source_lang: 源语言
            target_lang: 目标语言
            doc_type: 文档类型
            glossary: 术语表

        Returns:
            tuple: (page_translated_blocks_dict, merged_translations, translated_blocks)
        """
        total_original_blocks = len(text_blocks)
        translated_blocks = 0
        
        # 动态构建页面级别的翻译结果字典
        page_translated_blocks_dict = {}
        # 保存翻译结果，用于Word生成
        merged_translations = []
        # 线程安全的结果收集
        results_lock = threading.Lock()
        
        # 获取所有唯一的页码
        unique_pages = set()
        for block in text_blocks:
            unique_pages.add(block.page_num)
        total_pages = len(unique_pages)
        processed_pages = set()
        
        # 使用类的线程池实例并行翻译
        # 提交所有翻译任务
        future_to_block = {self.executor.submit(self.translate_original_block, task, block, i, translator, source_lang, target_lang, doc_type, glossary, total_original_blocks): (block, i) 
                         for i, block in enumerate(text_blocks)}
        
        # 收集所有结果，保存原始索引
        results = {}
        completed_blocks = 0
        
        for future in as_completed(future_to_block):
            try:
                block, index = future_to_block[future]
                page_num, translated_text_block, translated_merged_block = future.result()
                
                with results_lock:
                    # 保存结果和原始索引
                    results[index] = (page_num, translated_text_block, translated_merged_block)
                    
                    # 标记当前页面为已处理
                    if page_num not in processed_pages:
                        processed_pages.add(page_num)
                        processed_page_count = len(processed_pages)
                    
                    completed_blocks += 1
                    phase_percent = int((completed_blocks / total_original_blocks) * 100)
                    task.update_phase_progress('translation', phase_percent, f'正在翻译文本: {completed_blocks}/{total_original_blocks}')
                    
            except Exception as e:
                logger.error(f"任务 {task.task_id} 翻译原始块时出错: {str(e)}")
                # 继续处理其他块
                continue
        
        # 所有任务完成后，按原始顺序处理结果
        for index in sorted(results.keys()):
            page_num, translated_text_block, translated_merged_block = results[index]
            
            # 添加到合并结果列表（按原始顺序）
            merged_translations.append(translated_merged_block)
            
            # 动态创建页面对象（如果不存在）
            if page_num not in page_translated_blocks_dict:
                page_translated_blocks_dict[page_num] = PdfPage(page_num, [])
            
            # 添加到对应页面的翻译结果中
            page_translated_blocks_dict[page_num].text_blocks.append(translated_text_block)
            translated_blocks += 1
        
        return page_translated_blocks_dict, merged_translations, translated_blocks

    def translate_table_cell(self, task, table_idx, row_idx, col_idx, cell, translator, source_lang, target_lang, doc_type, glossary, table_pages):
        """翻译单个表格单元格

        Args:
            task: 任务对象
            table_idx: 表格索引
            row_idx: 行索引
            col_idx: 列索引
            cell: 单元格对象
            translator: 翻译器实例
            source_lang: 源语言
            target_lang: 目标语言
            doc_type: 文档类型
            glossary: 术语表
            table_pages: 表格页面信息字典

        Returns:
            tuple: (table_idx, row_idx, col_idx, translated_cell, page_num)
        """
        text_preview = cell.text[:50] + '...' if len(cell.text) > 50 else cell.text
        logger.info(f"任务 {task.task_id} 开始翻译单元格: 表格={table_idx}, 行={row_idx}, 列={col_idx}, 原文='{text_preview}'")
        
        # 调用翻译API
        translation_result = translator.translate(
            cell.text,
            source_lang,
            target_lang,
            doc_type=doc_type,
            glossary=glossary
        )
        translated_text = translation_result.content
        translated_preview = translated_text[:50] + '...' if len(translated_text) > 50 else translated_text
        
        logger.info(f"任务 {task.task_id} 单元格翻译完成: 表格={table_idx}, 行={row_idx}, 列={col_idx}, 译文='{translated_preview}'")
        
        # 检查是否被截断
        if translation_result.truncated:
            logger.warning(f"任务 {task.task_id} 表格单元格翻译被截断: {translation_result.truncation_info}")
            # 添加警告到任务对象
            task.add_warning("表格翻译被截断", {
                "process": "translation",
                "table_index": table_idx,
                "row_index": row_idx,
                "col_index": col_idx,
                "token_usage": translation_result.token_usage,
                "finish_reason": translation_result.finish_reason
            })
        # 创建翻译后的PdfCell对象
        from models.extraction import PdfCell
        translated_cell = PdfCell(
            text=translated_text,
            bbox=cell.bbox,
            row_idx=cell.row_idx,
            col_idx=cell.col_idx
        )
        return table_idx, row_idx, col_idx, translated_cell, table_pages.get(table_idx, 0)

    def build_translated_row(self, task, row_idx, row, table_idx, cell_results):
        """构建翻译后的表格行

        Args:
            task: 任务对象
            row_idx: 行索引
            row: 原始行
            table_idx: 表格索引
            cell_results: 翻译结果字典

        Returns:
            list: 翻译后的行
        """
        from models.extraction import PdfCell
        translated_row = []
        
        for col_idx, cell in enumerate(row):
            if cell and cell.text:
                # 查找翻译结果
                has_translation = (table_idx in cell_results and 
                                   row_idx in cell_results[table_idx] and 
                                   col_idx in cell_results[table_idx][row_idx])
                
                if has_translation:
                    translated_cell = cell_results[table_idx][row_idx][col_idx]
                    cell_preview = translated_cell.text[:50] + '...' if len(translated_cell.text) > 50 else translated_cell.text
                    logger.info(f"任务 {task.task_id} 使用翻译结果: 表格={table_idx}, 行={row_idx}, 列={col_idx}, 内容='{cell_preview}'")
                else:
                    # 如果没有翻译结果，使用原文
                    text_preview = cell.text[:50] + '...' if len(cell.text) > 50 else cell.text
                    logger.warning(f"任务 {task.task_id} 未找到翻译结果，使用原文: 表格={table_idx}, 行={row_idx}, 列={col_idx}, 原文='{text_preview}'")
                    translated_cell = PdfCell(
                        text=cell.text,
                        bbox=cell.bbox,
                        row_idx=cell.row_idx,
                        col_idx=cell.col_idx
                    )
                translated_row.append(translated_cell)
            else:
                # 空单元格
                translated_cell = PdfCell(
                    text='',
                    bbox=cell.bbox if cell else None,
                    row_idx=cell.row_idx if cell else 0,
                    col_idx=cell.col_idx if cell else 0
                )
                translated_row.append(translated_cell)
        
        return translated_row

    def translate_tables(self, task, tables, translator, source_lang, target_lang, doc_type, glossary):
        """翻译表格内容

        Args:
            task: 任务对象
            tables: 提取的表格列表
            translator: 翻译器实例
            source_lang: 源语言
            target_lang: 目标语言
            doc_type: 文档类型
            glossary: 术语表

        Returns:
            list: 翻译后的表格列表
        """
        
        translated_tables = []
        
        if tables:
            if not task.update_phase_progress('table_translation', 0, '正在翻译表格内容...'):
                # 任务被取消，直接返回
                logger.info(f"任务 {task.task_id} 被取消")
                return None
            
            logger.info(f"任务 {task.task_id} 开始翻译表格内容")
            
            # 提交翻译任务并处理结果
            cell_results, total_cells = self._process_table_translation(task, tables, translator, source_lang, target_lang, doc_type, glossary)
            
            # 构建翻译后的表格
            translated_tables = self._build_translated_tables(task, tables, cell_results)
            
            logger.info(f"任务 {task.task_id} 表格翻译完成，共 {len(translated_tables)} 个表格")
        
        return translated_tables
    
    def _process_table_translation(self, task, tables, translator, source_lang, target_lang, doc_type, glossary):
        """处理表格翻译任务
        
        Args:
            task: 任务对象
            tables: 提取的表格列表
            translator: 翻译器实例
            source_lang: 源语言
            target_lang: 目标语言
            doc_type: 文档类型
            glossary: 术语表
            
        Returns:
            tuple: (cell_results, total_cells)
        """
        # 获取所有唯一的页码
        unique_pages = set()
        # 线程安全的结果存储
        cell_results = {}
        results_lock = threading.Lock()
        translated_cells_count = 0
        total_cells = 0
        
        # 获取表格的页面信息
        table_pages = {table_idx: table.page_num for table_idx, table in enumerate(tables)}
        
        # 提交翻译任务
        future_to_cell = {}
        
        for table_idx, table in enumerate(tables):
            unique_pages.add(table.page_num)
            logger.info(f"任务 {task.task_id} 处理表格 {table_idx}: 页码={table.page_num}, 行数={len(table.cells)}")
            
            # 直接提交单元格翻译任务，避免创建中间列表
            for row_idx, row in enumerate(table.cells):
                for col_idx, cell in enumerate(row):
                    if cell and cell.text:
                        total_cells += 1
                        text_preview = cell.text[:50] + '...' if len(cell.text) > 50 else cell.text
                        logger.info(f"任务 {task.task_id} 提交单元格: 表格={table_idx}, 行={row_idx}, 列={col_idx}, 原文='{text_preview}'")
                        future_to_cell[self.executor.submit(self.translate_table_cell, task, table_idx, row_idx, col_idx, cell, translator, source_lang, target_lang, doc_type, glossary, table_pages)] = (table_idx, row_idx, col_idx, cell)
        
        logger.info(f"任务 {task.task_id} 共提交 {total_cells} 个需要翻译的单元格")
        
        # 处理翻译结果
        processed_pages = set()
        total_pages = len(unique_pages)
        
        for future in as_completed(future_to_cell):
            try:
                table_idx, row_idx, col_idx, translated_cell, page_num = future.result()
                translated_preview = translated_cell.text[:50] + '...' if len(translated_cell.text) > 50 else translated_cell.text
                logger.info(f"任务 {task.task_id} 存储翻译结果: 表格={table_idx}, 行={row_idx}, 列={col_idx}, 译文='{translated_preview}'")
                
                with results_lock:
                    # 存储翻译结果
                    if table_idx not in cell_results:
                        cell_results[table_idx] = {}
                    if row_idx not in cell_results[table_idx]:
                        cell_results[table_idx][row_idx] = {}
                    cell_results[table_idx][row_idx][col_idx] = translated_cell
                    
                    # 标记当前页面为已处理
                    if page_num not in processed_pages:
                        processed_pages.add(page_num)
                        processed_page_count = len(processed_pages)
                    
                    translated_cells_count += 1
                    if total_cells > 0:
                        phase_percent = int((translated_cells_count / total_cells) * 100)
                        task.update_phase_progress('table_translation', phase_percent, f'正在翻译表格: {translated_cells_count}/{total_cells}')
                        
            except Exception as e:
                logger.error(f"任务 {task.task_id} 翻译表格单元格时出错: {str(e)}")
                # 继续处理其他单元格
                continue
        
        return cell_results, total_cells
    
    def _build_translated_tables(self, task, tables, cell_results):
        """构建翻译后的表格
        
        Args:
            task: 任务对象
            tables: 提取的表格列表
            cell_results: 翻译结果
            
        Returns:
            list: 翻译后的表格列表
        """
        from models.extraction import PdfTable
        
        translated_tables = []
        
        logger.info(f"任务 {task.task_id} 开始构建翻译后的表格，cell_results 包含 {len(cell_results)} 个表格")
        
        for table_idx, table in enumerate(tables):
            # 创建翻译后的单元格列表
            translated_cells = []
            logger.info(f"任务 {task.task_id} 构建表格 {table_idx}: 行数={len(table.cells)}")
            
            # 构建每一行
            for row_idx, row in enumerate(table.cells):
                translated_row = self.build_translated_row(task, row_idx, row, table_idx, cell_results)
                translated_cells.append(translated_row)
            
            # 创建翻译后的PdfTable对象
            # 使用copy方法复制表格对象，排除cells属性
            translated_table = table.copy(exclude_attrs=['cells'])
            # 更新cells为翻译后的内容
            translated_table.cells = translated_cells
            
            translated_tables.append(translated_table)
            logger.info(f"任务 {task.task_id} 表格 {table_idx} 构建完成")
        
        return translated_tables

    def generate_pdf_output(self, task, input_filepath, unique_id, filename, translated_content, target_lang, output_path=None, output_filename=None):
        """生成PDF输出文件

        Args:
            task: 任务对象
            input_filepath: 输入文件路径
            unique_id: 唯一ID
            filename: 原始文件名
            translated_content: 翻译后的内容
            target_lang: 目标语言
            output_path: 自定义输出路径，默认使用配置的OUTPUT_FOLDER
            output_filename: 自定义输出文件名，默认使用自动生成的文件名

        Returns:
            str: 输出文件名
        """
        # 如果用户指定了输出文件名，则使用用户指定的文件名
        if output_filename:
            final_output_filename = output_filename
        else:
            final_output_filename = f"translated_{unique_id}_{filename}"
        output_filepath = os.path.join(output_path if output_path else config.OUTPUT_FOLDER, final_output_filename)
        
        # 创建PDF生成器实例
        pdf_generator = PdfGenerator()
        # 生成翻译后的PDF，传递目标语言参数
        pdf_generator.generate_pdf(input_filepath, translated_content, output_filepath, target_lang)
        logger.info(f"任务 {task.task_id} PDF生成完成，输出文件: {final_output_filename}")
        return final_output_filename
    
    def generate_docx_output(self, task, unique_id, filename, translated_content, extracted_images, target_lang, output_path=None, output_filename=None):
        """生成Word输出文件

        Args:
            task: 任务对象
            unique_id: 唯一ID
            filename: 原始文件名
            translated_content: 翻译后的内容
            extracted_images: 提取的图像
            target_lang: 目标语言
            output_path: 自定义输出路径，默认使用配置的OUTPUT_FOLDER
            output_filename: 自定义输出文件名，默认使用自动生成的文件名

        Returns:
            str: 输出文件名
        """
        # 如果用户指定了输出文件名，则使用用户指定的文件名
        if output_filename:
            final_output_filename = output_filename
        else:
            final_output_filename = f"translated_{unique_id}_{os.path.splitext(filename)[0]}.docx"
        docx_filepath = os.path.join(output_path if output_path else config.OUTPUT_FOLDER, final_output_filename)
        
        # 创建Word生成器实例
        docx_generator = DocxGenerator()
        
        # 记录传递给Word生成器的图像信息
        logger.info(f"任务 {task.task_id} 传递 {len(extracted_images)} 个图像到Word生成器")
        for i, image in enumerate(extracted_images):
            logger.info(f"任务 {task.task_id} 传递图像 {i+1}: 页码={image.page_num}, 路径={image.image_path}, 边界框={image.bbox}")
        
        # 生成翻译后的Word文档
        docx_generator.generate_docx(translated_content, extracted_images, docx_filepath, target_lang)
        logger.info(f"任务 {task.task_id} Word文档生成完成，输出文件: {final_output_filename}")
        return final_output_filename

    def generate_markdown_output(self, task, unique_id, filename, translated_content, extracted_images, target_lang, translator_type, chapters, chapter_split, output_path=None, output_filename=None, tmp_dir=None):
        """生成Markdown输出文件

        Args:
            task: 任务对象
            unique_id: 唯一ID
            filename: 原始文件名
            translated_content: 翻译后的内容
            extracted_images: 提取的图像
            target_lang: 目标语言
            translator_type: 翻译器类型
            chapters: 章节信息
            chapter_split: 是否按章节拆分
            output_path: 自定义输出路径，默认使用配置的OUTPUT_FOLDER
            output_filename: 自定义输出文件名，默认使用自动生成的文件名
            tmp_dir: 临时文件目录，用于存放中间文件

        Returns:
            str: 输出文件名
        """
        # 生成Markdown文件名
        md_filename = f"translated_{unique_id}_{os.path.splitext(filename)[0]}.md"
        # 使用tmp_dir存放Markdown文件
        md_filepath = os.path.join(tmp_dir if tmp_dir else (output_path if output_path else config.OUTPUT_FOLDER), md_filename)
        
        # 根据翻译器类型选择布局模型
        api_key, api_url, layout_model = self._get_markdown_generator_config(translator_type)
        
        # 创建Markdown生成器实例
        markdown_generator = create_markdown_generator(
            api_type=translator_type,
            api_key=api_key,
            api_url=api_url,
            model=layout_model
        )
        
        # 记录传递给Markdown生成器的图像信息
        logger.info(f"任务 {task.task_id} 传递 {len(extracted_images)} 个图像到Markdown生成器")
        for i, image in enumerate(extracted_images):
            logger.info(f"任务 {task.task_id} 传递图像 {i+1}: 页码={image.page_num}, 路径={image.image_path}, 边界框={image.bbox}")
        
        # 使用传入的章节信息
        logger.info(f"任务 {task.task_id} 接收到 {len(chapters) if chapters else 0} 个章节，章节拆分: {chapter_split}")
        
        # 生成翻译后的Markdown文档
        try:
            # 使用unique_id作为doc_id，确保每个文档有独立的图像目录
            # 根据chapter_split参数决定是否传递章节信息
            markdown_result = markdown_generator.generate_markdown(
                translated_content, extracted_images, md_filepath, target_lang, 
                doc_id=unique_id, 
                chapters=chapters if chapter_split and chapters and len(chapters) > 0 else None
            )
            
            # 处理返回的MarkdownGenerationResult
            # 检查是否有警告信息
            if hasattr(markdown_result, 'warnings') and markdown_result.warnings:
                for warning in markdown_result.warnings:
                    logger.warning(f"任务 {task.task_id} Markdown生成警告: {warning['message']}")
                    # 添加警告到任务对象
                    task.add_warning(warning['message'], warning['context'])
            
            # 构建输出文件列表
            if chapter_split and chapters and len(chapters) > 0:
                return self._generate_chapter_zip(task, unique_id, filename, md_filename, output_path, output_filename, tmp_dir)
            else:
                return self._generate_single_zip(task, unique_id, filename, md_filepath, output_path, output_filename, tmp_dir)
        finally:
            # 清理临时图像目录
            self._cleanup_temp_images(unique_id, output_path, tmp_dir)
    
    def _get_markdown_generator_config(self, translator_type):
        """获取Markdown生成器配置
        
        Args:
            translator_type: 翻译器类型
            
        Returns:
            tuple: (api_key, api_url, layout_model)
        """
        if translator_type == 'aiping':
            api_key = config.AIPING_API_KEY
            api_url = config.AIPING_API_URL
            layout_model = config.AIPING_MODEL_LAYOUT
        elif translator_type == 'silicon_flow':
            api_key = config.SILICON_FLOW_API_KEY
            api_url = config.SILICON_FLOW_API_URL
            layout_model = config.SILICON_FLOW_MODEL_LAYOUT
        else:
            # 默认使用aiping的布局模型
            api_key = config.AIPING_API_KEY
            api_url = config.AIPING_API_URL
            layout_model = config.AIPING_MODEL_LAYOUT
        return api_key, api_url, layout_model
    
    def _generate_chapter_zip(self, task, unique_id, filename, md_filename, output_path=None, output_filename=None, tmp_dir=None):
        """生成章节Markdown压缩文件
        
        Args:
            task: 任务对象
            unique_id: 唯一ID
            filename: 原始文件名
            md_filename: Markdown文件名
            output_path: 自定义输出路径，默认使用配置的OUTPUT_FOLDER
            output_filename: 自定义输出文件名，默认使用自动生成的文件名
            tmp_dir: 临时文件目录，用于存放中间文件
            
        Returns:
            str: 压缩文件名
        """
        import glob
        # 使用tmp_dir查找章节文件
        base_dir = tmp_dir if tmp_dir else (output_path if output_path else config.OUTPUT_FOLDER)
        chapter_files = glob.glob(os.path.join(base_dir, "*.md"))
        logger.info(f"找到的MD文件: {[os.path.basename(f) for f in chapter_files]}")
        # 过滤出章节文件
        chapter_files = [f for f in chapter_files if os.path.basename(f) != md_filename]
        logger.info(f"过滤后的章节文件: {[os.path.basename(f) for f in chapter_files]}")
        
        # 创建包含所有Markdown文件和图像目录的zip文件
        # 如果用户指定了输出文件名，则使用用户指定的文件名
        if output_filename:
            zip_filename = output_filename
        else:
            zip_filename = f"translated_{unique_id}_{os.path.splitext(filename)[0]}.zip"
        zip_filepath = os.path.join(output_path if output_path else config.OUTPUT_FOLDER, zip_filename)
        
        # 检查是否存在当前文档的图像目录
        images_dir = os.path.join(base_dir, f'images_{unique_id}')
        directories_to_include = []
        if os.path.exists(images_dir):
            directories_to_include.append(images_dir)
        
        # 创建zip文件
        create_zip(zip_filepath, chapter_files, directories_to_include)
        logger.info(f"任务 {task.task_id} 章节Markdown压缩文件生成完成，输出文件: {zip_filename}")
        return zip_filename
    
    def _generate_single_zip(self, task, unique_id, filename, md_filepath, output_path=None, output_filename=None, tmp_dir=None):
        """生成单个Markdown压缩文件
        
        Args:
            task: 任务对象
            unique_id: 唯一ID
            filename: 原始文件名
            md_filepath: Markdown文件路径
            output_path: 自定义输出路径，默认使用配置的OUTPUT_FOLDER
            output_filename: 自定义输出文件名，默认使用自动生成的文件名
            tmp_dir: 临时文件目录，用于存放中间文件
            
        Returns:
            str: 压缩文件名
        """
        logger.info(f"任务 {task.task_id} Markdown文档生成完成，输出文件: {os.path.basename(md_filepath)}")
        
        # 创建包含Markdown文件和当前文档图像目录的zip文件
        base_dir = output_path if output_path else config.OUTPUT_FOLDER
        # 如果用户指定了输出文件名，则使用用户指定的文件名
        if output_filename:
            zip_filename = output_filename
        else:
            zip_filename = f"translated_{unique_id}_{os.path.splitext(filename)[0]}.zip"
        zip_filepath = os.path.join(base_dir, zip_filename)
        
        # 检查是否存在当前文档的图像目录（优先使用tmp_dir）
        images_dir = os.path.join(tmp_dir if tmp_dir else base_dir, f'images_{unique_id}')
        directories_to_include = []
        if os.path.exists(images_dir):
            directories_to_include.append(images_dir)
        
        # 创建zip文件
        create_zip(zip_filepath, [md_filepath], directories_to_include)
        logger.info(f"任务 {task.task_id} Markdown压缩文件生成完成，输出文件: {zip_filename}")
        return zip_filename
    
    def _cleanup_temp_images(self, unique_id, output_path=None, tmp_dir=None):
        """清理临时图像目录
        
        Args:
            unique_id: 唯一ID
            output_path: 自定义输出路径，默认使用配置的OUTPUT_FOLDER
            tmp_dir: 临时文件目录，用于存放中间文件
        """
        base_dir = tmp_dir if tmp_dir else (output_path if output_path else config.OUTPUT_FOLDER)
        images_dir = os.path.join(base_dir, f'images_{unique_id}')
        if os.path.exists(images_dir):
            import shutil
            shutil.rmtree(images_dir)
            logger.info(f"已清理临时图像目录: {images_dir}")
    
    def generate_output_files(self, task, input_filepath, unique_id, filename, output_format, translated_content, extracted_images, target_lang, translator_type='aiping', chapters=None, chapter_split=True, output_path=None, output_filename=None, tmp_dir=None):
        """生成输出文件

        Args:
            task: 任务对象
            input_filepath: 输入文件路径
            unique_id: 唯一ID
            filename: 原始文件名
            output_format: 输出格式
            translated_content: 翻译后的内容
            extracted_images: 提取的图像
            target_lang: 目标语言
            translator_type: 翻译器类型（aiping/silicon_flow）
            chapter_split: 是否按章节翻译Markdown (默认: True)
            output_path: 自定义输出路径，默认使用配置的OUTPUT_FOLDER
            output_filename: 自定义输出文件名，默认使用自动生成的文件名
            tmp_dir: 临时文件目录，用于存放中间文件

        Returns:
            list: 输出文件名列表
        """
        logger.info(f"任务 {task.task_id} 开始生成输出文件")
        
        # 添加调用前的日志，记录translated_content中的blocks信息
        logger.info(f"任务 {task.task_id} translated_content包含blocks信息: {('blocks' in translated_content)}")
        if 'blocks' in translated_content:
            total_blocks = sum(len(page.text_blocks) for page in translated_content['blocks'])
            logger.info(f"任务 {task.task_id} 传递给生成器的blocks信息: 总页数={len(translated_content['blocks'])}, 总blocks数={total_blocks}")
        
        output_files = []
        
        # 处理PDF生成
        if output_format in ['pdf', 'pdf_docx', 'all']:
            pdf_filename = self.generate_pdf_output(task, input_filepath, unique_id, filename, translated_content, target_lang, output_path, output_filename)
            output_files.append(pdf_filename)
        
        # 处理Word生成
        if output_format in ['docx', 'pdf_docx', 'all']:
            docx_filename = self.generate_docx_output(task, unique_id, filename, translated_content, extracted_images, target_lang, output_path, output_filename)
            output_files.append(docx_filename)
        
        # 处理Markdown生成
        if output_format in ['md', 'markdown', 'all']:
            logger.info(f"任务 {task.task_id} 开始生成Markdown输出")
            try:
                md_filename = self.generate_markdown_output(task, unique_id, filename, translated_content, extracted_images, target_lang, translator_type, chapters, chapter_split, output_path, output_filename, tmp_dir)
                output_files.append(md_filename)
            except Exception as e:
                logger.error(f"任务 {task.task_id} Markdown文档生成失败: {str(e)}")
                # 抛出异常，让上层处理
                raise Exception(f"Markdown文档生成失败: {str(e)}")
        
        return output_files

    def cleanup_resources(self, task, input_filepath, output_filepath=None):
        """清理资源

        Args:
            task: 任务对象
            input_filepath: 输入文件路径
            output_filepath: 输出文件路径（可选）
        """
        try:
            # 清理临时文件
            if input_filepath and os.path.exists(input_filepath):
                remove_file(input_filepath)
                logger.info(f"任务 {task.task_id} 已清理临时文件: {input_filepath}")
            
            # 清理输出文件（如果任务被取消）
            if output_filepath and os.path.exists(output_filepath):
                remove_file(output_filepath)
                logger.info(f"任务 {task.task_id} 已清理输出文件: {output_filepath}")
        except Exception as e:
            logger.error(f"任务 {task.task_id} 清理资源时出错: {str(e)}")

    def cleanup_on_cancel(self, task, input_filepath):
        """任务取消时的资源清理

        Args:
            task: 任务对象
            input_filepath: 输入文件路径
        """
        try:
            # 清理临时文件
            if input_filepath and os.path.exists(input_filepath):
                remove_file(input_filepath)
                logger.info(f"任务 {task.task_id} 被取消，已清理临时文件: {input_filepath}")
        except Exception as e:
            logger.error(f"任务 {task.task_id} 取消时清理资源出错: {str(e)}")

    def cleanup_output_directory(self):
        """清理输出目录中的旧文件
        """
        if os.path.exists(config.OUTPUT_FOLDER):
            for file_name in os.listdir(config.OUTPUT_FOLDER):
                file_path = os.path.join(config.OUTPUT_FOLDER, file_name)
                if os.path.isfile(file_path):
                    # 清理所有类型的输出文件
                    if file_path.endswith(('.pdf', '.docx', '.md', '.zip')):
                        try:
                            if os.access(file_path, os.W_OK):
                                os.remove(file_path)
                                logger.info(f"清理旧输出文件: {file_path}")
                            else:
                                logger.warning(f"没有权限清理文件: {file_path}")
                        except Exception as e:
                            logger.warning(f"清理文件时出错: {file_path}, 错误: {str(e)}")
                elif os.path.isdir(file_path) and file_name.startswith('images_'):
                    # 清理图像目录
                    try:
                        if os.access(file_path, os.W_OK):
                            shutil.rmtree(file_path)
                            logger.info(f"清理旧图像目录: {file_path}")
                        else:
                            logger.warning(f"没有权限清理目录: {file_path}")
                    except Exception as e:
                        logger.warning(f"清理目录时出错: {file_path}, 错误: {str(e)}")
            logger.info("输出目录清理完成")
    
    def translate_content(self, task, text_blocks, semantic_merge, use_llm_merging, translator, semantic_analyzer, source_lang, target_lang, doc_type, glossary):
        """翻译文本内容

        Args:
            task: 任务对象
            text_blocks: 文本块列表
            semantic_merge: 是否启用语义块合并
            use_llm_merging: 是否使用大模型进行语义块合并
            translator: 翻译器实例
            semantic_analyzer: 语义分析器实例
            source_lang: 源语言
            target_lang: 目标语言
            doc_type: 文档类型
            glossary: 术语表

        Returns:
            tuple: (page_translated_blocks_dict, merged_translations, translated_blocks)
        """
        if semantic_merge:
            task.update_phase_progress('semantic_merge', 0, '正在进行语义合并...')
            logger.info(f"任务 {task.task_id} 开始语义块合并，原始块数量: {len(text_blocks)}")
            
            # 根据配置选择合并方法
            if use_llm_merging:
                logger.info(f"任务 {task.task_id} 使用大模型进行语义块合并")
                # 根据配置选择使用两阶段并行合并或原方法
                if config.USE_TWO_PHASE_MERGE:
                    logger.info(f"任务 {task.task_id} 使用两阶段并行合并方法")
                    merged_blocks, block_mapping = merge_semantic_blocks_with_llm_two_phase(
                        text_blocks, semantic_analyzer, source_lang,
                        max_workers=config.MERGE_MAX_WORKERS,
                        batch_size=config.MERGE_BATCH_SIZE
                    )
                else:
                    logger.info(f"任务 {task.task_id} 使用原始串行合并方法")
                    merged_blocks, block_mapping = merge_semantic_blocks_with_llm(text_blocks, semantic_analyzer, source_lang)
            else:
                logger.info(f"任务 {task.task_id} 使用规则-based方法进行语义块合并")
                # 使用规则-based方法进行语义块合并
                merged_blocks, block_mapping = merge_semantic_blocks(text_blocks)
            
            logger.info(f"任务 {task.task_id} 语义块合并完成，原始块数量: {len(text_blocks)}, 合并后块数量: {len(merged_blocks)}")
            
            task.update_phase_progress('semantic_merge', 100, '语义块合并完成，开始翻译...')
            
            # 记录合并块的具体内容
            for i, merged_block in enumerate(merged_blocks):
                logger.info(f"任务 {task.task_id} 合并块 {i+1} 内容: {merged_block.block_text}")
            
            # 处理合并后的块
            return self.process_merged_blocks(
                task, merged_blocks, translator, source_lang, target_lang, doc_type, glossary
            )
        else:
            logger.info(f"任务 {task.task_id} 跳过语义块合并，直接按原始块翻译")
            task.update_phase_progress('semantic_merge', 100, '跳过语义合并，开始翻译...')
            # 直接翻译原始块
            return self.process_original_blocks(
                task, text_blocks, translator, source_lang, target_lang, doc_type, glossary
            )
    
    def process_translation(self, task, input_filepath, source_lang, target_lang, translator_type, unique_id, filename, doc_type=config.DEFAULT_DOC_TYPE, glossary="", page_range="", output_format="pdf", semantic_merge=True, use_llm_merging=False, chapter_split=True):
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
        """
        try:
            logger.info(f"开始处理任务 {task.task_id}，文件: {filename}")
            logger.info(f"后端接收到的chapter_split值: {chapter_split}")
            # 更新任务状态为处理中
            task.set_status('processing')
            task.update_phase_progress('init', 0, '任务开始，正在初始化...')
            task.update_phase_progress('init', 50, '正在检查源文件...')
            task.update_phase_progress('init', 100, '源文件检查完成，准备提取内容')
            
            # 优化：如果目标语言和源语言相同，直接拷贝原始页
            if source_lang == target_lang:
                self.handle_same_language(task, input_filepath, unique_id, filename, page_range)
                return
            
            # 清理输出目录中的旧文件
            self.cleanup_output_directory()
            
            # 提取PDF内容
            extract_result = self.extract_pdf_content(task, input_filepath, page_range)
            if not extract_result:
                return
            
            text_blocks, tables, extracted_images, chapters = extract_result
            
            # 创建翻译器和语义分析器
            translator, semantic_analyzer = self._create_translators(task, translator_type)
            if task.is_canceled():
                self.cleanup_on_cancel(task, input_filepath)
                return
            
            # 翻译文本内容
            translated_content = self._translate_content(task, text_blocks, semantic_merge, use_llm_merging, translator, semantic_analyzer, source_lang, target_lang, doc_type, glossary)
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
            output_files = self._generate_outputs(task, input_filepath, unique_id, filename, output_format, translated_content, extracted_images, target_lang, translator_type, chapters, chapter_split)
            if task.is_canceled():
                self.cleanup_on_cancel(task, input_filepath)
                return
            
            # 完成任务
            self._complete_task(task, input_filepath, output_files, is_cli=False)
            
        except Exception as e:
            # 记录错误信息到日志
            logger.error(f"任务 {task.task_id} 处理失败: {str(e)}", exc_info=True)
            # 设置任务错误状态
            task.set_error(f"翻译失败: {str(e)}")
            # 清理临时文件
            if 'input_filepath' in locals():
                remove_file(input_filepath)
                logger.info(f"任务 {task.task_id} 失败，已清理临时文件")
    
    def _create_translators(self, task, translator_type):
        """创建翻译器和语义分析器实例
        
        Args:
            task: 任务对象
            translator_type: 翻译服务类型
            
        Returns:
            tuple: (translator, semantic_analyzer)
        """
        task.update_phase_progress('translation', 0, '正在创建翻译器...')
        
        # 创建翻译器实例
        logger.info(f"任务 {task.task_id} 开始创建翻译器")
        translator = self.get_translator(translator_type)
        logger.info(f"任务 {task.task_id} 翻译器创建完成")
        
        # 创建语义分析器实例
        logger.info(f"任务 {task.task_id} 开始创建语义分析器")
        # 根据翻译器类型选择对应的语义分析器类型
        semantic_analyzer = self.get_semantic_analyzer(translator_type)
        logger.info(f"任务 {task.task_id} 语义分析器创建完成，类型: {translator_type}")
        
        return translator, semantic_analyzer
    
    def _translate_content(self, task, text_blocks, semantic_merge, use_llm_merging, translator, semantic_analyzer, source_lang, target_lang, doc_type, glossary):
        """翻译文本内容
        
        Args:
            task: 任务对象
            text_blocks: 文本块列表
            semantic_merge: 是否启用语义块合并
            use_llm_merging: 是否使用大模型进行语义块合并
            translator: 翻译器实例
            semantic_analyzer: 语义分析器实例
            source_lang: 源语言
            target_lang: 目标语言
            doc_type: 文档类型
            glossary: 术语表
            
        Returns:
            dict: 翻译后的内容
        """
        task.update_phase_progress('translation', 5, '准备开始翻译文本内容...')
        
        logger.info(f"任务 {task.task_id} 开始翻译文本内容")
        # 准备翻译内容
        translated_content = {
            'tables': []
        }
        
        # 收集所有页面的所有块，方便上下文查找
        logger.info(f"任务 {task.task_id} 将blocks信息添加到translated_content中")
        translated_content['blocks'] = []
        
        # 翻译文本内容
        page_translated_blocks_dict, merged_translations, translated_blocks = self.translate_content(
            task, text_blocks, semantic_merge, use_llm_merging, translator, semantic_analyzer, source_lang, target_lang, doc_type, glossary
        )
        
        # 添加合并后的翻译结果到translated_content
        translated_content['merged_translations'] = merged_translations
        
        # 将翻译结果添加到translated_content中
        translated_content['blocks'] = [page_translated_blocks_dict[page_num] for page_num in sorted(page_translated_blocks_dict.keys())]
        
        logger.info(f"任务 {task.task_id} 翻译完成，总翻译块数量: {translated_blocks}")
        
        # 直接使用原始样式信息，不再需要text_content字段
        logger.info(f"任务 {task.task_id} 直接使用原始样式信息，不再需要text_content字段")
        
        logger.info(f"任务 {task.task_id} 文本翻译完成")
        
        if task.is_canceled():
            return None
        
        return translated_content
    
    def _generate_outputs(self, task, input_filepath, unique_id, filename, output_format, translated_content, extracted_images, target_lang, translator_type, chapters, chapter_split, output_path=None, output_filename=None, tmp_dir=None):
        """生成输出文件
        
        Args:
            task: 任务对象
            input_filepath: 输入文件路径
            unique_id: 唯一ID
            filename: 原始文件名
            output_format: 输出格式
            translated_content: 翻译后的内容
            extracted_images: 提取的图像
            target_lang: 目标语言
            translator_type: 翻译器类型
            chapters: 章节信息
            chapter_split: 是否按章节拆分
            output_path: 自定义输出路径，默认使用配置的OUTPUT_FOLDER
            output_filename: 自定义输出文件名，默认使用自动生成的文件名
            tmp_dir: 临时文件目录，用于存放中间文件
            
        Returns:
            list: 输出文件名列表
        """
        # 记录图像信息
        logger.info(f"任务 {task.task_id} 准备传递 {len(extracted_images)} 个图像到输出文件生成")
        for i, image in enumerate(extracted_images):
            logger.info(f"任务 {task.task_id} 图像 {i+1}: 页码={image.page_num}, 路径={image.image_path}, 边界框={image.bbox}")
        
        # 生成输出文件
        logger.info(f"任务 {task.task_id} 开始调用 generate_output_files 方法")
        output_files = self.generate_output_files(
            task, input_filepath, unique_id, filename, output_format, translated_content, extracted_images, target_lang, translator_type, chapters, chapter_split, output_path, output_filename, tmp_dir
        )
        logger.info(f"任务 {task.task_id} generate_output_files 方法执行完成，返回 {len(output_files)} 个输出文件")
        
        return output_files
    
    def _complete_task(self, task, input_filepath, output_files, is_cli=False):
        """完成任务，更新进度并设置结果
        
        Args:
            task: 任务对象
            input_filepath: 输入文件路径
            output_files: 输出文件名列表
            is_cli: 是否为CLI模式，CLI模式下不删除源文件
        """
        logger.info(f"任务 {task.task_id} 准备更新进度到 90%")
        if not task.update_phase_progress('generation', 50, '正在生成输出文件...'):
            self.cleanup_on_cancel(task, input_filepath)
            return
        
        if not task.update_phase_progress('clean', 0, '正在清理临时文件...'):
            self.cleanup_on_cancel(task, input_filepath)
            return
        
        # 清理临时文件（CLI模式下不删除源文件）
        if not is_cli:
            remove_file(input_filepath)
            logger.info(f"任务 {task.task_id} 已清理临时文件")
        else:
            logger.info(f"任务 {task.task_id} 为CLI模式，保留源文件")
        
        if not task.update_phase_progress('generation', 100, '翻译完成！'):
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

    def process_translation_sync(self, task, input_filepath, source_lang, target_lang, translator_type, unique_id, filename, doc_type=config.DEFAULT_DOC_TYPE, glossary="", page_range="", output_format="pdf", semantic_merge=True, use_llm_merging=False, chapter_split=True, progress_callback=None, is_cli=False, output_path=None, output_filename=None, tmp_dir=None):
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
            task.update_phase_progress('init', 0, '任务开始，正在初始化...')
            if progress_callback:
                progress_callback(0, '任务开始，正在初始化...')
            
            task.update_phase_progress('init', 50, '正在检查源文件...')
            task.update_phase_progress('init', 100, '源文件检查完成，准备提取内容')
            if progress_callback:
                progress_callback(5, '源文件检查完成')
            
            # 优化：如果目标语言和源语言相同，直接拷贝原始页
            if source_lang == target_lang:
                return self.handle_same_language(task, input_filepath, unique_id, filename, page_range, output_path)
            
            # 清理输出目录中的旧文件（仅当使用默认输出目录时）
            if not output_path:
                self.cleanup_output_directory()
            
            # 提取PDF内容
            extract_result = self.extract_pdf_content(task, input_filepath, page_range, output_path=output_path, tmp_dir=tmp_dir)
            if not extract_result:
                logger.error(f"任务 {task.task_id} PDF内容提取失败")
                return None
            
            text_blocks, tables, extracted_images, chapters = extract_result
            
            if progress_callback:
                progress_callback(10, 'PDF内容提取完成')
            
            # 创建翻译器和语义分析器
            translator, semantic_analyzer = self._create_translators(task, translator_type)
            if task.is_canceled():
                self.cleanup_on_cancel(task, input_filepath)
                return None
            
            if progress_callback:
                progress_callback(15, '翻译器创建完成')
            
            # 翻译文本内容
            translated_content = self._translate_content(task, text_blocks, semantic_merge, use_llm_merging, translator, semantic_analyzer, source_lang, target_lang, doc_type, glossary)
            if not translated_content:
                logger.error(f"任务 {task.task_id} 文本翻译失败")
                return None
            
            if progress_callback:
                progress_callback(60, '文本翻译完成')
            
            # 翻译表格内容
            translated_tables = self.translate_tables(
                task, tables, translator, source_lang, target_lang, doc_type, glossary
            )
            if translated_tables is None:
                logger.error(f"任务 {task.task_id} 表格翻译失败")
                return None
            translated_content['tables'] = translated_tables
            
            if progress_callback:
                progress_callback(70, '表格翻译完成')
            
            if task.is_canceled():
                self.cleanup_on_cancel(task, input_filepath)
                return None
            
            if not task.update_phase_progress('generation', 0, '正在生成输出文件...'):
                self.cleanup_on_cancel(task, input_filepath)
                return None
            
            if progress_callback:
                progress_callback(75, '正在生成输出文件...')
            
            # 生成输出文件
            output_files = self._generate_outputs(task, input_filepath, unique_id, filename, output_format, translated_content, extracted_images, target_lang, translator_type, chapters, chapter_split, output_path, output_filename, tmp_dir)
            
            if progress_callback:
                progress_callback(95, '输出文件生成完成')
            
            if task.is_canceled():
                self.cleanup_on_cancel(task, input_filepath)
                return None
            
            # 完成任务
            self._complete_task(task, input_filepath, output_files, is_cli=is_cli)
            
            if progress_callback:
                progress_callback(100, '翻译完成！')
            
            # 返回第一个输出文件
            return output_files[0] if output_files else None
            
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
            return None

# 创建翻译服务实例
translation_service = TranslationService()
