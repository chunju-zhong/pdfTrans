# -*- coding: utf-8 -*-
"""OCR提取器抽象基类

定义OCR提取器的统一接口，所有OCR引擎实现必须继承此基类。
"""

from abc import ABC, abstractmethod


class OcrExtractor(ABC):
    """OCR提取器抽象基类

    所有OCR引擎（PaddleOCR、LLM OCR等）必须实现此接口，
    确保OCR输出能无缝接入现有翻译管线。
    """

    @abstractmethod
    def extract_from_pdf(self, pdf_path, pages=None, temp_images_dir=None):
        """从PDF中提取内容（文字、表格、图表）

        Args:
            pdf_path (str): PDF文件路径
            pages (list[int] | None): 指定要提取的页码列表（从1开始），
                None表示提取所有页面
            temp_images_dir (str | None): 临时图像目录路径，
                None表示使用默认路径

        Returns:
            PdfExtraction: 包含提取的文本、表格和图像的对象，
                结构与PdfExtractor.extract()完全一致

        Raises:
            FileNotFoundError: PDF文件不存在
            ValueError: 参数无效
        """
        pass