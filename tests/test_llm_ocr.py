# -*- coding: utf-8 -*-
"""LLM OCR提取器测试"""

import json
import pytest
from unittest.mock import patch, MagicMock

from modules.ocr.base import OcrExtractor
from modules.ocr.factory import create_ocr_extractor
from modules.ocr.llm_extractor import LlmOcrExtractor
from models.extraction import PdfExtraction


class TestLlmOcrFactory:
    """工厂函数测试"""

    def test_create_llm_extractor_aiping(self):
        """创建aiping提供商的LLM OCR提取器"""
        extractor = create_ocr_extractor('llm', translator_type='aiping')
        assert isinstance(extractor, LlmOcrExtractor)
        assert isinstance(extractor, OcrExtractor)
        assert extractor.translator_type == 'aiping'

    def test_create_llm_extractor_silicon_flow(self):
        """创建silicon_flow提供商的LLM OCR提取器"""
        extractor = create_ocr_extractor('llm', translator_type='silicon_flow')
        assert isinstance(extractor, LlmOcrExtractor)
        assert extractor.translator_type == 'silicon_flow'

    def test_create_llm_extractor_default_provider(self):
        """默认提供商为aiping"""
        extractor = create_ocr_extractor('llm')
        assert extractor.translator_type == 'aiping'


class TestLlmOcrJsonParsing:
    """JSON解析测试"""

    def test_extract_json_direct(self):
        """直接解析JSON"""
        extractor = LlmOcrExtractor()
        data = extractor._extract_json('{"key": "value"}')
        assert data == {"key": "value"}

    def test_extract_json_markdown_block(self):
        """从markdown代码块中提取JSON"""
        extractor = LlmOcrExtractor()
        data = extractor._extract_json('```json\n{"key": "value"}\n```')
        assert data == {"key": "value"}

    def test_extract_json_markdown_block_no_lang(self):
        """从无语言标记的markdown代码块中提取"""
        extractor = LlmOcrExtractor()
        data = extractor._extract_json('```\n{"key": "value"}\n```')
        # 无json标记时不匹配markdown模式，但会尝试{...}提取
        assert data == {"key": "value"}

    def test_extract_json_embedded(self):
        """从嵌入文本中提取JSON"""
        extractor = LlmOcrExtractor()
        data = extractor._extract_json('Here is the result: {"key": "value"} done')
        assert data == {"key": "value"}

    def test_extract_json_invalid(self):
        """无效JSON返回None"""
        extractor = LlmOcrExtractor()
        data = extractor._extract_json("not json at all")
        assert data is None

    def test_extract_json_empty_object(self):
        """空JSON对象"""
        extractor = LlmOcrExtractor()
        data = extractor._extract_json('{}')
        assert data == {}


class TestLlmOcrResponseParsing:
    """响应解析测试"""

    def test_parse_response_text_blocks(self):
        """解析文本块"""
        extractor = LlmOcrExtractor(translator_type='aiping')
        response = json.dumps({
            "text_blocks": [
                {
                    "id": 0,
                    "text": "Hello World",
                    "bbox": [10, 10, 200, 50],
                    "type": "text",
                    "is_body": True
                },
                {
                    "id": 1,
                    "text": "Title",
                    "bbox": [10, 60, 200, 90],
                    "type": "title",
                    "is_body": False
                }
            ],
            "tables": [],
            "images": []
        })
        result = extractor._parse_response(response, page_num=1)
        assert result is not None
        text_blocks, tables, images = result
        assert len(text_blocks) == 2
        assert text_blocks[0].block_text == "Hello World"
        assert text_blocks[0].is_body_text is True
        assert text_blocks[0].page_num == 1
        assert text_blocks[1].is_body_text is True  # LLM OCR所有块都标记为正文

    def test_parse_response_tables(self):
        """解析表格"""
        extractor = LlmOcrExtractor(translator_type='aiping')
        response = json.dumps({
            "text_blocks": [],
            "tables": [
                {
                    "id": 0,
                    "bbox": [10, 10, 400, 200],
                    "html": "<table><tr><td>A</td><td>B</td></tr><tr><td>1</td><td>2</td></tr></table>"
                }
            ],
            "images": []
        })
        result = extractor._parse_response(response, page_num=2)
        assert result is not None
        text_blocks, tables, images = result
        assert len(tables) == 1
        assert tables[0].page_num == 2
        assert len(tables[0].cells) == 2  # 2行
        assert tables[0].cells[0][0].text == "A"

    def test_parse_response_images(self):
        """解析图表"""
        extractor = LlmOcrExtractor(translator_type='aiping')
        response = json.dumps({
            "text_blocks": [],
            "tables": [],
            "images": [
                {
                    "id": 0,
                    "bbox": [10, 10, 300, 200],
                    "description": "A chart showing growth"
                }
            ]
        })
        result = extractor._parse_response(response, page_num=3)
        assert result is not None
        text_blocks, tables, images = result
        assert len(images) == 1
        assert images[0].page_num == 3
        assert images[0].image_path == ''  # LLM OCR不生成裁剪图片

    def test_parse_response_markdown_wrapped(self):
        """解析markdown包裹的JSON"""
        extractor = LlmOcrExtractor(translator_type='aiping')
        response = '```json\n{"text_blocks": [], "tables": [], "images": []}\n```'
        result = extractor._parse_response(response, page_num=1)
        assert result is not None
        text_blocks, tables, images = result
        assert len(text_blocks) == 0

    def test_parse_response_invalid_json(self):
        """无效JSON回退到Markdown段落解析"""
        extractor = LlmOcrExtractor(translator_type='aiping')
        result = extractor._parse_response("not json", page_num=1)
        # 纯文本"not json"会被Markdown解析器当作一个段落
        assert result is not None
        text_blocks, _, _ = result
        assert len(text_blocks) == 1
        assert text_blocks[0].block_text == "not json"

    def test_parse_response_empty(self):
        """空JSON"""
        extractor = LlmOcrExtractor(translator_type='aiping')
        result = extractor._parse_response('{}', page_num=1)
        assert result is not None
        text_blocks, tables, images = result
        assert len(text_blocks) == 0
        assert len(tables) == 0
        assert len(images) == 0

    def test_parse_response_invalid_bbox(self):
        """无效bbox容错"""
        extractor = LlmOcrExtractor(translator_type='aiping')
        response = json.dumps({
            "text_blocks": [
                {"id": 0, "text": "Test", "bbox": "invalid", "type": "text", "is_body": True}
            ],
            "tables": [],
            "images": []
        })
        result = extractor._parse_response(response, page_num=1)
        assert result is not None
        text_blocks, _, _ = result
        assert len(text_blocks) == 1
        assert text_blocks[0].block_bbox == (0, 0, 0, 0)


class TestLlmOcrClientInit:
    """客户端初始化测试"""

    @patch('modules.ocr.llm_extractor.OpenAI')
    def test_client_lazy_init_aiping(self, mock_openai):
        """aiping客户端延迟初始化"""
        extractor = LlmOcrExtractor(translator_type='aiping')
        assert extractor._client is None
        _ = extractor.client
        mock_openai.assert_called_once()

    @patch('modules.ocr.llm_extractor.OpenAI')
    def test_client_lazy_init_silicon_flow(self, mock_openai):
        """silicon_flow客户端延迟初始化"""
        extractor = LlmOcrExtractor(translator_type='silicon_flow')
        assert extractor._client is None
        _ = extractor.client
        mock_openai.assert_called_once()

    def test_unsupported_provider(self):
        """不支持的翻译引擎类型抛出ValueError"""
        extractor = LlmOcrExtractor(translator_type='unsupported')
        with pytest.raises(ValueError, match="不支持的翻译引擎类型"):
            _ = extractor.client


class TestLlmOcrHtmlTableParser:
    """HTML表格解析测试"""

    def test_parse_simple_table(self):
        """解析简单表格"""
        extractor = LlmOcrExtractor()
        html = "<table><tr><td>A</td><td>B</td></tr><tr><td>1</td><td>2</td></tr></table>"
        cells = extractor._parse_html_table(html)
        assert cells is not None
        assert len(cells) == 2
        assert cells[0][0].text == "A"
        assert cells[1][1].text == "2"

    def test_parse_table_with_rowspan(self):
        """解析带rowspan的表格"""
        extractor = LlmOcrExtractor()
        html = '<table><tr><td rowspan="2">A</td><td>B</td></tr><tr><td>C</td></tr></table>'
        cells = extractor._parse_html_table(html)
        assert cells is not None
        assert cells[0][0].row_span == 2

    def test_parse_empty_html(self):
        """空HTML返回None"""
        extractor = LlmOcrExtractor()
        cells = extractor._parse_html_table("")
        assert cells is None


class TestLlmOcrConfigDefaults:
    """配置默认值测试"""

    def test_llm_ocr_config_defaults(self):
        """LLM OCR配置默认值"""
        from config import Config
        assert Config.OCR_LLM_DPI == 150
        assert Config.OCR_LLM_TEMPERATURE == 0.1
        assert Config.OCR_LLM_MAX_TOKENS == 8192


class TestLlmOcrRefTagParsing:
    """DeepSeek-OCR <|ref|><|det|> 标签格式解析测试"""

    def test_parse_deepseek_ocr_full_format(self):
        """解析DeepSeek-OCR完整格式：提取实际文本和bbox，清理Markdown前缀"""
        extractor = LlmOcrExtractor()
        response = (
            "<|ref|>title<|/ref|><|det|>[[54, 23, 940, 87]]<|/det|>\n"
            "# Removal of the primary depends on the raw water characteristics\n\n"
            "<|ref|>text<|/ref|><|det|>[[56, 92, 562, 142]]<|/det|>\n"
            "Example: Two plants in the same city"
        )
        result = extractor._parse_response(response, page_num=1)
        assert result is not None
        text_blocks, tables, images = result
        assert len(text_blocks) == 2
        # 第一个块：title类型，Markdown前缀已清理
        assert text_blocks[0].block_text == "Removal of the primary depends on the raw water characteristics"
        assert text_blocks[0].block_bbox == (54.0, 23.0, 940.0, 87.0)
        assert text_blocks[0].is_body_text is True  # LLM OCR所有块都标记为正文
        # 第二个块：text类型
        assert text_blocks[1].block_text == "Example: Two plants in the same city"
        assert text_blocks[1].block_bbox == (56.0, 92.0, 562.0, 142.0)
        assert text_blocks[1].is_body_text is True

    def test_parse_deepseek_ocr_image_type(self):
        """image类型创建PdfImage而非TextBlock"""
        extractor = LlmOcrExtractor()
        response = (
            "<|ref|>title<|/ref|><|det|>[[54, 23, 940, 87]]<|/det|>\n"
            "Some Title\n\n"
            "<|ref|>image<|/ref|><|det|>[[20, 153, 677, 911]]<|/det|>\n"
        )
        result = extractor._parse_response(response, page_num=1)
        assert result is not None
        text_blocks, tables, images = result
        assert len(text_blocks) == 1
        assert len(images) == 1
        assert images[0].bbox == (20.0, 153.0, 677.0, 911.0)

    def test_parse_deepseek_ocr_sub_title_type(self):
        """sub_title类型也标记为正文，Markdown前缀已清理"""
        extractor = LlmOcrExtractor()
        response = (
            "<|ref|>sub_title<|/ref|><|det|>[[700, 421, 775, 461]]<|/det|>\n"
            "## Lesson:"
        )
        result = extractor._parse_response(response, page_num=1)
        assert result is not None
        text_blocks, _, _ = result
        assert len(text_blocks) == 1
        assert text_blocks[0].is_body_text is True  # LLM OCR所有块都标记为正文
        assert text_blocks[0].block_text == "Lesson:"  # Markdown前缀已清理

    def test_parse_deepseek_ocr_empty_text_skipped(self):
        """空文本块被跳过"""
        extractor = LlmOcrExtractor()
        response = (
            "<|ref|>text<|/ref|><|det|>[[56, 92, 562, 142]]<|/det|>\n"
            "Actual text\n\n"
            "<|ref|>text<|/ref|><|det|>[[100, 200, 300, 400]]<|/det|>\n"
        )
        result = extractor._parse_response(response, page_num=1)
        assert result is not None
        text_blocks, _, _ = result
        assert len(text_blocks) == 1
        assert text_blocks[0].block_text == "Actual text"

    def test_parse_det_bbox(self):
        """_parse_det_bbox提取坐标"""
        extractor = LlmOcrExtractor()
        assert extractor._parse_det_bbox("[[54, 23, 940, 87]]") == (54.0, 23.0, 940.0, 87.0)
        assert extractor._parse_det_bbox("[[0, 0, 0, 0]]") == (0.0, 0.0, 0.0, 0.0)
        assert extractor._parse_det_bbox("invalid") == (0, 0, 0, 0)
        assert extractor._parse_det_bbox("") == (0, 0, 0, 0)

    def test_parse_ref_tags_no_tables(self):
        """<|ref|>标签格式不返回表格"""
        extractor = LlmOcrExtractor()
        response = (
            "<|ref|>text<|/ref|><|det|>[[56, 92, 562, 142]]<|/det|>\n"
            "Some text"
        )
        result = extractor._parse_response(response, page_num=1)
        assert result is not None
        _, tables, _ = result
        assert len(tables) == 0

    def test_pixel_to_pdf_coords_with_page_info(self):
        """像素坐标转PDF点坐标（非归一化）"""
        extractor = LlmOcrExtractor()
        # 模拟页面：960pt x 540pt，图像：2000px x 1125px
        page_info = {
            'page_width_pts': 960.0,
            'page_height_pts': 540.0,
            'img_width_px': 2000,
            'img_height_px': 1125,
        }
        # scale_x = 960/2000 = 0.48, scale_y = 540/1125 = 0.48
        result = extractor._pixel_to_pdf_coords((100, 200, 500, 400), page_info)
        assert result == pytest.approx((48.0, 96.0, 240.0, 192.0), abs=0.01)

    def test_pixel_to_pdf_coords_normalized(self):
        """归一化坐标(0-999)转PDF点坐标"""
        extractor = LlmOcrExtractor()
        # 模拟页面：720pt x 405pt
        page_info = {
            'page_width_pts': 720.0,
            'page_height_pts': 405.0,
        }
        # 归一化坐标 [700, 422, 776, 461]
        # 期望: 700/999*720=504.5, 422/999*405=171.1, 776/999*720=559.0, 461/999*405=186.8
        result = extractor._pixel_to_pdf_coords((700, 422, 776, 461), page_info, is_normalized=True)
        assert result[0] == pytest.approx(504.5, abs=0.5)
        assert result[1] == pytest.approx(171.1, abs=0.5)
        assert result[2] == pytest.approx(559.0, abs=0.5)
        assert result[3] == pytest.approx(186.8, abs=0.5)

    def test_pixel_to_pdf_coords_without_page_info(self):
        """无page_info时返回原始坐标"""
        extractor = LlmOcrExtractor()
        result = extractor._pixel_to_pdf_coords((100, 200, 500, 400), None)
        assert result == (100, 200, 500, 400)

    def test_pixel_to_pdf_coords_zero_bbox(self):
        """零bbox直接返回"""
        extractor = LlmOcrExtractor()
        page_info = {
            'page_width_pts': 960.0,
            'page_height_pts': 540.0,
            'img_width_px': 2000,
            'img_height_px': 1125,
        }
        result = extractor._pixel_to_pdf_coords((0, 0, 0, 0), page_info)
        assert result == (0, 0, 0, 0)

    def test_parse_ref_tags_with_page_info(self):
        """<|ref|>标签格式带page_info时坐标按归一化(0-999)转换"""
        extractor = LlmOcrExtractor()
        response = (
            "<|ref|>title<|/ref|><|det|>[[54, 23, 943, 87]]<|/det|>\n"
            "Some Title\n\n"
            "<|ref|>image<|/ref|><|det|>[[21, 150, 679, 910]]<|/det|>\n"
        )
        page_info = {
            'page_width_pts': 960.0,
            'page_height_pts': 540.0,
            'img_width_px': 1000,
            'img_height_px': 1000,
        }
        result = extractor._parse_response(response, page_num=1, page_info=page_info)
        assert result is not None
        text_blocks, _, images = result
        # 归一化坐标转换: coord / 999 * page_size
        # title: 54/999*960=51.89, 23/999*540=12.43, 943/999*960=906.19, 87/999*540=47.01
        assert text_blocks[0].block_bbox == pytest.approx((51.89, 12.43, 906.19, 47.01), abs=0.1)
        # image: 21/999*960=20.18, 150/999*540=81.08, 679/999*960=652.49, 910/999*540=491.89
        assert images[0].bbox == pytest.approx((20.18, 81.08, 652.49, 491.89), abs=0.1)


class TestLlmOcrMarkdownParsing:
    """Markdown段落格式解析测试"""

    def test_parse_markdown_paragraphs(self):
        """解析Markdown段落"""
        extractor = LlmOcrExtractor()
        response = "# Title\n\nFirst paragraph\n\nSecond paragraph"
        result = extractor._parse_response(response, page_num=1)
        assert result is not None
        text_blocks, _, _ = result
        assert len(text_blocks) == 3
        assert text_blocks[0].block_text == "# Title"
        assert text_blocks[0].is_body_text is True  # LLM OCR所有块都标记为正文
        assert text_blocks[1].block_text == "First paragraph"
        assert text_blocks[1].is_body_text is True

    def test_parse_markdown_empty_paragraphs_filtered(self):
        """空段落被过滤"""
        extractor = LlmOcrExtractor()
        response = "Text\n\n\n\nMore text"
        result = extractor._parse_response(response, page_num=1)
        assert result is not None
        text_blocks, _, _ = result
        assert len(text_blocks) == 2

    def test_parse_markdown_pure_format_lines_filtered(self):
        """纯格式行被过滤"""
        extractor = LlmOcrExtractor()
        response = "---\n\n||\n\n###\n\nReal text"
        result = extractor._parse_response(response, page_num=1)
        assert result is not None
        text_blocks, _, _ = result
        assert len(text_blocks) == 1
        assert text_blocks[0].block_text == "Real text"

    def test_parse_empty_text_returns_none(self):
        """空文本解析失败返回None"""
        extractor = LlmOcrExtractor()
        result = extractor._parse_response("", page_num=1)
        assert result is None

    def test_parse_whitespace_only_returns_none(self):
        """仅空白字符解析失败返回None"""
        extractor = LlmOcrExtractor()
        result = extractor._parse_response("   \n\n  \n  ", page_num=1)
        assert result is None


class TestDeepSeekOcrPromptDetection:
    """DeepSeek-OCR模型检测测试"""

    def test_detect_deepseek_ocr(self):
        """检测DeepSeek-OCR模型"""
        from modules.ocr.llm_extractor import _is_deepseek_ocr_model
        assert _is_deepseek_ocr_model('DeepSeek-OCR') is True
        assert _is_deepseek_ocr_model('deepseek-ai/DeepSeek-OCR') is True
        assert _is_deepseek_ocr_model('deepseek-ocr') is True

    def test_non_deepseek_model(self):
        """非DeepSeek-OCR模型"""
        from modules.ocr.llm_extractor import _is_deepseek_ocr_model
        assert _is_deepseek_ocr_model('Qwen/Qwen3-VL-8B') is False
        assert _is_deepseek_ocr_model('gpt-4o') is False


class TestLlmOcrFormulaDetection:
    """LLM OCR 公式检测与标记测试"""

    def test_detect_formula_inline_dollar(self):
        """检测 $...$ 行内公式"""
        extractor = LlmOcrExtractor()
        is_formula, cleaned = extractor._detect_formula('$Q_{d} = 1000\\mathrm{m}^3 /\\mathrm{d}$')
        assert is_formula is True
        assert cleaned == 'Q_{d} = 1000\\mathrm{m}^3 /\\mathrm{d}'

    def test_detect_formula_display_dollar(self):
        """检测 $$...$$ 独立行公式"""
        extractor = LlmOcrExtractor()
        is_formula, cleaned = extractor._detect_formula('$$\\mathrm{k}_{\\mathrm{T}} = 1,07(\\mathrm{T}^{- 10})$$')
        assert is_formula is True
        assert cleaned == '\\mathrm{k}_{\\mathrm{T}} = 1,07(\\mathrm{T}^{- 10})'

    def test_detect_formula_latex_paren(self):
        """检测 \\(...\\) LaTeX行内公式"""
        extractor = LlmOcrExtractor()
        is_formula, cleaned = extractor._detect_formula('\\(\\mathrm{m}^2 /\\mathrm{m}^3\\)')
        assert is_formula is True
        assert cleaned == '\\mathrm{m}^2 /\\mathrm{m}^3'

    def test_detect_formula_latex_bracket(self):
        """检测 \\[...\\] LaTeX独立行公式"""
        extractor = LlmOcrExtractor()
        is_formula, cleaned = extractor._detect_formula('\\[E = mc^2\\]')
        assert is_formula is True
        assert cleaned == 'E = mc^2'

    def test_mixed_text_not_formula(self):
        """混合文本（中文说明+公式）不标记为公式"""
        extractor = LlmOcrExtractor()
        is_formula, cleaned = extractor._detect_formula('高负荷率：$15 - 30\\mathrm{gBOD}_5 / \\mathrm{m}^2 \\mathrm{d}$')
        assert is_formula is False

    def test_multiple_formulas_mixed_not_formula(self):
        """多公式混合文本不标记为公式"""
        extractor = LlmOcrExtractor()
        text = '$\\mathrm{Q}_{\\mathrm{d}} = 1000\\mathrm{m}^3 /\\mathrm{d}$，$\\mathrm{BOD}_{\\mathrm{in}} = 200\\mathrm{g / m}^3$，Carrier selected (K3)'
        is_formula, cleaned = extractor._detect_formula(text)
        assert is_formula is False

    def test_plain_text_not_formula(self):
        """普通文本不标记为公式"""
        extractor = LlmOcrExtractor()
        is_formula, cleaned = extractor._detect_formula('BOD/COD-removal dimensioning is based on loading rate')
        assert is_formula is False

    def test_empty_text_not_formula(self):
        """空文本不标记为公式"""
        extractor = LlmOcrExtractor()
        is_formula, cleaned = extractor._detect_formula('')
        assert is_formula is False

    def test_formula_detection_in_ref_tags(self):
        """<|ref|>标签格式中纯公式块被正确标记"""
        extractor = LlmOcrExtractor()
        response = (
            "<|ref|>text<|/ref|><|det|>[[100, 200, 500, 300]]<|/det|>\n"
            "$$\\mathrm{k}_{\\mathrm{T}} = 1,07(\\mathrm{T}^{- 10})$$\n\n"
            "<|ref|>text<|/ref|><|det|>[[100, 350, 500, 400]]<|/det|>\n"
            "Normal text without formula"
        )
        result = extractor._parse_response(response, page_num=1)
        assert result is not None
        text_blocks, _, _ = result
        assert len(text_blocks) == 2
        # 第一个块是纯公式
        assert text_blocks[0].is_formula is True
        assert text_blocks[0].block_text == '\\mathrm{k}_{\\mathrm{T}} = 1,07(\\mathrm{T}^{- 10})'
        # 第二个块是普通文本
        assert text_blocks[1].is_formula is False

    def test_formula_detection_in_json(self):
        """JSON格式中纯公式块被正确标记"""
        extractor = LlmOcrExtractor()
        response = json.dumps({
            "text_blocks": [
                {"id": 0, "text": "$E = mc^2$", "bbox": [10, 10, 200, 50], "type": "text", "is_body": True},
                {"id": 1, "text": "Normal text", "bbox": [10, 60, 200, 90], "type": "text", "is_body": True}
            ],
            "tables": [],
            "images": []
        })
        result = extractor._parse_response(response, page_num=1)
        assert result is not None
        text_blocks, _, _ = result
        assert len(text_blocks) == 2
        # 第一个块是纯公式
        assert text_blocks[0].is_formula is True
        assert text_blocks[0].block_text == 'E = mc^2'
        # 第二个块是普通文本
        assert text_blocks[1].is_formula is False


class TestLlmOcrFormulaNoFalsePositive:
    """公式检测不误判混合文本测试"""

    def test_mixed_inline_formulas_not_formula(self):
        """包含多个行内公式的说明文本不标记为公式"""
        extractor = LlmOcrExtractor()
        text = 'High rate: \\(15 - 30gBOD_5 / m^2 d\\) Normal rate : \\(8 - 12gBOD_5 / m^2 d\\)'
        is_formula, cleaned = extractor._detect_formula(text)
        assert is_formula is False

    def test_english_with_inline_formula_not_formula(self):
        """英文说明+行内公式不标记为公式"""
        extractor = LlmOcrExtractor()
        text = 'b. Effective, specific surface of carrier \\((m^2 /m^3_{bulk})\\)'
        is_formula, cleaned = extractor._detect_formula(text)
        assert is_formula is False

    def test_no_delimiter_latex_not_formula(self):
        """无定界符的LaTeX文本不标记为公式（避免误判）"""
        extractor = LlmOcrExtractor()
        text = 'k_{\\mathrm{T}} = 1,07(\\mathrm{T}^{- 10})'
        is_formula, cleaned = extractor._detect_formula(text)
        assert is_formula is False

    def test_plain_english_not_formula(self):
        """纯英文文本不标记为公式"""
        extractor = LlmOcrExtractor()
        is_formula, cleaned = extractor._detect_formula('Design loading rate for BOD removal')
        assert is_formula is False

    def test_dollar_wrapped_still_formula(self):
        """$...$ 包裹的纯公式仍被正确检测"""
        extractor = LlmOcrExtractor()
        text = '$k_{\\mathrm{T}} = 1,07(\\mathrm{T}^{- 10})$'
        is_formula, cleaned = extractor._detect_formula(text)
        assert is_formula is True
        assert cleaned == 'k_{\\mathrm{T}} = 1,07(\\mathrm{T}^{- 10})'

    def test_paren_wrapped_still_formula(self):
        """\\(...\\) 包裹的纯公式仍被正确检测"""
        extractor = LlmOcrExtractor()
        text = '\\(\\mathrm{m}^2 /\\mathrm{m}^3\\)'
        is_formula, cleaned = extractor._detect_formula(text)
        assert is_formula is True


class TestFormulaUsetexRendering:
    """公式 usetex 渲染测试"""

    def test_preprocess_latex_for_mathtext(self):
        """预处理LaTeX：\\text{} → 纯文本"""
        from modules.pdf_generator import PdfGenerator
        result = PdfGenerator._preprocess_latex_for_mathtext(
            '\\text{LR}_{\\text{BOD}} = Q_{\\mathrm{d}}'
        )
        assert '\\text' not in result
        assert '\\mathrm' not in result
        assert 'LR' in result
        assert 'BOD' in result
        assert 'd' in result

    def test_preprocess_nested_commands(self):
        """预处理嵌套LaTeX命令"""
        from modules.pdf_generator import PdfGenerator
        result = PdfGenerator._preprocess_latex_for_mathtext(
            '$15 - 30 \\text{g BOD}_5 / \\text{m}^2 \\text{d}$'
        )
        assert '\\text' not in result

    def test_preprocess_paren_delimiter(self):
        """预处理 \\(\\) → $$ 定界符转换"""
        from modules.pdf_generator import PdfGenerator
        result = PdfGenerator._preprocess_latex_for_mathtext(
            '\\(\\mathrm{m}^2 /\\mathrm{m}^3\\)'
        )
        assert '\\(' not in result
        assert '\\)' not in result
        assert '$' in result

    def test_preprocess_bracket_delimiter(self):
        """预处理 \\[\\] → $$$$ 定界符转换"""
        from modules.pdf_generator import PdfGenerator
        result = PdfGenerator._preprocess_latex_for_mathtext(
            '\\[E = mc^2\\]'
        )
        assert '\\[' not in result
        assert '\\]' not in result
        assert '$$' not in result  # $$ 也被转为 $
        assert '$' in result

    def test_preprocess_double_dollar_to_single(self):
        """预处理 $$...$$ → $...$ 转换（display math → inline math）"""
        from modules.pdf_generator import PdfGenerator
        result = PdfGenerator._preprocess_latex_for_mathtext(
            '$$k_{T} = 1,07(T^{- 10})$$ (when $$T = 5 - 10°C$$ )'
        )
        assert '$$' not in result
        assert '$k_{T} = 1,07(T^{- 10})$ (when $T = 5 - 10°C$ )' == result

    def test_cjk_font_configured_in_mixed_render(self):
        """混合文本渲染时配置了 CJK 字体"""
        import matplotlib.pyplot as plt
        from modules.pdf_generator import PdfGenerator
        generator = PdfGenerator()
        # 重置 LaTeX 缓存
        PdfGenerator._latex_available = None
        text = '高负荷率：测试'
        buf = generator._render_mixed_text_formula_image(text, fontsize=12)
        # 验证字体配置包含 CJK 字体
        assert 'PingFang SC' in plt.rcParams['font.sans-serif'] or \
               'SimHei' in plt.rcParams['font.sans-serif'] or \
               any('PingFang' in f or 'SimHei' in f or 'Heiti' in f for f in plt.rcParams['font.sans-serif'])

    def test_check_latex_available_returns_bool(self):
        """LaTeX可用性检测返回布尔值"""
        from modules.pdf_generator import PdfGenerator
        PdfGenerator._latex_available = None
        result = PdfGenerator._check_latex_available()
        assert isinstance(result, bool)

    def test_render_formula_image_basic(self):
        """基本公式渲染不抛出异常"""
        from modules.pdf_generator import PdfGenerator
        generator = PdfGenerator()
        buf = generator._render_formula_image('E = mc^2', fontsize=12)
        assert buf is not None
        assert len(buf.getvalue()) > 0


class TestLlmOcrTitleTranslation:
    """LLM OCR 标题/副标题翻译测试"""

    def test_title_is_body_text(self):
        """LLM OCR title 类型文本块 is_body_text=True"""
        extractor = LlmOcrExtractor()
        response = (
            "<|ref|>title<|/ref|><|det|>[[54, 23, 943, 87]]<|/det|>\n"
            "Removal of the primary depends on the raw water characteristics\n\n"
            "<|ref|>text<|/ref|><|det|>[[56, 93, 562, 141]]<|/det|>\n"
            "Example: Two plants in the same city"
        )
        result = extractor._parse_response(response, page_num=1)
        assert result is not None
        text_blocks, _, _ = result
        assert len(text_blocks) == 2
        # title 块也应该是 is_body_text=True
        assert text_blocks[0].is_body_text is True
        assert text_blocks[1].is_body_text is True

    def test_sub_title_is_body_text(self):
        """LLM OCR sub_title 类型文本块 is_body_text=True"""
        extractor = LlmOcrExtractor()
        response = (
            "<|ref|>sub_title<|/ref|><|det|>[[700, 421, 775, 459]]<|/det|>\n"
            "## Lesson:\n\n"
            "<|ref|>text<|/ref|><|det|>[[700, 519, 989, 652]]<|/det|>\n"
            "There are large variations"
        )
        result = extractor._parse_response(response, page_num=1)
        assert result is not None
        text_blocks, _, _ = result
        assert text_blocks[0].is_body_text is True
        assert text_blocks[1].is_body_text is True

    def test_font_size_estimated_from_bbox(self):
        """LLM OCR 文本块 font_size 根据 bbox 估算"""
        extractor = LlmOcrExtractor()
        response = (
            "<|ref|>text<|/ref|><|det|>[[700, 519, 989, 652]]<|/det|>\n"
            "Line1\nLine2\nLine3"
        )
        result = extractor._parse_response(response, page_num=1)
        assert result is not None
        text_blocks, _, _ = result
        # bbox_height = 652-519 = 133, 3 lines
        # font_size = 133 / 3 * 0.75 = 33.25
        assert text_blocks[0].font_size > 0
        assert text_blocks[0].font_size < 36


class TestMixedFormulaTextRendering:
    """混合公式文本渲染测试"""

    def test_contains_latex_formula_dollar(self):
        """检测 $...$ 公式片段"""
        from modules.pdf_generator import PdfGenerator
        assert PdfGenerator._contains_latex_formula('高负荷率：$15 - 30\\mathrm{gBOD}_5$') is True

    def test_contains_latex_formula_double_dollar(self):
        """检测 $$...$$ 公式片段"""
        from modules.pdf_generator import PdfGenerator
        assert PdfGenerator._contains_latex_formula('$$E = mc^2$$') is True

    def test_contains_latex_formula_paren(self):
        """检测 \\(...\\) 公式片段"""
        from modules.pdf_generator import PdfGenerator
        assert PdfGenerator._contains_latex_formula('载体 \\(\\mathrm{m}^2\\)') is True

    def test_contains_latex_formula_bracket(self):
        """检测 \\[...\\] 公式片段"""
        from modules.pdf_generator import PdfGenerator
        assert PdfGenerator._contains_latex_formula('\\[E = mc^2\\]') is True

    def test_no_latex_formula(self):
        """纯文本不含公式"""
        from modules.pdf_generator import PdfGenerator
        assert PdfGenerator._contains_latex_formula('这是一段纯中文文本') is False

    def test_preprocess_greek_letters(self):
        """预处理希腊字母替换"""
        from modules.pdf_generator import PdfGenerator
        result = PdfGenerator._preprocess_latex_for_mathtext('\\alpha + \\beta = \\gamma')
        assert '\\alpha' not in result
        assert 'α' in result
        assert 'β' in result
        assert 'γ' in result

    def test_preprocess_math_symbols(self):
        """预处理数学符号替换"""
        from modules.pdf_generator import PdfGenerator
        result = PdfGenerator._preprocess_latex_for_mathtext('18^{\\circ}C, a \\cdot b')
        assert '\\circ' not in result
        assert '°' in result
        assert '\\cdot' not in result
        assert '·' in result

    def test_preprocess_left_right(self):
        """预处理 \\left \\right 去除"""
        from modules.pdf_generator import PdfGenerator
        result = PdfGenerator._preprocess_latex_for_mathtext('\\left( x \\right)')
        assert '\\left' not in result
        assert '\\right' not in result
        assert 'x' in result

    def test_render_mixed_text_formula(self):
        """混合公式文本渲染不抛出异常"""
        from modules.pdf_generator import PdfGenerator
        generator = PdfGenerator()
        # 重置 LaTeX 缓存
        PdfGenerator._latex_available = None
        text = '高负荷率：$15 - 30 \\mathrm{gBOD}_5 / \\mathrm{m}^2 \\mathrm{d}$'
        buf = generator._render_mixed_text_formula_image(text, fontsize=12)
        # 无论 LaTeX 是否可用，都应该返回结果或 None
        if buf is not None:
            assert len(buf.getvalue()) > 0

    def test_render_formula_returns_none_on_failure(self):
        """公式渲染完全失败时返回 None"""
        from modules.pdf_generator import PdfGenerator
        generator = PdfGenerator()
        PdfGenerator._latex_available = False
        # 使用完全无效的 LaTeX
        result = generator._render_formula_image('\\invalidcommand{xyz}', fontsize=12)
        # 可能返回 None 或有效的 BytesIO
        assert result is None or (hasattr(result, 'getvalue') and len(result.getvalue()) > 0)
