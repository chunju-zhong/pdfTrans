#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OCR空白页检测与噪声文本过滤测试

测试前置像素方差检测（_is_blank_image）和后置OCR输出质量检测（_is_noise_text）。
"""

import pytest
import base64
import io
import numpy as np
from PIL import Image
from unittest.mock import patch, MagicMock

from modules.ocr.llm_response_parser import LlmOcrResponseParser
from modules.ocr.llm_response_parser import OcrBlock


# ============================================================
# 前置检测：_is_blank_image
# ============================================================

def _make_blank_image_base64(width=100, height=100, r=255, g=255, b=255):
    """生成纯色图像的base64编码"""
    img = Image.new('RGB', (width, height), (r, g, b))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def _make_text_image_base64(width=100, height=100):
    """生成带随机纹理的图像模拟有文字的页面"""
    arr = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    img = Image.fromarray(arr, 'RGB')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')


class TestIsBlankImage:
    """测试 _is_blank_image 像素方差检测"""

    def test_blank_white_image(self):
        """纯白图像应被检测为空白页"""
        from modules.ocr.llm_extractor import LlmOcrExtractor
        img_b64 = _make_blank_image_base64(200, 200, 255, 255, 255)
        assert LlmOcrExtractor._is_blank_image(img_b64) is True

    def test_blank_black_image(self):
        """纯黑图像应被检测为空白页"""
        from modules.ocr.llm_extractor import LlmOcrExtractor
        img_b64 = _make_blank_image_base64(200, 200, 0, 0, 0)
        assert LlmOcrExtractor._is_blank_image(img_b64) is True

    def test_blank_gray_image(self):
        """纯灰图像应被检测为空白页"""
        from modules.ocr.llm_extractor import LlmOcrExtractor
        img_b64 = _make_blank_image_base64(200, 200, 128, 128, 128)
        assert LlmOcrExtractor._is_blank_image(img_b64) is True

    def test_non_blank_text_image(self):
        """有内容的图像不应被检测为空白页"""
        from modules.ocr.llm_extractor import LlmOcrExtractor
        img_b64 = _make_text_image_base64(200, 200)
        assert LlmOcrExtractor._is_blank_image(img_b64) is False

    def test_invalid_base64(self):
        """无效base64应保守返回False（不阻断流程）"""
        from modules.ocr.llm_extractor import LlmOcrExtractor
        assert LlmOcrExtractor._is_blank_image("invalid!@#") is False


# ============================================================
# 后置检测：_is_noise_text
# ============================================================

def _make_ocr_block(text, bbox=(0, 0, 997, 997)):
    """创建测试用 OcrBlock"""
    return OcrBlock(text=text, bbox=bbox, block_type='text')


class TestIsNoiseText:
    """测试 _is_noise_text 噪声文本过滤"""

    def test_normal_english_paragraph(self):
        """正常英文段落不应被过滤"""
        block = _make_ocr_block(
            "This book is intended for a broad audience, including software engineers "
            "and machine learning practitioners who want to build applications using LLMs.",
            bbox=(140, 320, 858, 417)
        )
        assert LlmOcrResponseParser._is_noise_text(block) is False

    def test_normal_chinese_paragraph(self):
        """正常中文段落不应被过滤"""
        block = _make_ocr_block(
            "本书旨在帮助您完成工作。通常，如果本书提供了示例代码，您可以在您的程序和文档中使用它们。",
            bbox=(140, 191, 858, 327)
        )
        assert LlmOcrResponseParser._is_noise_text(block) is False

    def test_short_text(self):
        """短文本（<20字符）不应触发R3误杀"""
        block = _make_ocr_block("Chapter 1", bbox=(140, 78, 395, 136))
        assert LlmOcrResponseParser._is_noise_text(block) is False

    def test_page14_number_enumeration(self):
        """R1: 第14页数字枚举模式应被过滤（全页bbox + 数字序列）"""
        text = "1. 2. 3. 4. 5. 6. 7. 8. 9. 10. 11. 12. 13. 14. 15. 16. 17. 18. 19. 20."
        block = _make_ocr_block(text, bbox=(0, 0, 997, 997))
        assert LlmOcrResponseParser._is_noise_text(block) is True

    def test_page14_with_hash_prefix(self):
        """R1: 带#前缀的数字枚举（第14页实际格式）"""
        text = "# 1. 2. 3. 4. 5. 6. 7. 8. 9. 10. 11. 12. 13. 14. 15. 16. 17. 18. 19. 20."
        block = _make_ocr_block(text, bbox=(0, 0, 997, 997))
        assert LlmOcrResponseParser._is_noise_text(block) is True

    def test_page16_repeating_digits(self):
        """R2: 第16页重复数字序列应被过滤"""
        block = _make_ocr_block(
            "1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1",
            bbox=(140, 320, 858, 417)
        )
        assert LlmOcrResponseParser._is_noise_text(block) is True

    def test_digit_dot_only(self):
        """R2: 纯数字+点应被过滤"""
        block = _make_ocr_block(
            "1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1",
            bbox=(200, 200, 500, 500)
        )
        assert LlmOcrResponseParser._is_noise_text(block) is True

    def test_mixed_text_with_numbers(self):
        """含数字的正常文本不应被过滤"""
        block = _make_ocr_block(
            "In 2024, over 1.5 million developers used LLMs for 2.3 billion API calls. "
            "This represents a 45% increase from 2023.",
            bbox=(140, 191, 858, 327)
        )
        assert LlmOcrResponseParser._is_noise_text(block) is False

    def test_symbol_dominated_text(self):
        """R3: 符号占比>85%的文本应被过滤"""
        block = _make_ocr_block(
            ">>> --- *** &&& ^^^ ### !!! ~~~ @@@ $$$ %%%",
            bbox=(140, 320, 858, 417)
        )
        assert LlmOcrResponseParser._is_noise_text(block) is True

    def test_code_snippet(self):
        """代码片段不应被误杀"""
        block = _make_ocr_block(
            "def hello():\n    print('hello world')\n    return 42",
            bbox=(140, 320, 858, 417)
        )
        assert LlmOcrResponseParser._is_noise_text(block) is False

    def test_tableau_table_content(self):
        """含有数字和点的表格数据不应误杀"""
        block = _make_ocr_block(
            "1. Introduction to LLMs\n2. Transformer Architecture\n3. Fine-tuning Methods",
            bbox=(140, 320, 858, 417)
        )
        # 不是全页bbox, 列表项仅3个，不满足 R1 (≥5)
        assert LlmOcrResponseParser._is_noise_text(block) is False

    def test_empty_text(self):
        """空文本不应被过滤"""
        block = _make_ocr_block("", bbox=(0, 0, 997, 997))
        assert LlmOcrResponseParser._is_noise_text(block) is False

    def test_normal_text_with_page_numbers(self):
        """含页码的正常文本不应误杀"""
        block = _make_ocr_block(
            "See page 14 for more details. Figure 5 shows the results.",
            bbox=(140, 320, 858, 417)
        )
        assert LlmOcrResponseParser._is_noise_text(block) is False


# ============================================================
# 集成测试：_map_ocr_blocks_to_models 中的过滤效果
# ============================================================

class TestMappingNoiseFilter:
    """测试 _map_ocr_blocks_to_models 中的噪声过滤"""

    def test_noise_block_skipped_in_mapping(self, caplog):
        """噪声文本块在映射中被跳过"""
        from modules.ocr.llm_response_parser import LlmOcrResponseParser

        parser = LlmOcrResponseParser('aiping', 'en', source_lang='en')

        ocr_blocks = [
            _make_ocr_block("正常段落文本", bbox=(140, 320, 858, 417)),
            _make_ocr_block(
                "1. 2. 3. 4. 5. 6. 7. 8. 9. 10. 11. 12. 13. 14. 15.",
                bbox=(0, 0, 997, 997)
            ),
            _make_ocr_block("另一个正常段落", bbox=(200, 500, 800, 600)),
        ]

        result = parser._map_ocr_blocks_to_models(
            ocr_blocks, page_num=14, page_info={
                'page_width_pts': 504.0,
                'page_height_pts': 661.5,
                'img_width_px': 1050,
                'img_height_px': 1379,
            }
        )

        text_blocks, tables, images = result
        # 只有2个正常块应保留，噪声块被过滤
        assert len(text_blocks) == 2
        # 验证被过滤的块是那个数字枚举块
        assert text_blocks[0].block_text == "正常段落文本"
        assert text_blocks[1].block_text == "另一个正常段落"


class TestIntegrationWithExtractor:
    """测试 _extract_page 中的空白页检测"""

    def test_blank_image_returns_none(self):
        """空白页应返回None，不调用API"""
        from modules.ocr.llm_extractor import LlmOcrExtractor

        img_b64 = _make_blank_image_base64(200, 200, 255, 255, 255)

        extractor = LlmOcrExtractor('aiping', 'en', source_lang='en')

        # 如果空白页检测生效，不会走到API调用
        result = extractor._extract_page(
            img_b64, page_num=99,
            page_info={
                'page_width_pts': 504.0,
                'page_height_pts': 661.5,
                'img_width_px': 1050,
                'img_height_px': 1379,
            }
        )
        assert result == (None, None)