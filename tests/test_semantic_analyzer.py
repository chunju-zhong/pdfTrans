import pytest
from unittest.mock import patch, MagicMock
from modules.semantic_analyzer import SemanticAnalyzer


class TestSemanticAnalyzer:
    """测试语义分析器基类"""

    def test_analyze_semantic_relationship(self):
        """测试语义分析方法"""
        analyzer = SemanticAnalyzer(
            api_key="test_key",
            api_url="https://test-api.example.com/v1",
            model="test-model"
        )

        text1 = "Hello"
        text2 = "world"

        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content='{"merge": true}'))]
            mock_create.return_value = mock_response

            result = analyzer.analyze_semantic_relationship(text1, text2, 'en')

            assert isinstance(result, bool)
            assert result == True

    def test_analyze_semantic_relationship_false(self):
        """测试语义分析方法返回false的情况"""
        analyzer = SemanticAnalyzer(
            api_key="test_key",
            api_url="https://test-api.example.com/v1",
            model="test-model"
        )

        text1 = "Introduction"
        text2 = "This chapter introduces the topic"

        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content='{"merge": false}'))]
            mock_create.return_value = mock_response

            result = analyzer.analyze_semantic_relationship(text1, text2, 'en')

            assert isinstance(result, bool)
            assert result == False

    def test_analyze_semantic_relationship_api_error(self):
        """测试语义分析方法API错误处理"""
        analyzer = SemanticAnalyzer(
            api_key="test_key",
            api_url="https://test-api.example.com/v1",
            model="test-model"
        )

        text1 = "Hello"
        text2 = "world"

        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
            mock_create.side_effect = Exception("API Error")

            result = analyzer.analyze_semantic_relationship(text1, text2, 'en')

            assert isinstance(result, bool)
            assert result == False

    def test_batch_analyze_semantic_relationship(self):
        """测试批量语义分析方法"""
        analyzer = SemanticAnalyzer(
            api_key="test_key",
            api_url="https://test-api.example.com/v1",
            model="test-model"
        )

        text_pairs = [
            ("Hello", "world"),
            ("How are", "you")
        ]

        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content='{"merge": [true, false]}'))]
            mock_create.return_value = mock_response

            result = analyzer.batch_analyze_semantic_relationship(text_pairs, 'en')

            assert isinstance(result, list)
            assert len(result) == 2
            assert result == [True, False]

    def test_batch_analyze_with_retry(self):
        """测试批量语义分析方法的重试机制"""
        analyzer = SemanticAnalyzer(
            api_key="test_key",
            api_url="https://test-api.example.com/v1",
            model="test-model"
        )

        text_pairs = [
            ("Hello", "world"),
            ("How are", "you"),
            ("I am", "fine")
        ]

        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
            mock_response1 = MagicMock()
            mock_response1.choices = [MagicMock(message=MagicMock(content='{"merge": [true, false]}'))]
            mock_response2 = MagicMock()
            mock_response2.choices = [MagicMock(message=MagicMock(content='{"merge": [true, false, true]}'))]

            mock_create.side_effect = [mock_response1, mock_response2]

            result = analyzer.batch_analyze_semantic_relationship(text_pairs, 'en')

            assert isinstance(result, list)
            assert len(result) == 3
            assert result == [True, False, True]
            assert mock_create.call_count == 2

    def test_batch_analyze_with_final_failure(self):
        """测试批量语义分析方法在最终失败时的处理"""
        analyzer = SemanticAnalyzer(
            api_key="test_key",
            api_url="https://test-api.example.com/v1",
            model="test-model"
        )

        text_pairs = [
            ("Hello", "world"),
            ("How are", "you"),
            ("I am", "fine")
        ]

        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content='{"merge": [true, false]}'))]
            mock_create.return_value = mock_response

            result = analyzer.batch_analyze_semantic_relationship(text_pairs, 'en')

            assert isinstance(result, list)
            assert len(result) == 3
            assert result == [True, False, False]
            assert mock_create.call_count == 3

    def test_batch_analyze_json_error(self):
        """测试批量语义分析方法JSON解析错误处理"""
        analyzer = SemanticAnalyzer(
            api_key="test_key",
            api_url="https://test-api.example.com/v1",
            model="test-model"
        )

        text_pairs = [
            ("Hello", "world"),
            ("How are", "you")
        ]

        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content='invalid json'))]
            mock_create.return_value = mock_response

            result = analyzer.batch_analyze_semantic_relationship(text_pairs, 'en')

            assert isinstance(result, list)
            assert len(result) == 2
            assert result == [False, False]

    def test_generate_semantic_analysis_prompt(self):
        """测试语义分析提示词生成"""
        analyzer = SemanticAnalyzer(
            api_key="test_key",
            api_url="https://test-api.example.com/v1",
            model="test-model"
        )

        text1 = "Hello"
        text2 = "world"

        prompt = analyzer._generate_semantic_analysis_prompt(text1, text2, 'en')

        assert "你是专业的文本语义分析专家" in prompt
        assert "块1: \"Hello\"" in prompt
        assert "块2: \"world\"" in prompt
        assert "分析标准" in prompt
        assert "重要输出要求" in prompt
        assert "merge" in prompt

    def test_generate_batch_semantic_analysis_prompt(self):
        """测试批量语义分析提示词生成"""
        analyzer = SemanticAnalyzer(
            api_key="test_key",
            api_url="https://test-api.example.com/v1",
            model="test-model"
        )

        text_pairs = [
            ("Hello", "world"),
            ("How are", "you")
        ]

        prompt = analyzer._generate_batch_semantic_analysis_prompt(text_pairs, 'en')

        assert "你是专业的文本语义分析专家" in prompt
        assert "对1:" in prompt
        assert "块1: \"Hello\"" in prompt
        assert "块2: \"world\"" in prompt
        assert "对2:" in prompt
        assert "块1: \"How are\"" in prompt
        assert "块2: \"you\"" in prompt
        assert "分析标准" in prompt
        assert "重要输出要求" in prompt

    def test_supported_languages(self):
        """测试支持的语言"""
        analyzer = SemanticAnalyzer(
            api_key="test_key",
            api_url="https://test-api.example.com/v1",
            model="test-model"
        )

        assert 'zh' in analyzer.supported_languages
        assert 'en' in analyzer.supported_languages
        assert 'ja' in analyzer.supported_languages
        assert analyzer.supported_languages['zh'] == '中文'
        assert analyzer.supported_languages['en'] == '英语'

    def test_max_tokens_defaults(self):
        """测试默认max_tokens设置"""
        analyzer = SemanticAnalyzer(
            api_key="test_key",
            api_url="https://test-api.example.com/v1",
            model="test-model"
        )

        assert analyzer.max_tokens == 1024
        assert analyzer.batch_max_tokens == 2048


if __name__ == "__main__":
    pytest.main([__file__])
