"""_parse_det_bboxes 方法的单元测试"""
import pytest
from modules.ocr.llm_extractor import LlmOcrExtractor


@pytest.fixture
def extractor():
    return LlmOcrExtractor()


class TestParseDetBboxes:
    """_parse_det_bboxes 多 bbox 解析测试"""

    def test_single_bbox(self, extractor):
        """单个 bbox 解析"""
        result = extractor._parse_det_bboxes("[[135, 80, 861, 175]]")
        assert result == [(135.0, 80.0, 861.0, 175.0)]

    def test_double_bbox(self, extractor):
        """双 bbox 解析"""
        result = extractor._parse_det_bboxes("[[135, 80, 861, 175], [264, 197, 790, 391]]")
        assert result == [(135.0, 80.0, 861.0, 175.0), (264.0, 197.0, 790.0, 391.0)]

    def test_empty_string(self, extractor):
        """空字符串返回默认值"""
        result = extractor._parse_det_bboxes("")
        assert result == [(0, 0, 0, 0)]

    def test_malformed_input(self, extractor):
        """格式错误返回默认值"""
        result = extractor._parse_det_bboxes("invalid")
        assert result == [(0, 0, 0, 0)]
