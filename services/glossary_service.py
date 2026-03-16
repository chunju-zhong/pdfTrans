import logging
import os
import concurrent.futures
from modules.pdf_extractor import PdfExtractor
from modules.glossary_extractor import create_glossary_extractor

logger = logging.getLogger(__name__)


class GlossaryService:
    """术语提取服务"""
    
    def __init__(self, max_workers=None):
        """初始化术语提取服务
        
        Args:
            max_workers (int | None): 线程池最大工作线程数，None表示使用默认值
        """
        self.max_workers = max_workers
    
    def extract_glossary_from_pdf(self, pdf_path, source_lang, target_lang, extractor_type='aiping', pages=None, doc_type=None, task=None):
        """从PDF文件中提取术语表
        
        Args:
            pdf_path (str): PDF文件路径
            source_lang (str): 源语言
            target_lang (str): 目标语言
            extractor_type (str): 提取器类型 (aiping/silicon_flow)
            pages (list[int] | None): 指定要提取的页码列表（从1开始），None表示提取所有页面
            doc_type (str): 文档类型
            task (object, optional): 任务对象，用于更新进度. Defaults to None.
            
        Returns:
            str: 提取的术语表，格式为"术语: 翻译"每行一个
        """
        try:
            logger.info(f"开始从PDF中提取术语表: {pdf_path}")
            
            # 1. 创建术语提取器
            glossary_extractor = create_glossary_extractor(extractor_type)
            
            # 2. 预先提取所有页面的文本，避免在多线程中重复打开PDF文件
            logger.info("开始预提取所有页面的文本")
            if task:
                task.update_phase_progress('init', 100, '开始提取PDF文本...')
            page_texts = self._extract_text_from_pdf(pdf_path, pages)
            if task:
                task.update_phase_progress('pdf_extraction', 100, 'PDF文本提取完成，开始提取术语...')
            
            # 3. 获取提取到的页码列表
            pages = list(page_texts.keys())
            if not pages:
                logger.warning("PDF中未提取到文本")
                return ""
            
            logger.info(f"PDF总页数: {len(pages)}")
            
            # 4. 使用线程池并发执行术语提取
            glossary_results = []
            # 动态调整线程池大小，基于CPU核心数或用户指定值，最多8个线程
            max_workers = min(self.max_workers or os.cpu_count() or 4, 8)
            
            # 总页面数
            total_pages = len(pages)
            processed_pages = 0
            
            def process_page(page_num):
                """处理单个页面：提取术语"""
                # 获取预提取的页面文本
                page_text = page_texts.get(page_num, "")
                if page_text.strip():
                    # 提取术语
                    return glossary_extractor.extract_glossary(page_text, source_lang, target_lang, doc_type)
                return None
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 为每个页面提交任务
                future_to_page = {executor.submit(process_page, page_num): page_num for page_num in pages}
                
                # 等待所有任务完成并收集结果
                for future in concurrent.futures.as_completed(future_to_page):
                    page_num = future_to_page[future]
                    processed_pages += 1
                    
                    # 更新进度
                    if task:
                        phase_percent = int((processed_pages / total_pages) * 100)
                        task.update_phase_progress('term_extraction', phase_percent, f'正在处理第{page_num}页，共{total_pages}页...')
                        logger.info(f"任务进度更新: 第{page_num}页，阶段进度{phase_percent}%")
                    
                    try:
                        result = future.result()
                        if result:
                            glossary_results.append(result)
                    except Exception as e:
                        logger.error(f"处理页面 {page_num} 时出错: {str(e)}")
            
            # 4. 合并所有页面的术语结果
            if not glossary_results:
                logger.info("未提取到术语")
                return ""
            
            # 合并所有结果，去重并排序
            term_dict = {}
            for result in glossary_results:
                for line in result.strip().split('\n'):
                    if line.strip() and ':' in line:
                        term, translation = line.split(':', 1)
                        term = term.strip()
                        translation = translation.strip()
                        if term:
                            term_dict[term] = translation
            
            # 对术语进行排序
            sorted_terms = sorted(term_dict.items(), key=lambda x: x[0])
            
            # 构建最终术语表
            final_glossary = "\n".join([f"{term}: {translation}" for term, translation in sorted_terms])
            
            # 5. 修复f-string中的反斜杠问题
            line_count = len(sorted_terms)
            logger.info(f"术语提取完成，提取到 {line_count} 个术语")
            
            # 确保任务状态更新为100%
            if task:
                task.update_phase_progress('term_extraction', 100, '术语提取完成！')
            
            return final_glossary
            
        except Exception as e:
            logger.error(f"从PDF中提取术语表失败: {str(e)}")
            return ""
    
    def _extract_text_from_pdf(self, pdf_path, pages=None):
        """从PDF中提取文本
        
        Args:
            pdf_path (str): PDF文件路径
            pages (list[int] | None): 指定要提取的页码列表（从1开始），None表示提取所有页面
            
        Returns:
            dict: 提取的文本，键为页码，值为该页面的文本
        """
        try:
            logger.info(f"开始提取PDF文本: {pdf_path}")
            
            # 使用PdfExtractor提取文本，传递页码范围，禁用非正文文本块标记
            pdf_extractor = PdfExtractor(pdf_path)
            extraction_result = pdf_extractor.extract(pages, mark_non_body=False)
            
            # 收集所有文本，包括标题、正文等，以确保捕获所有可能的术语
            page_texts = {}
            if pages is not None:
                # 如果指定了页码列表，按列表顺序处理
                for page_num, page in zip(pages, extraction_result.pages):
                    page_text = ""
                    for block in page.text_blocks:
                        page_text += block.block_text + "\n"
                    # 添加表格文本
                    for table in extraction_result.tables:
                        if table.page_num == page_num:
                            page_text += self._extract_text_from_table(table) + "\n"
                    page_texts[page_num] = page_text
            else:
                # 如果未指定页码，按顺序从1开始编号
                for page_num, page in enumerate(extraction_result.pages, start=1):
                    page_text = ""
                    for block in page.text_blocks:
                        page_text += block.block_text + "\n"
                    # 添加表格文本
                    for table in extraction_result.tables:
                        if table.page_num == page_num:
                            page_text += self._extract_text_from_table(table) + "\n"
                    page_texts[page_num] = page_text
            
            # 计算总字符数
            total_chars = sum(len(text) for text in page_texts.values())
            logger.info(f"PDF文本提取完成，提取到 {total_chars} 个字符，共 {len(page_texts)} 页")
            return page_texts
            
        except Exception as e:
            logger.error(f"提取PDF文本失败: {str(e)}")
            return {}
    
    def _extract_text_from_table(self, table):
        """从表格中提取文本
        
        Args:
            table (PdfTable): 表格对象
            
        Returns:
            str: 提取的表格文本
        """
        try:
            table_text = ""
            # 遍历表格的所有行和列
            for row in table.cells:
                row_text = ""
                for cell in row:
                    if cell and cell.strip():
                        row_text += cell + " | "
                if row_text:
                    # 移除行尾的" | "
                    row_text = row_text.rstrip(" | ")
                    table_text += row_text + "\n"
            return table_text
        except Exception as e:
            logger.error(f"提取表格文本失败: {str(e)}")
            return ""
    
    def _extract_page_text(self, pdf_path, page_num):
        """提取单个页面的文本
        
        Args:
            pdf_path (str): PDF文件路径
            page_num (int): 页码（从1开始）
            
        Returns:
            str: 提取的文本
        """
        try:
            logger.info(f"开始提取PDF页面 {page_num} 的文本: {pdf_path}")
            
            # 使用PdfExtractor提取指定页面的文本
            pdf_extractor = PdfExtractor(pdf_path)
            extraction_result = pdf_extractor.extract([page_num])
            
            # 收集页面文本
            page_text = ""
            if extraction_result.pages:
                page = extraction_result.pages[0]
                for block in page.text_blocks:
                    page_text += block.block_text + "\n"
                # 添加表格文本
                for table in extraction_result.tables:
                    if table.page_num == page_num:
                        page_text += self._extract_text_from_table(table) + "\n"
            
            logger.info(f"PDF页面 {page_num} 文本提取完成，提取到 {len(page_text)} 个字符")
            return page_text
            
        except Exception as e:
            logger.error(f"提取PDF页面 {page_num} 文本失败: {str(e)}")
            return ""


# 创建术语提取服务实例
glossary_service = GlossaryService()
