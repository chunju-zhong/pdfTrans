"""测试动态 max_tokens 计算功能"""

import pytest
from modules.translator import Translator, calculate_max_tokens


class TestCalculateMaxTokensStandalone:
    """测试独立函数 calculate_max_tokens"""

    def test_short_text_returns_min_output_tokens(self):
        """短文本应返回 MIN_OUTPUT_TOKENS（256）"""
        result = calculate_max_tokens("hi", max_ceiling=8192)
        assert result == 256

    def test_empty_text_returns_min_output_tokens(self):
        """空文本应返回 MIN_OUTPUT_TOKENS"""
        result = calculate_max_tokens("", max_ceiling=8192)
        assert result == 256

    def test_medium_text_dynamic_calculation(self):
        """中等长度文本应动态计算"""
        # 300字符 / 3 chars_per_token = 100 tokens × 3 expansion = 300
        text = "a" * 300
        result = calculate_max_tokens(text, max_ceiling=8192)
        assert result == 300

    def test_result_capped_by_ceiling(self):
        """结果不应超过 max_ceiling"""
        text = "a" * 10000  # 10000/3*3=10000
        result = calculate_max_tokens(text, max_ceiling=4096)
        assert result == 4096

    def test_custom_chars_per_token(self):
        """自定义 chars_per_token"""
        text = "a" * 600  # 600/2*3=900
        result = calculate_max_tokens(text, max_ceiling=8192, chars_per_token=2)
        assert result == 900

    def test_custom_expansion_factor(self):
        """自定义 expansion_factor"""
        text = "a" * 300  # 300/3*2=200
        result = calculate_max_tokens(text, max_ceiling=8192, expansion_factor=2)
        assert result == 256  # max(256, 200) = 256

    def test_custom_min_output_tokens(self):
        """自定义 min_output_tokens"""
        text = "hi"  # 短文本
        result = calculate_max_tokens(text, max_ceiling=8192, min_output_tokens=512)
        assert result == 512


class TestTranslatorCalculateMaxTokens:
    """测试 Translator._calculate_max_tokens 实例方法"""

    def setup_method(self):
        self.translator = Translator(api_key="test_key")
        # Translator 基类没有 max_tokens 属性，需要手动设置用于测试
        self.translator.max_tokens = 8192

    def test_short_text_uses_min_output_tokens(self):
        """短文本应使用 MIN_OUTPUT_TOKENS"""
        result = self.translator._calculate_max_tokens("hi")
        assert result == 256

    def test_medium_text(self):
        """中等文本动态计算"""
        text = "a" * 300  # 100 tokens * 3 = 300
        result = self.translator._calculate_max_tokens(text)
        assert result == 300

    def test_capped_by_default_max_tokens(self):
        """默认上限为 self.max_tokens（8192）"""
        text = "a" * 100000  # 100000/3*3=100000
        result = self.translator._calculate_max_tokens(text)
        assert result == self.translator.max_tokens

    def test_custom_ceiling(self):
        """自定义上限"""
        text = "a" * 10000
        result = self.translator._calculate_max_tokens(text, max_ceiling=4096)
        assert result == 4096

    def test_constants_consistency(self):
        """常量应与独立函数默认值一致"""
        assert self.translator.CHARS_PER_TOKEN == 3
        assert self.translator.EXPANSION_FACTOR == 3
        assert self.translator.MIN_OUTPUT_TOKENS == 256


class TestCalculateMaxTokensWithTranslators:
    """测试三个翻译器子类使用动态 max_tokens"""

    def test_aiping_uses_dynamic_max_tokens(self):
        """AipingTranslator 翻译调用应使用 _calculate_max_tokens"""
        from modules.aiping_translator import AipingTranslator
        from unittest.mock import patch, MagicMock

        translator = AipingTranslator("test_key", "https://test-api.aiping.com/v1", "Qwen3-32B")

        with patch.object(translator.client.chat.completions, 'create') as mock_create:
            mock_chunk = MagicMock()
            mock_chunk.choices = [MagicMock(delta=MagicMock(content='你好'))]
            mock_create.return_value = [mock_chunk]

            translator.translate('Hello world', 'en', 'zh', doc_type="AI技术", glossary=None)

            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs['max_tokens'] != 8192
            assert call_kwargs['max_tokens'] == translator._calculate_max_tokens('Hello world')

    def test_silicon_flow_uses_dynamic_max_tokens(self):
        """SiliconFlowTranslator 翻译调用应使用 _calculate_max_tokens"""
        from modules.silicon_flow_translator import SiliconFlowTranslator
        from unittest.mock import patch, MagicMock

        translator = SiliconFlowTranslator("test_key", "https://api.siliconflow.cn/v1", "test-model")

        with patch.object(translator.client.chat.completions, 'create') as mock_create:
            mock_chunk = MagicMock()
            mock_chunk.choices = [MagicMock(delta=MagicMock(content='你好'))]
            mock_create.return_value = [mock_chunk]

            translator.translate('Hello world', 'en', 'zh', doc_type="AI技术", glossary=None)

            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs['max_tokens'] == translator._calculate_max_tokens('Hello world')

    def test_qianfan_uses_dynamic_max_tokens(self):
        """QianfanTranslator 翻译调用应使用 _calculate_max_tokens"""
        from modules.qianfan_translator import QianfanTranslator
        from unittest.mock import patch, MagicMock

        translator = QianfanTranslator("test_key", "https://qianfan.baidubce.com/v2", "ernie-4.0")

        with patch.object(translator.client.chat.completions, 'create') as mock_create:
            mock_chunk = MagicMock()
            mock_chunk.choices = [MagicMock(delta=MagicMock(content='你好'))]
            mock_create.return_value = [mock_chunk]

            translator.translate('Hello world', 'en', 'zh', doc_type="AI技术", glossary=None)

            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs['max_tokens'] == translator._calculate_max_tokens('Hello world')


if __name__ == "__main__":
    pytest.main([__file__])
