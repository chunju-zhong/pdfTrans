# -*- coding: utf-8 -*-
"""OCR提取器工厂函数

根据OCR引擎类型创建对应的提取器实例。
"""

import logging

from modules.ocr.base import OcrExtractor

logger = logging.getLogger(__name__)

# 支持的OCR引擎类型
SUPPORTED_OCR_ENGINES = ['paddleocr']


def create_ocr_extractor(ocr_type='paddleocr', **kwargs):
    """创建OCR提取器实例

    Args:
        ocr_type (str): OCR引擎类型，可选值:
            - 'paddleocr': PaddleOCR PP-StructureV3
        **kwargs: 传递给提取器构造函数的参数

    Returns:
        OcrExtractor: OCR提取器实例

    Raises:
        ValueError: 不支持的OCR引擎类型

    Example:
        >>> extractor = create_ocr_extractor('paddleocr', lang='en')
        >>> result = extractor.extract_from_pdf('scan.pdf')
    """
    if ocr_type == 'paddleocr':
        from modules.ocr.paddle_extractor import PaddleOcrExtractor
        return PaddleOcrExtractor(**kwargs)
    else:
        raise ValueError(
            f"不支持的OCR引擎类型: {ocr_type}，"
            f"支持的类型: {', '.join(SUPPORTED_OCR_ENGINES)}"
        )