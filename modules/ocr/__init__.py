# -*- coding: utf-8 -*-
"""OCR模块

提供OCR文字提取功能，支持多种OCR引擎。
"""

from modules.ocr.base import OcrExtractor
from modules.ocr.factory import create_ocr_extractor
from modules.ocr.ocr_worker import OcrRetryableError, OcrFatalError

__all__ = ['OcrExtractor', 'create_ocr_extractor', 'OcrRetryableError', 'OcrFatalError']