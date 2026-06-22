"""_parse_ref_tags_to_blocks 多 bbox 拆分 TextBlock 的单元测试"""
import pytest
from unittest.mock import patch, MagicMock
from modules.ocr.llm_extractor import LlmOcrExtractor


@pytest.fixture
def extractor():
    return LlmOcrExtractor()


def _make_ref_block(block_type, det_content, text):
    """构造 <|ref|> 标签格式的响应文本"""
    return f"<|ref|>{block_type}<|/ref|><|det|>{det_content}<|/det|>\n{text}"


# page_info mock：让 _pixel_to_pdf_coords 直接返回归一化坐标（便于断言）
MOCK_PAGE_INFO = {"width": 999, "height": 999}


@pytest.fixture(autouse=True)
def mock_pixel_to_pdf(extractor):
    """让 _pixel_to_pdf_coords 返回原始坐标，便于断言 bbox 值"""
    with patch.object(extractor, '_pixel_to_pdf_coords', side_effect=lambda bbox, pi, is_normalized=False: bbox):
        yield


class TestMultiBboxSplit:
    """多 bbox 拆分 TextBlock 测试"""

    def test_two_bboxes_two_paragraphs_split(self, extractor):
        """两个 bbox + 两个段落 → 拆分为两个 TextBlock，各带对应 bbox"""
        result_text = _make_ref_block(
            "text",
            "[[135, 80, 861, 175], [264, 197, 790, 391]]",
            "First paragraph text\n\nSecond paragraph text",
        )
        text_blocks, _, _ = extractor._parse_ref_tags_to_blocks(result_text)

        assert len(text_blocks) == 2

        # 第一个 TextBlock
        assert text_blocks[0].block_text == "First paragraph text"
        assert text_blocks[0].block_bbox == (135.0, 80.0, 861.0, 175.0)
        assert text_blocks[0].block_no == 0
        assert text_blocks[0].page_num == 1
        assert text_blocks[0].is_body_text is True

        # 第二个 TextBlock
        assert text_blocks[1].block_text == "Second paragraph text"
        assert text_blocks[1].block_bbox == (264.0, 197.0, 790.0, 391.0)
        assert text_blocks[1].block_no == 1
        assert text_blocks[1].page_num == 1
        assert text_blocks[1].is_body_text is True

    def test_two_bboxes_one_paragraph_fallback(self, extractor):
        """两个 bbox + 一个段落（无 \\n\\n）→ 回退为单个 TextBlock，使用第一个 bbox"""
        result_text = _make_ref_block(
            "text",
            "[[135, 80, 861, 175], [264, 197, 790, 391]]",
            "Single paragraph without double newline",
        )
        text_blocks, _, _ = extractor._parse_ref_tags_to_blocks(result_text)

        assert len(text_blocks) == 1
        assert text_blocks[0].block_text == "Single paragraph without double newline"
        assert text_blocks[0].block_bbox == (135.0, 80.0, 861.0, 175.0)
        assert text_blocks[0].is_body_text is True

    def test_single_bbox_single_paragraph(self, extractor):
        """一个 bbox + 一个段落 → 单个 TextBlock（原有行为不变）"""
        result_text = _make_ref_block(
            "text",
            "[[135, 80, 861, 175]]",
            "Just one paragraph",
        )
        text_blocks, _, _ = extractor._parse_ref_tags_to_blocks(result_text)

        assert len(text_blocks) == 1
        assert text_blocks[0].block_text == "Just one paragraph"
        assert text_blocks[0].block_bbox == (135.0, 80.0, 861.0, 175.0)
        assert text_blocks[0].is_body_text is True

    def test_two_bboxes_three_paragraphs_fallback(self, extractor):
        """两个 bbox + 三个段落 → 段落数与 bbox 数不匹配，回退为单个 TextBlock"""
        result_text = _make_ref_block(
            "text",
            "[[135, 80, 861, 175], [264, 197, 790, 391]]",
            "First paragraph\n\nSecond paragraph\n\nThird paragraph",
        )
        text_blocks, _, _ = extractor._parse_ref_tags_to_blocks(result_text)

        assert len(text_blocks) == 1
        assert text_blocks[0].block_text == "First paragraph\n\nSecond paragraph\n\nThird paragraph"
        assert text_blocks[0].block_bbox == (135.0, 80.0, 861.0, 175.0)

    def test_three_bboxes_three_paragraphs_split(self, extractor):
        """三个 bbox + 三个段落 → 拆分为三个 TextBlock"""
        result_text = _make_ref_block(
            "text",
            "[[10, 20, 100, 50], [10, 60, 100, 90], [10, 100, 100, 130]]",
            "Para one\n\nPara two\n\nPara three",
        )
        text_blocks, _, _ = extractor._parse_ref_tags_to_blocks(result_text)

        assert len(text_blocks) == 3
        assert text_blocks[0].block_text == "Para one"
        assert text_blocks[0].block_bbox == (10.0, 20.0, 100.0, 50.0)
        assert text_blocks[1].block_text == "Para two"
        assert text_blocks[1].block_bbox == (10.0, 60.0, 100.0, 90.0)
        assert text_blocks[2].block_text == "Para three"
        assert text_blocks[2].block_bbox == (10.0, 100.0, 100.0, 130.0)
        # block_no 递增
        assert text_blocks[0].block_no == 0
        assert text_blocks[1].block_no == 1
        assert text_blocks[2].block_no == 2

    def test_multi_bbox_split_with_existing_blocks(self, extractor):
        """多 bbox 拆分时 block_no 在已有 TextBlock 之后递增"""
        # 构造两个 ref block：第一个是单 bbox，第二个是多 bbox
        block1 = _make_ref_block("text", "[[10, 10, 100, 50]]", "Existing block")
        block2 = _make_ref_block(
            "text",
            "[[200, 80, 600, 150], [200, 160, 600, 230]]",
            "New para A\n\nNew para B",
        )
        result_text = block1 + block2
        text_blocks, _, _ = extractor._parse_ref_tags_to_blocks(result_text)

        assert len(text_blocks) == 3
        assert text_blocks[0].block_no == 0
        assert text_blocks[0].block_text == "Existing block"
        assert text_blocks[1].block_no == 1
        assert text_blocks[1].block_text == "New para A"
        assert text_blocks[2].block_no == 2
        assert text_blocks[2].block_text == "New para B"
