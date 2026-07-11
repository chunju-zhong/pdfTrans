"""
藏文术语提取专项规则与提示词测试

验证内容：
1. 藏文术语提取规则（task_type="glossary", source_lang="bo", target_lang="*",
   priority=200）被正确注册到 PromptRuleRegistry 并能按语言对匹配。
2. GlossaryExtractor 在处理藏文文本时，能正确格式化术语、处理 NO_GLOSSARY，
   并在传给 LLM 的提示词中使用语言名称（"藏文"）而非语言代码（"bo"）。

依赖：
- 通过 `from prompts import rule_registry` 触发 prompts.language_rules 自动注册。
- 使用 unittest.mock.patch 模拟 openai.OpenAI 客户端，不实际调用 API。
"""

import pytest
from unittest.mock import patch, MagicMock

# 导入 prompts 包会触发 language_rules 子包的自动注册
from prompts import rule_registry  # noqa: F401
from prompts.rule_registry import PromptRuleRegistry
from modules.glossary_extractor import BaseApiGlossaryExtractor


class TestTibetanGlossaryRule:
    """验证藏文术语提取规则的注册与匹配"""

    def test_glossary_rule_registered(self):
        """规则注册表中存在 task_type="glossary", source_lang="bo" 的规则"""
        registry = PromptRuleRegistry.get_instance()
        rules = registry.get_rules("glossary", "bo", "*")
        bo_glossary_rules = [
            r for r in rules
            if r.task_type == "glossary" and r.source_lang == "bo"
        ]
        assert len(bo_glossary_rules) > 0

    def test_glossary_rule_matched_for_bo_to_zh(self):
        """get_rules("glossary", "bo", "zh") 能匹配到藏文规则"""
        registry = PromptRuleRegistry.get_instance()
        rules = registry.get_rules("glossary", "bo", "zh")
        assert len(rules) > 0
        assert any(r.source_lang == "bo" for r in rules)

    def test_glossary_rule_matched_for_bo_to_en(self):
        """get_rules("glossary", "bo", "en") 也能匹配到规则（因为 target_lang="*"）"""
        registry = PromptRuleRegistry.get_instance()
        rules = registry.get_rules("glossary", "bo", "en")
        assert len(rules) > 0
        assert any(r.source_lang == "bo" for r in rules)

    def test_glossary_rule_not_matched_for_en(self):
        """get_rules("glossary", "en", "zh") 不匹配藏文规则"""
        registry = PromptRuleRegistry.get_instance()
        rules = registry.get_rules("glossary", "en", "zh")
        assert not any(r.source_lang == "bo" for r in rules)

    def test_glossary_rule_content_contains_key_terms(self):
        """规则内容包含关键术语（གཏེར་སྟོན、རྫོགས་པ་ཆེན་པོ）"""
        registry = PromptRuleRegistry.get_instance()
        rules = registry.get_rules("glossary", "bo", "zh")
        contents = "\n".join(r.content for r in rules if r.source_lang == "bo")
        assert "གཏེར་སྟོན" in contents
        assert "རྫོགས་པ་ཆེན་པོ" in contents

    def test_merge_into_prompt_adds_rule(self):
        """merge_into_prompt 追加了藏文术语提取规则"""
        registry = PromptRuleRegistry.get_instance()
        base_prompt = "BASE_PROMPT"
        result = registry.merge_into_prompt(base_prompt, "glossary", "bo", "zh")
        assert len(result) > len(base_prompt)
        assert "藏文术语提取专项规则" in result

    def test_merge_into_prompt_no_change_for_en(self):
        """merge_into_prompt 对 en→zh 不追加任何 glossary 规则，返回原提示词"""
        registry = PromptRuleRegistry.get_instance()
        base_prompt = "BASE_PROMPT"
        result = registry.merge_into_prompt(base_prompt, "glossary", "en", "zh")
        assert result == base_prompt


class TestTibetanGlossaryExtractor:
    """使用 mock 验证术语提取器对藏文文本的处理（不实际调用 API）"""

    def _create_extractor(self):
        """创建用于测试的术语提取器实例（避免依赖具体服务商配置）"""
        return BaseApiGlossaryExtractor(
            api_key="test_key",
            api_url="https://test.api.com",
            model="test-model",
            extra_body=None,
            provider_name="test",
        )

    def test_extract_glossary_tibetan_with_terms(self):
        """mock LLM 返回藏文术语，验证 _format_glossary 正确处理"""
        extractor = self._create_extractor()
        mock_response_text = (
            "གཏེར་སྟོན: 伏藏师\n"
            "རྫོགས་པ་ཆེན་པོ: 大圆满\n"
            "ལྡེབ: 页/篇/牒"
        )

        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_response = MagicMock()
            mock_response.choices[0].message.content = mock_response_text
            mock_client.chat.completions.create.return_value = mock_response

            result = extractor.extract_glossary("测试藏文文本", "bo", "zh")

        assert isinstance(result, str)
        assert "གཏེར་སྟོན: 伏藏师" in result
        assert "རྫོགས་པ་ཆེན་པོ: 大圆满" in result
        assert "ལྡེབ: 页/篇/牒" in result

    def test_extract_glossary_tibetan_no_terms(self):
        """mock LLM 返回 NO_GLOSSARY，验证返回空字符串"""
        extractor = self._create_extractor()

        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "NO_GLOSSARY"
            mock_client.chat.completions.create.return_value = mock_response

            result = extractor.extract_glossary("测试藏文文本", "bo", "zh")

        assert result == ""

    def test_glossary_prompt_uses_lang_name(self):
        """验证传给 LLM 的 prompt 中包含"藏文"而非语言代码"bo" """
        extractor = self._create_extractor()

        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "NO_GLOSSARY"
            mock_client.chat.completions.create.return_value = mock_response

            extractor.extract_glossary("测试藏文文本", "bo", "zh")

            # 捕获传给 LLM 的 messages 参数
            call_kwargs = mock_client.chat.completions.create.call_args.kwargs
            messages = call_kwargs["messages"]

            # 提取 user message 的 content（即 prompt）
            user_messages = [m for m in messages if m["role"] == "user"]
            assert len(user_messages) > 0
            prompt_content = user_messages[0]["content"]

            # 验证 prompt 中使用语言名称"藏文"
            assert "藏文" in prompt_content
            # 验证 prompt 中不以语言代码"bo"作为源语言标识
            assert "源语言：bo" not in prompt_content


if __name__ == "__main__":
    pytest.main([__file__])
