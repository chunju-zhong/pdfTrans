import threading
import os
import shutil
import fitz  # PyMuPDF

from modules.pdf_extractor import pdf_extractor
from modules.aiping_translator import AipingTranslator
from modules.silicon_flow_translator import SiliconFlowTranslator
from modules.pdf_generator import PdfGenerator
from modules.docx_generator import DocxGenerator
from models.text_block import TextBlock
from models.extraction import PdfPage
from utils.text_processing import merge_semantic_blocks, split_translated_result
from utils.file_utils import remove_file
from utils.logging_config import get_logger
from config import config

logger = get_logger(__name__)

# 翻译业务服务
class TranslationService:
    """翻译业务服务类，负责处理PDF文档的翻译流程"""
    
    def __init__(self):
        """初始化TranslationService对象"""
        pass
    
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
    
    def process_translation(self, task, input_filepath, source_lang, target_lang, translator_type, unique_id, filename, doc_type=config.DEFAULT_DOC_TYPE, glossary="", page_range="", output_format="pdf"):
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
        """
        try:
            logger.info(f"开始处理任务 {task.task_id}，文件: {filename}")
            # 更新任务状态为处理中
            task.set_status('processing')
            
            # 优化：如果目标语言和源语言相同，直接拷贝原始页
            if source_lang == target_lang:
                logger.info(f"任务 {task.task_id} 源语言和目标语言相同，直接拷贝原始页")
                task.update_progress(30, '正在准备输出文件...')
                
                # 生成输出文件路径
                output_filename = f"translated_{unique_id}_{filename}"
                output_filepath = os.path.join(config.OUTPUT_FOLDER, output_filename)
                
                # 提取PDF文本以获取总页数
                extracted_content = pdf_extractor.extract_text(input_filepath)
                total_pages = extracted_content.total_pages
                
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
                        for page_num in sorted(target_pages):
                            # 转换为原始文档的索引（从0开始）
                            original_page_idx = page_num - 1
                            # 跳过超出范围的页码
                            if original_page_idx < 0 or original_page_idx >= len(original_doc):
                                logger.warning(f"任务 {task.task_id} 页码 {page_num} 超出原始文档范围，跳过")
                                continue
                            # 克隆页面到新文档
                            new_doc.insert_pdf(original_doc, from_page=original_page_idx, to_page=original_page_idx)
                        
                        # 保存新文档
                        new_doc.save(output_filepath)
                        new_doc.close()
                    
                    logger.info(f"任务 {task.task_id} 拷贝指定页码的页面完成，共拷贝 {len(target_pages)} 页")
                
                task.update_progress(90, '正在清理临时文件...')
                # 清理临时文件
                remove_file(input_filepath)
                logger.info(f"任务 {task.task_id} 已清理临时文件")
                
                task.update_progress(100, '翻译完成！')
                # 设置任务结果
                task.set_result(output_filename)
                logger.info(f"任务 {task.task_id} 完成，输出文件: {output_filename}")
                return
            
            task.update_progress(20, '正在提取PDF文本...')
            
            # 1.1 先获取总页数
            logger.info(f"任务 {task.task_id} 开始获取总页数")
            # 使用轻量级方式获取总页数
            with fitz.open(input_filepath) as doc:
                total_pages = len(doc)
            logger.info(f"任务 {task.task_id} 获取总页数完成: {total_pages}")
            
            if task.is_canceled():
                # 清理临时文件
                remove_file(input_filepath)
                logger.info(f"任务 {task.task_id} 被取消，已清理临时文件")
                return
            
            # 1.2 解析页码范围
            target_pages = self.parse_page_range(page_range, total_pages)
            logger.info(f"任务 {task.task_id} 需要翻译的页码: {sorted(target_pages)}")
            
            # 1.3 根据页码范围提取PDF文本
            logger.info(f"任务 {task.task_id} 开始提取PDF文本")
            extracted_content = pdf_extractor.extract_text(input_filepath, pages=list(target_pages))
            logger.info(f"任务 {task.task_id} PDF文本提取完成")
            
            # 保存提取的图像信息
            extracted_images = extracted_content.images
            logger.info(f"任务 {task.task_id} 提取到 {len(extracted_images)} 个图像")
            
            # 添加blocks信息日志
            logger.info(f"任务 {task.task_id} 提取到的blocks信息: 总页数={extracted_content.total_pages}")
            # 不再使用'blocks'键，而是直接使用pages属性
            total_blocks = sum(len(page.text_blocks) for page in extracted_content.pages if page.page_num in target_pages)
            logger.info(f"任务 {task.task_id} 共提取到 {total_blocks} 个完整文本块")
            
            task.update_progress(30, '正在创建翻译器...')
            
            # 2. 创建翻译器实例
            logger.info(f"任务 {task.task_id} 开始创建翻译器")
            translator = self.get_translator(translator_type)
            logger.info(f"任务 {task.task_id} 翻译器创建完成")
            
            if task.is_canceled():
                # 清理临时文件
                remove_file(input_filepath)
                logger.info(f"任务 {task.task_id} 被取消，已清理临时文件")
                return
            
            task.update_progress(40, '正在翻译文本内容...')
            
            logger.info(f"任务 {task.task_id} 开始翻译文本内容")
            # 3. 翻译文本内容
            translated_content = {
                'tables': []
            }
            
            # 收集所有页面的所有块，方便上下文查找
            logger.info(f"任务 {task.task_id} 将blocks信息添加到translated_content中")
            translated_content['blocks'] = []
            
            # 1. 收集所有页面的所有块，方便上下文查找
            # 只收集正文块，简化后续流程
            all_blocks = []
            block_index = 0
            for page in extracted_content.pages:
                # 只处理指定页码的页面
                if page.page_num not in target_pages:
                    continue
                
                # 页面的text_blocks已经是按垂直位置排序的
                for text_block in page.text_blocks:
                    # 只添加正文块
                    if text_block.is_body_text:
                        all_blocks.append({
                            'text_block': text_block,  # 直接保存TextBlock对象
                            'page_num': page.page_num,  # 保存页面号
                            'index': block_index  # 添加序号标识
                        })
                        block_index += 1
            
            if not all_blocks:
                logger.warning(f"任务 {task.task_id} 没有找到需要翻译的文本块")
                task.update_progress(100, '没有找到需要翻译的文本块')
                return
            
            # 2. 语义块合并
            logger.info(f"任务 {task.task_id} 开始语义块合并，原始块数量: {len(all_blocks)}")
            # 语义块合并
            merged_blocks, block_mapping = merge_semantic_blocks(all_blocks)
            logger.info(f"任务 {task.task_id} 语义块合并完成，原始块数量: {len(all_blocks)}, 合并后块数量: {len(merged_blocks)}")
            
            # 记录合并块的具体内容
            for i, merged_block in enumerate(merged_blocks):
                logger.info(f"任务 {task.task_id} 合并块 {i+1} 内容: {merged_block['block_text']}")
            
            # 翻译合并后的块
            total_original_blocks = len(all_blocks)
            translated_blocks = 0
            
            # 创建页面级别的翻译结果列表
            page_translated_blocks_dict = {}
            for page in extracted_content.pages:
                if page.page_num in target_pages:
                    page_translated_blocks_dict[page.page_num] = PdfPage(page.page_num, [])
            
            # 保存合并后的翻译结果，用于Word生成
            merged_translations = []
            
            for i, merged_block in enumerate(merged_blocks):
                logger.info(f"任务 {task.task_id} 处理合并块 {i+1}/{len(merged_blocks)}")
                logger.info(f"任务 {task.task_id} 合并块 {i+1} 原文: {merged_block['block_text']}")
                
                # 检查合并块是否包含正文
                # 检查合并块中的原始块是否有正文
                is_body_block = any(block['text_block'].is_body_text for block in merged_block['original_blocks'])
                
                if is_body_block:
                    logger.info(f"任务 {task.task_id} 合并块 {i+1} 是正文块，开始翻译")
                    # 调用翻译API
                    merged_translation = translator.translate(
                        merged_block['block_text'],
                        source_lang,
                        target_lang,
                        doc_type=doc_type,
                        glossary=glossary
                    )
                    logger.info(f"任务 {task.task_id} 合并块 {i+1} 翻译结果: {merged_translation}")
                else:
                    logger.info(f"任务 {task.task_id} 合并块 {i+1} 是非正文块，直接使用原文")
                    # 非正文块直接使用原文
                    merged_translation = merged_block['block_text']
                
                # 保存合并后的翻译结果
                first_block = merged_block['original_blocks'][0]
                first_text_block = first_block['text_block']
                logger.info(f"合并块 {i+1} 第一个原始块字体大小: {first_text_block.font_size}, 文本: '{first_text_block.block_text[:50]}...'")
                
                merged_translations.append({
                    'text': merged_translation,
                    'page_num': first_block['page_num'],  # 使用第一个原始块的页码
                    'font': first_text_block.font,
                    'font_size': first_text_block.font_size,
                    'color': first_text_block.color,
                    'bold': first_text_block.bold,
                    'italic': first_text_block.italic
                })
                
                # 记录合并块中所有原始块的字体大小
                for j, block_info in enumerate(merged_block['original_blocks']):
                    text_block = block_info['text_block']
                    logger.info(f"合并块 {i+1} 原始块 {j+1} 字体大小: {text_block.font_size}, 文本: '{text_block.block_text[:50]}...'")
                
                # 拆分翻译结果
                original_blocks = merged_block['original_blocks']
                translated_block_texts = split_translated_result(merged_translation, original_blocks)
                logger.info(f"任务 {task.task_id} 合并块 {i+1} 拆分结果: {translated_block_texts}")
                
                # 获取合并块的最大宽度和高度
                max_width = merged_block.get('max_width', 0)
                max_height = merged_block.get('max_height', 0)
                
                # 获取第一个原始块的样式信息，用于统一应用到所有拆分块
                first_block = merged_block['original_blocks'][0]
                first_text_block = first_block['text_block']
                merged_font = first_text_block.font
                merged_font_size = first_text_block.font_size
                merged_color = first_text_block.color
                merged_flags = first_text_block.flags
                logger.info(f"任务 {task.task_id} 合并块 {i+1} 将使用统一样式: 字体={merged_font}, 字体大小={merged_font_size}")
                
                # 将拆分后的结果映射回原始块
                for j, block_text in enumerate(translated_block_texts):
                    original_block_info = original_blocks[j]
                    text_block = original_block_info['text_block']  # 获取TextBlock对象
                    page_num = original_block_info['page_num']
                    
                    # 检查当前页是否在目标页码集合中
                    if page_num not in target_pages:
                        continue
                    
                    # 更新原始文本框为合并时得到的最大文本框
                    original_bbox = text_block.block_bbox
                    if max_width > 0 and max_height > 0:
                        # 计算新的边界框，保持左上角坐标不变，使用最大宽度和高度
                        new_bbox = (original_bbox[0], original_bbox[1], original_bbox[0] + max_width, original_bbox[1] + max_height)
                    else:
                        new_bbox = original_bbox
                    
                    # 创建翻译后的TextBlock对象，使用更新后的边界框
                    translated_text_block = TextBlock(
                        block_no=text_block.block_no,
                        text=block_text,
                        bbox=new_bbox,
                        block_type=text_block.block_type
                    )
                    
                    # 更新样式信息 - 使用合并块的统一样式（来自第一个原始块）
                    translated_text_block.update_style(
                        font=merged_font,
                        font_size=merged_font_size,
                        color=merged_color,
                        flags=merged_flags
                    )
                    
                    # 添加到对应页面的翻译结果中
                    page_translated_blocks_dict[page_num].text_blocks.append(translated_text_block)
                    translated_blocks += 1
                
                # 更新进度
                progress = 40 + int((translated_blocks / total_original_blocks) * 30)
                task.update_progress(progress, f'正在翻译文本: {translated_blocks}/{total_original_blocks}')
            
            # 添加合并后的翻译结果到translated_content
            translated_content['merged_translations'] = merged_translations
            
            # 将翻译结果添加到translated_content中
            translated_content['blocks'] = [page_translated_blocks_dict[page_num] for page_num in sorted(page_translated_blocks_dict.keys())]
            
            logger.info(f"任务 {task.task_id} 翻译完成，总翻译块数量: {translated_blocks}")
            
            # 直接使用原始样式信息，不再需要text_content字段
            logger.info(f"任务 {task.task_id} 直接使用原始样式信息，不再需要text_content字段")
            
            logger.info(f"任务 {task.task_id} 文本翻译完成")
            
            if task.is_canceled():
                # 清理临时文件
                remove_file(input_filepath)
                logger.info(f"任务 {task.task_id} 被取消，已清理临时文件")
                return
            
            # 翻译表格内容
            if extracted_content.tables:
                if not task.update_progress(70, '正在翻译表格内容...'):
                    # 清理临时文件
                    remove_file(input_filepath)
                    logger.info(f"任务 {task.task_id} 被取消，已清理临时文件")
                    return
                
                logger.info(f"任务 {task.task_id} 开始翻译表格内容")
                for table in extracted_content.tables:
                    # 只翻译指定页码的表格
                    if table.page_num not in target_pages:
                        continue
                    
                    translated_table = {
                        'page_num': table.page_num,
                        'table_idx': table.table_idx,
                        'content': []
                    }
                    
                    for row in table.content:
                        if task.is_canceled():
                            # 清理临时文件
                            remove_file(input_filepath)
                            logger.info(f"任务 {task.task_id} 被取消，已清理临时文件")
                            return
                        
                        translated_row = []
                        for cell in row:
                            if task.is_canceled():
                                # 清理临时文件
                                remove_file(input_filepath)
                                logger.info(f"任务 {task.task_id} 被取消，已清理临时文件")
                                return
                            
                            if cell:
                                # 调用翻译API
                                translated_cell = translator.translate(
                                    cell,
                                    source_lang,
                                    target_lang
                                )
                                translated_row.append(translated_cell)
                            else:
                                translated_row.append('')
                        translated_table['content'].append(translated_row)
                    
                    translated_content['tables'].append(translated_table)
                
                logger.info(f"任务 {task.task_id} 表格翻译完成")
            
            if task.is_canceled():
                # 清理临时文件
                remove_file(input_filepath)
                logger.info(f"任务 {task.task_id} 被取消，已清理临时文件")
                return
            
            if not task.update_progress(80, '正在生成新PDF...'):
                # 清理临时文件
                remove_file(input_filepath)
                logger.info(f"任务 {task.task_id} 被取消，已清理临时文件")
                return
            
            logger.info(f"任务 {task.task_id} 开始生成新PDF")
            # 4. 生成新PDF
            output_filename = f"translated_{unique_id}_{filename}"
            output_filepath = os.path.join(config.OUTPUT_FOLDER, output_filename)
            
            # 添加调用前的日志，记录translated_content中的blocks信息
            logger.info(f"任务 {task.task_id} 准备调用PDF生成器")
            logger.info(f"任务 {task.task_id} translated_content包含blocks信息: {('blocks' in translated_content)}")
            if 'blocks' in translated_content:
                total_blocks = sum(len(page.text_blocks) for page in translated_content['blocks'])
                logger.info(f"任务 {task.task_id} 传递给生成器的blocks信息: 总页数={len(translated_content['blocks'])}, 总blocks数={total_blocks}")
            
            output_files = []
            
            # 处理PDF生成
            if output_format in ['pdf', 'both']:
                # 创建PDF生成器实例
                pdf_generator = PdfGenerator()
                # 生成翻译后的PDF，传递目标语言参数
                pdf_generator.generate_pdf(input_filepath, translated_content, output_filepath, target_lang)
                logger.info(f"任务 {task.task_id} PDF生成完成，输出文件: {output_filename}")
                output_files.append(output_filename)
            
            # 处理Word生成
            if output_format in ['docx', 'both']:
                # 生成Word文件名
                docx_filename = f"translated_{unique_id}_{os.path.splitext(filename)[0]}.docx"
                docx_filepath = os.path.join(config.OUTPUT_FOLDER, docx_filename)
                
                # 创建Word生成器实例
                docx_generator = DocxGenerator()
                # 生成翻译后的Word文档
                docx_generator.generate_docx(translated_content, extracted_images, docx_filepath, target_lang)
                logger.info(f"任务 {task.task_id} Word文档生成完成，输出文件: {docx_filename}")
                output_files.append(docx_filename)
            
            if task.is_canceled():
                # 清理临时文件和输出文件
                remove_file(input_filepath)
                remove_file(output_filepath)
                logger.info(f"任务 {task.task_id} 被取消，已清理输出文件")
                return
            
            if not task.update_progress(90, '正在清理临时文件...'):
                # 清理临时文件和输出文件
                remove_file(input_filepath)
                remove_file(output_filepath)
                logger.info(f"任务 {task.task_id} 被取消，已清理输出文件")
                return
            
            # 清理临时文件
            remove_file(input_filepath)
            logger.info(f"任务 {task.task_id} 已清理临时文件")
            
            if not task.update_progress(100, '翻译完成！'):
                # 清理输出文件
                remove_file(output_filepath)
                logger.info(f"任务 {task.task_id} 被取消，已清理输出文件")
                return
            
            # 设置任务结果
            if output_files:
                # 如果有多个输出文件，返回第一个作为主要结果，其他作为附加结果
                task.set_result(output_files[0])
                if len(output_files) > 1:
                    task.add_attachment(output_files[1])
                logger.info(f"任务 {task.task_id} 完成，输出文件: {', '.join(output_files)}")
            else:
                logger.warning(f"任务 {task.task_id} 未生成任何输出文件")
            
        except Exception as e:
            # 记录错误信息到日志
            logger.error(f"任务 {task.task_id} 处理失败: {str(e)}", exc_info=True)
            # 设置任务错误状态
            task.set_error(f"翻译失败: {str(e)}")
            # 清理临时文件
            if 'input_filepath' in locals():
                remove_file(input_filepath)
                logger.info(f"任务 {task.task_id} 失败，已清理临时文件")
            # 清理输出文件
            if 'output_filepath' in locals():
                remove_file(output_filepath)
                logger.info(f"任务 {task.task_id} 失败，已清理输出文件")

# 创建翻译服务实例
translation_service = TranslationService()
