import logging
import os
from modules.pdf_extractor import PdfExtractor
from modules.glossary_extractor import create_glossary_extractor

logger = logging.getLogger(__name__)


class GlossaryService:
    """术语提取服务"""
    
    def __init__(self):
        """初始化术语提取服务"""
        pass
    
    def extract_glossary_from_pdf(self, pdf_path, source_lang, target_lang, extractor_type='aiping'):
        """从PDF文件中提取术语表
        
        Args:
            pdf_path (str): PDF文件路径
            source_lang (str): 源语言
            target_lang (str): 目标语言
            extractor_type (str): 提取器类型 (aiping/silicon_flow)
            
        Returns:
            str: 提取的术语表，格式为"术语: 翻译"每行一个
        """
        try:
            logger.info(f"开始从PDF中提取术语表: {pdf_path}")
            
            # 1. 提取PDF文本
            text = self._extract_text_from_pdf(pdf_path)
            if not text:
                logger.warning("PDF中未提取到文本")
                return ""
            
            # 2. 调用术语提取器
            glossary_extractor = create_glossary_extractor(extractor_type)
            glossary = glossary_extractor.extract_glossary(text, source_lang, target_lang)
            
            # 3. 处理无术语的情况
            if not glossary:
                logger.info("未提取到术语")
                return ""
            
            # 修复f-string中的反斜杠问题
            line_count = len(glossary.split('\n'))
            logger.info(f"术语提取完成，提取到 {line_count} 个术语")
            return glossary
            
        except Exception as e:
            logger.error(f"从PDF中提取术语表失败: {str(e)}")
            return ""
    
    def _extract_text_from_pdf(self, pdf_path):
        """从PDF中提取文本
        
        Args:
            pdf_path (str): PDF文件路径
            
        Returns:
            str: 提取的文本
        """
        try:
            logger.info(f"开始提取PDF文本: {pdf_path}")
            
            # 使用PdfExtractor提取文本
            pdf_extractor = PdfExtractor(pdf_path)
            extraction_result = pdf_extractor.extract()
            
            # 收集所有文本，包括标题、正文等，以确保捕获所有可能的术语
            text = ""
            for page in extraction_result.pages:
                for block in page.text_blocks:
                    text += block.block_text + "\n"
            
            logger.info(f"PDF文本提取完成，提取到 {len(text)} 个字符")
            return text
            
        except Exception as e:
            logger.error(f"提取PDF文本失败: {str(e)}")
            return ""


# 创建术语提取服务实例
glossary_service = GlossaryService()
