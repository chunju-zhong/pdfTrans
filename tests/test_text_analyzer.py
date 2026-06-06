"""text_analyzer.py 测试用例

覆盖 calculate_text_similarity、_add_similar_blocks、identify_header_footer、
identify_page_numbers、mark_non_body_text 的核心逻辑。
"""

import pytest
from modules.extractors.text_analyzer import (
    calculate_text_similarity,
    _add_similar_blocks,
    identify_header_footer,
    identify_page_numbers,
    mark_non_body_text,
)
from models.text_block import TextBlock
from models.extraction import PdfPage


# ============================================================
# 辅助函数
# ============================================================

def make_block(text, bbox=(0, 0, 100, 20), page_num=1, block_no=0, font_size=9.0):
    """创建测试用 TextBlock"""
    tb = TextBlock(block_no=block_no, text=text, bbox=list(bbox), page_num=page_num)
    tb.font_size = font_size
    return tb


def make_page(page_num, blocks, page_size=(612, 792)):
    """创建测试用 PdfPage"""
    return PdfPage(page_num=page_num, text_blocks=blocks), page_size


# ============================================================
# calculate_text_similarity 测试
# ============================================================

class TestCalculateTextSimilarity:
    def test_identical_text(self):
        assert calculate_text_similarity("hello", "hello") == 1.0

    def test_completely_different(self):
        assert calculate_text_similarity("abc", "xyz") == 0.0

    def test_empty_string(self):
        assert calculate_text_similarity("", "hello") == 0.0
        assert calculate_text_similarity("hello", "") == 0.0

    def test_case_insensitive(self):
        sim = calculate_text_similarity("Hello", "hello")
        assert sim == 1.0

    def test_date_footer_similarity(self):
        """日期型页尾 '2025年2月 8' 与 '2025年2月 9' 的相似度应 > 0.8"""
        sim = calculate_text_similarity("2025年2月 8", "2025年2月 9")
        assert sim > 0.8
        assert round(sim, 4) == 0.8889

    def test_page_number_annotation_similarity(self):
        """页码标注 'xii | Foreword' 与 'xiv | Foreword' 的相似度应 > 0.8"""
        sim = calculate_text_similarity("xii | Foreword", "xiv | Foreword")
        assert sim > 0.8

    def test_dissimilar_short_text(self):
        """不相似的短文本应 < 0.8"""
        sim = calculate_text_similarity("Hello", "World")
        assert sim < 0.8


# ============================================================
# _add_similar_blocks 测试
# ============================================================

class TestAddSimilarBlocks:
    def test_date_footer_detected(self):
        """日期型页尾应被检测为非正文（阈值 0.85）"""
        block1 = make_block("2025年2月 8", block_no=1)
        block2 = make_block("2025年2月 9", block_no=2)
        non_body = set()
        processed = set()
        _add_similar_blocks([(1, block1)], [(2, block2)], processed, non_body)
        assert "2025年2月 8" in non_body
        assert "2025年2月 9" in non_body

    def test_page_number_annotation_detected(self):
        """页码标注应被检测为非正文"""
        block1 = make_block("xii | Foreword", block_no=1)
        block2 = make_block("xiv | Foreword", block_no=2)
        non_body = set()
        processed = set()
        _add_similar_blocks([(1, block1)], [(2, block2)], processed, non_body)
        assert "xii | Foreword" in non_body
        assert "xiv | Foreword" in non_body

    def test_dissimilar_text_not_detected(self):
        """不相似的文本不应被检测为非正文"""
        block1 = make_block("Introduction", block_no=1)
        block2 = make_block("Conclusion", block_no=2)
        non_body = set()
        processed = set()
        _add_similar_blocks([(1, block1)], [(2, block2)], processed, non_body)
        assert "Introduction" not in non_body
        assert "Conclusion" not in non_body

    def test_same_block_skipped(self):
        """同一页同一块号应跳过"""
        block = make_block("test", block_no=1)
        non_body = set()
        processed = set()
        _add_similar_blocks([(1, block)], [(1, block)], processed, non_body)
        assert "test" not in non_body

    def test_identical_text_detected(self):
        """完全相同的文本应被检测为非正文"""
        block1 = make_block("Confidential", block_no=1)
        block2 = make_block("Confidential", block_no=2)
        non_body = set()
        processed = set()
        _add_similar_blocks([(1, block1)], [(2, block2)], processed, non_body)
        assert "Confidential" in non_body


# ============================================================
# identify_header_footer 测试
# ============================================================

class TestIdentifyHeaderFooter:
    def test_date_footer_in_bottom_area(self):
        """底部区域的日期型页尾应被识别（相似度 > 0.85 的日期对）"""
        page_height = 792
        # 底部 15% 区域：y0 > 792 * 0.85 = 673.2
        blocks_p1 = [make_block("2025年2月 8", bbox=(0, 700, 100, 720), page_num=1, block_no=1)]
        blocks_p2 = [make_block("2025年2月 9", bbox=(0, 700, 100, 720), page_num=2, block_no=1)]
        blocks_p3 = [make_block("2025年2月 7", bbox=(0, 700, 100, 720), page_num=3, block_no=1)]

        pages = [
            PdfPage(page_num=1, text_blocks=blocks_p1),
            PdfPage(page_num=2, text_blocks=blocks_p2),
            PdfPage(page_num=3, text_blocks=blocks_p3),
        ]
        page_sizes = {1: (612, page_height), 2: (612, page_height), 3: (612, page_height)}

        result = identify_header_footer(pages, page_sizes)
        assert "2025年2月 8" in result
        assert "2025年2月 9" in result
        assert "2025年2月 7" in result

    def test_repeated_header_detected(self):
        """重复出现的页眉应被识别"""
        page_height = 792
        # 顶部 15% 区域：y1 < 792 * 0.15 = 118.8
        header_text = "Company Confidential"
        pages = []
        page_sizes = {}
        for i in range(1, 8):
            blocks = [make_block(header_text, bbox=(0, 50, 200, 70), page_num=i, block_no=1)]
            pages.append(PdfPage(page_num=i, text_blocks=blocks))
            page_sizes[i] = (612, page_height)

        result = identify_header_footer(pages, page_sizes)
        assert header_text in result

    def test_body_text_not_detected(self):
        """正文文本不应被识别为页眉页脚"""
        page_height = 792
        # 中间区域的正文
        pages = []
        page_sizes = {}
        for i in range(1, 8):
            blocks = [make_block(f"Unique paragraph {i}", bbox=(0, 300, 200, 320), page_num=i, block_no=1)]
            pages.append(PdfPage(page_num=i, text_blocks=blocks))
            page_sizes[i] = (612, page_height)

        result = identify_header_footer(pages, page_sizes)
        for i in range(1, 8):
            assert f"Unique paragraph {i}" not in result

    def test_empty_pages(self):
        """空页面应返回空集合"""
        result = identify_header_footer([], {})
        assert result == set()


# ============================================================
# identify_page_numbers 测试
# ============================================================

class TestIdentifyPageNumbers:
    def test_page_number_in_bottom(self):
        """底部小字体页码应被识别"""
        page_height = 792
        blocks = [make_block("5", bbox=(0, 750, 20, 760), page_num=5, block_no=1, font_size=8.0)]
        pages = [PdfPage(page_num=5, text_blocks=blocks)]
        page_sizes = {5: (612, page_height)}

        result = identify_page_numbers(pages, page_sizes)
        assert "5" in result

    def test_body_number_not_detected(self):
        """正文中的数字不应被识别为页码"""
        page_height = 792
        # 中间区域，大字体
        blocks = [make_block("42", bbox=(0, 400, 20, 420), page_num=1, block_no=1, font_size=12.0)]
        pages = [PdfPage(page_num=1, text_blocks=blocks)]
        page_sizes = {1: (612, page_height)}

        result = identify_page_numbers(pages, page_sizes)
        assert "42" not in result


# ============================================================
# mark_non_body_text 测试
# ============================================================

class TestMarkNonBodyText:
    def test_footer_marked_as_non_body(self):
        """页脚应被标记为非正文"""
        page_height = 792
        footer_text = "Draft"
        blocks = [make_block(footer_text, bbox=(0, 750, 100, 770), page_num=i, block_no=1) for i in range(1, 8)]
        pages = [PdfPage(page_num=i, text_blocks=[b]) for i, b in enumerate(blocks, 1)]
        page_sizes = {i: (612, page_height) for i in range(1, 8)}

        mark_non_body_text(pages, page_sizes)

        for page in pages:
            for block in page.text_blocks:
                if block.block_text == footer_text:
                    assert block.is_body_text is False

    def test_body_text_remains(self):
        """正文文本应保持 is_body_text=True"""
        page_height = 792
        body_text = "This is a paragraph of body text."
        blocks = [make_block(body_text, bbox=(0, 400, 300, 420), page_num=i, block_no=1) for i in range(1, 8)]
        pages = [PdfPage(page_num=i, text_blocks=[b]) for i, b in enumerate(blocks, 1)]
        page_sizes = {i: (612, page_height) for i in range(1, 8)}

        mark_non_body_text(pages, page_sizes)

        for page in pages:
            for block in page.text_blocks:
                assert block.is_body_text is True

    def test_disabled(self):
        """禁用标记时不应修改 is_body_text"""
        page_height = 792
        blocks = [make_block("Draft", bbox=(0, 750, 100, 770), page_num=1, block_no=1)]
        pages = [PdfPage(page_num=1, text_blocks=blocks)]
        page_sizes = {1: (612, page_height)}

        mark_non_body_text(pages, page_sizes, enable=False)

        for page in pages:
            for block in page.text_blocks:
                assert block.is_body_text is True
