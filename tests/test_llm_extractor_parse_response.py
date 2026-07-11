"""_parse_response 方法的单元测试

测试三阶段回退管道：<|ref|>标签 → JSON → Markdown
"""
import pytest
from unittest.mock import patch, MagicMock

from modules.ocr.llm_extractor import LlmOcrExtractor


@pytest.fixture
def extractor():
    return LlmOcrExtractor()


class TestParseResponseRefTagPriority:
    """<|ref|>标签格式优先级测试"""

    def test_ref_tags_takes_priority_over_json(self, extractor):
        """当响应同时包含<|ref|>标签和类似JSON的内容时，应使用<|ref|>标签格式解析

        这是核心bug修复场景：第51页的<|ref|>响应被误路由到JSON解析，
        因为响应中包含Python代码的大括号。
        """
        result_text = 'some text <|ref|>block1<|/ref|> and also {"key": "value"} inside'

        mock_block = MagicMock()

        with patch.object(extractor, '_parse_ref_tags_to_blocks', return_value=[mock_block]) as mock_ref, \
             patch.object(extractor, '_extract_json', return_value={"key": "value"}) as mock_extract, \
             patch.object(extractor, '_parse_json_to_blocks', return_value=[MagicMock()]) as mock_json, \
             patch.object(extractor, '_map_ocr_blocks_to_models', return_value='mapped_result') as mock_map:

            result = extractor._parse_response(result_text, page_num=51)

            assert result == 'mapped_result'
            mock_ref.assert_called_once_with(result_text)
            # JSON解析不应被调用
            mock_extract.assert_not_called()
            mock_json.assert_not_called()
            # 模型映射应使用ref标签解析的结果
            mock_map.assert_called_once_with(
                [mock_block], 51, None, page=None, temp_images_dir=None
            )


class TestParseResponseRefTagFallback:
    """<|ref|>标签返回空结果时回退到JSON"""

    def test_empty_ref_result_falls_back_to_json(self, extractor):
        """当<|ref|>标签解析返回空列表时，应回退到JSON解析"""
        result_text = '<|ref|><|/ref|> some text with ```json\n{"blocks": []}\n```'

        mock_json_block = MagicMock()
        json_data = {"blocks": []}

        with patch.object(extractor, '_parse_ref_tags_to_blocks', return_value=[]) as mock_ref, \
             patch.object(extractor, '_extract_json', return_value=json_data) as mock_extract, \
             patch.object(extractor, '_parse_json_to_blocks', return_value=[mock_json_block]) as mock_json, \
             patch.object(extractor, '_map_ocr_blocks_to_models', return_value='json_result') as mock_map:

            result = extractor._parse_response(result_text, page_num=1)

            assert result == 'json_result'
            mock_ref.assert_called_once()
            mock_extract.assert_called_once_with(result_text)
            mock_json.assert_called_once_with(json_data)
            mock_map.assert_called_once_with(
                [mock_json_block], 1, None, page=None, temp_images_dir=None
            )


class TestParseResponseJsonFallback:
    """JSON返回空结果时的行为"""

    def test_empty_json_result_does_not_fall_back_to_markdown(self, extractor):
        """当JSON成功解析（data不为None）但返回空列表时，不应回退到Markdown解析

        设计意图：JSON成功解析说明模型意图输出JSON格式，
        即使内容为空也应保持该格式结果，而非静默回退到Markdown。
        """
        result_text = '```json\n{"blocks": []}\n```'

        json_data = {"blocks": []}

        with patch.object(extractor, '_extract_json', return_value=json_data) as mock_extract, \
             patch.object(extractor, '_parse_json_to_blocks', return_value=[]) as mock_json, \
             patch.object(extractor, '_parse_markdown_to_blocks', return_value=[MagicMock()]) as mock_md, \
             patch.object(extractor, '_map_ocr_blocks_to_models', return_value='md_result') as mock_map:

            result = extractor._parse_response(result_text, page_num=2)

            # JSON解析成功但内容为空 → 返回None，不回退到Markdown
            assert result is None
            mock_extract.assert_called_once()
            mock_json.assert_called_once_with(json_data)
            mock_md.assert_not_called()
            mock_map.assert_not_called()


class TestParseResponseAllEmpty:
    """所有格式均返回空结果"""

    def test_all_formats_return_empty_returns_none(self, extractor):
        """当三种格式都返回空结果时，_parse_response应返回None并记录警告"""
        result_text = 'unparseable content'

        with patch.object(extractor, '_extract_json', return_value=None), \
             patch.object(extractor, '_parse_markdown_to_blocks', return_value=[]), \
             patch.object(extractor, '_map_ocr_blocks_to_models') as mock_map:

            result = extractor._parse_response(result_text, page_num=3)

            assert result is None
            mock_map.assert_not_called()


class TestParseResponseNoRefNoJson:
    """无<|ref|>标签且无JSON时直接使用Markdown"""

    def test_no_ref_tags_no_json_uses_markdown(self, extractor):
        """当响应不含<|ref|>标签且无有效JSON时，应直接使用Markdown解析"""
        result_text = 'Just some plain text with no special formatting'

        mock_md_block = MagicMock()

        with patch.object(extractor, '_extract_json', return_value=None) as mock_extract, \
             patch.object(extractor, '_parse_markdown_to_blocks', return_value=[mock_md_block]) as mock_md, \
             patch.object(extractor, '_map_ocr_blocks_to_models', return_value='md_result') as mock_map:

            result = extractor._parse_response(result_text, page_num=4)

            assert result == 'md_result'
            mock_extract.assert_called_once_with(result_text)
            mock_md.assert_called_once_with(result_text)
            mock_map.assert_called_once_with(
                [mock_md_block], 4, None, page=None, temp_images_dir=None
            )


class TestExtractJsonBraceFinding:
    """_extract_json 三级容错：直接解析 → 代码块提取 → 大括号查找"""

    def test_braces_inside_text_extracts_json(self, extractor):
        """包含大括号但不以{开头且无```json```块的文本应尝试提取JSON

        Level 3容错：_extract_json会查找文本中第一个{到最后一个}之间的内容
        并尝试解析，因此文本中间出现的合法JSON片段会被提取。
        """
        text = 'Some text with {"key": "value"} inside'
        result = extractor._extract_json(text)
        assert result == {"key": "value"}

    def test_text_starting_with_brace_parses(self, extractor):
        """以{开头的文本应尝试直接解析"""
        text = '{"blocks": []}'
        result = extractor._extract_json(text)
        assert result == {"blocks": []}

    def test_json_code_block_parses(self, extractor):
        """```json```代码块中的JSON应被正确提取"""
        text = 'Here is the result:\n```json\n{"blocks": []}\n```\nDone.'
        result = extractor._extract_json(text)
        assert result == {"blocks": []}

    def test_invalid_json_starting_with_brace_returns_none(self, extractor):
        """以{开头但不是有效JSON的文本应返回None"""
        text = '{not valid json at all'
        result = extractor._extract_json(text)
        assert result is None

    def test_invalid_json_in_code_block_returns_none(self, extractor):
        """```json```代码块中包含无效JSON应返回None"""
        text = '```json\n{broken json\n```'
        result = extractor._extract_json(text)
        assert result is None

    def test_plain_text_no_json_returns_none(self, extractor):
        """纯文本无任何JSON格式应返回None"""
        text = 'Just plain text without any JSON'
        result = extractor._extract_json(text)
        assert result is None
