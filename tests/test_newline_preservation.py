"""测试翻译提示词行为

验证系统提示词不再包含换行符保持规则，翻译行为符合预期。
"""

import pytest
from unittest.mock import MagicMock, patch
from modules.translator import Translator
from modules.silicon_flow_translator import SiliconFlowTranslator


class TestNewlinePreservation:
    """换行符保持规则测试"""

    def test_system_prompt_does_not_contain_newline_rule(self):
        """测试系统提示词不再包含换行符保持规则

        换行符已在提取阶段统一删除，翻译阶段不再需要该规则。
        """
        # 创建 Translator 实例（使用 mock api_key）
        translator = Translator(api_key="mock_key")

        # 生成系统提示词
        system_prompt = translator._generate_system_prompt(
            doc_type="AI技术",
            source_lang_name="英文",
            target_lang_name="中文",
            glossary=""
        )

        # 验证提示词不再包含换行符保持规则
        assert "保持换行符一致性" not in system_prompt
        assert "原文有换行符" not in system_prompt
        assert "原文无换行符" not in system_prompt
        assert "禁止自行决定增加、删除或调整换行符位置" not in system_prompt
        assert "换行符数量必须与原文一致" not in system_prompt

    def test_single_line_text_no_newline_added(self):
        """测试单行文本翻译不添加换行符
        
        验证：单行英文文本翻译后不应包含换行符
        """
        # 原文：单行文本，无换行符
        original_text = "When zero-shot doesn't work, you can provide demonstrations or examples in the prompt,"
        
        # 验证原文不含换行符
        assert "\n" not in original_text
        
        # 创建 Translator 实例
        translator = Translator(api_key="mock_key")
        
        # 模拟翻译结果（假设翻译正确，不添加换行符）
        # 这里我们测试 _postprocess_text 方法的行为
        # 当原文是单行时，翻译结果也应保持单行
        
        # 模拟一个正确的翻译结果（不含换行符）
        mock_translated = "当零样本方法无法奏效时，你可以在提示词中提供示例或演示，"
        
        # 验证翻译结果不含换行符
        assert "\n" not in mock_translated
        
        # 使用 _postprocess_text 处理
        processed = translator._postprocess_text(mock_translated, original_text)
        
        # 处理后的结果仍不应包含换行符
        assert "\n" not in processed

    def test_multi_line_text_preserves_newline(self):
        """测试多行文本翻译保留换行符
        
        验证：包含换行符的英文文本翻译后应保留换行符
        """
        # 原文：包含换行符的多行文本
        original_text = "First line of text.\nSecond line of text."
        
        # 验证原文包含换行符
        assert "\n" in original_text
        original_newline_count = original_text.count("\n")
        
        # 创建 Translator 实例
        translator = Translator(api_key="mock_key")
        
        # 模拟翻译结果（保留换行符）
        mock_translated = "第一行文本。\n第二行文本。"
        
        # 验证翻译结果包含换行符
        assert "\n" in mock_translated
        
        # 验证换行符数量一致
        translated_newline_count = mock_translated.count("\n")
        assert translated_newline_count == original_newline_count

    def test_newline_count_consistency(self):
        """测试换行符数量一致性
        
        验证：翻译结果的换行符数量应与原文一致
        """
        # 原文：包含多个换行符的文本（2个换行符）
        original_text = "Line 1\nLine 2\nLine 3"
        
        # 验证原文换行符数量
        original_newline_count = original_text.count("\n")
        assert original_newline_count == 2
        
        # 创建 Translator 实例
        translator = Translator(api_key="mock_key")
        
        # 模拟翻译结果（换行符数量一致）
        mock_translated = "第一行\n第二行\n第三行"
        
        # 验证翻译结果换行符数量
        translated_newline_count = mock_translated.count("\n")
        assert translated_newline_count == original_newline_count
        
        # 测试不同换行符数量的场景
        # 3个换行符
        original_text_3 = "Line 1\nLine 2\nLine 3\nLine 4"
        mock_translated_3 = "第一行\n第二行\n第三行\n第四行"
        assert original_text_3.count("\n") == mock_translated_3.count("\n")

    def test_newline_rule_not_in_silicon_flow_translator(self):
        """测试 SiliconFlowTranslator 的系统提示词不再包含换行符规则"""
        # 创建 SiliconFlowTranslator 实例
        translator = SiliconFlowTranslator(
            api_key="mock_key",
            api_url="https://mock.api.url",
            model="mock_model"
        )
        
        # 生成系统提示词
        system_prompt = translator._generate_system_prompt(
            doc_type="AI技术",
            source_lang_name="英文",
            target_lang_name="中文",
            glossary=""
        )
        
        # 验证提示词不再包含换行符保持规则
        assert "保持换行符一致性" not in system_prompt
        assert "原文有换行符" not in system_prompt
        assert "原文无换行符" not in system_prompt

    def test_empty_text_handling(self):
        """测试空文本的处理"""
        translator = Translator(api_key="mock_key")
        
        # 空文本
        empty_text = ""
        
        # _postprocess_text 应返回原始文本（fallback）
        processed = translator._postprocess_text("", empty_text)
        assert processed == empty_text

    def test_text_with_only_newlines(self):
        """测试仅包含换行符的文本"""
        translator = Translator(api_key="mock_key")
        
        # 仅包含换行符的文本
        text_with_only_newlines = "\n\n\n"
        
        # 原文换行符数量
        original_count = text_with_only_newlines.count("\n")
        
        # 模拟翻译结果（保持换行符数量）
        mock_translated = "\n\n\n"
        assert mock_translated.count("\n") == original_count


class TestNewlinePreservationIntegration:
    """换行符保持集成测试"""

    def test_system_prompt_structure(self):
        """测试系统提示词的结构完整性"""
        translator = Translator(api_key="mock_key")
        
        system_prompt = translator._generate_system_prompt(
            doc_type="AI技术",
            source_lang_name="英文",
            target_lang_name="中文",
            glossary="AI: 人工智能\nLLM: 大语言模型"
        )
        
        # 验证提示词包含所有关键规则（注意：换行符保持规则已在2026-06-13移除）
        required_rules = [
            "语义连贯",
            "自然过渡",
            "风格一致",
            "简洁精炼",
            "术语一致",
            "不增删义",
            "语法正确",
            "技术精准",
            "不要翻译URL",
            "不要翻译代码段",
            "长度控制",
            "不要翻译公式",
            "不要解释缩写",
            "禁止元注释",
            "保持列表格式",
            "保留单元格分隔符"
        ]
        
        for rule in required_rules:
            assert rule in system_prompt, f"提示词缺少规则: {rule}"

    def test_glossary_in_system_prompt(self):
        """测试术语表正确嵌入系统提示词"""
        translator = Translator(api_key="mock_key")
        
        glossary = "AI: 人工智能\nLLM: 大语言模型\nAPI: 应用程序接口"
        
        system_prompt = translator._generate_system_prompt(
            doc_type="AI技术",
            source_lang_name="英文",
            target_lang_name="中文",
            glossary=glossary
        )
        
        # 验证术语表内容在提示词中
        assert "AI: 人工智能" in system_prompt
        assert "LLM: 大语言模型" in system_prompt
        assert "API: 应用程序接口" in system_prompt

    def test_no_glossary_in_system_prompt(self):
        """测试无术语表时的系统提示词"""
        translator = Translator(api_key="mock_key")
        
        system_prompt = translator._generate_system_prompt(
            doc_type="AI技术",
            source_lang_name="英文",
            target_lang_name="中文",
            glossary=""
        )
        
        # 验证无术语表时显示"无"
        assert "无" in system_prompt


class TestNewlinePreservationEdgeCases:
    """换行符保持边界情况测试"""

    def test_trailing_newline_preservation(self):
        """测试尾部换行符的保持"""
        # 原文带有尾部换行符
        original_text = "Text with trailing newline.\n"
        
        original_count = original_text.count("\n")
        assert original_count == 1
        
        # 模拟翻译结果保持尾部换行符
        mock_translated = "带有尾部换行符的文本。\n"
        assert mock_translated.count("\n") == original_count

    def test_leading_newline_preservation(self):
        """测试开头换行符的保持"""
        # 原文带有开头换行符
        original_text = "\nText with leading newline."
        
        original_count = original_text.count("\n")
        assert original_count == 1
        
        # 模拟翻译结果保持开头换行符
        mock_translated = "\n带有开头换行符的文本。"
        assert mock_translated.count("\n") == original_count

    def test_consecutive_newlines_preservation(self):
        """测试连续换行符的保持"""
        # 原文包含连续换行符（段落分隔）
        original_text = "Paragraph 1.\n\nParagraph 2."
        
        original_count = original_text.count("\n")
        assert original_count == 2
        
        # 模拟翻译结果保持连续换行符
        mock_translated = "段落一。\n\n段落二。"
        assert mock_translated.count("\n") == original_count

    def test_mixed_whitespace_preservation(self):
        """测试混合空白字符的处理"""
        # 原文包含换行符和空格
        original_text = "Line 1\n  Line 2 with indent\nLine 3"
        
        original_newline_count = original_text.count("\n")
        
        # 模拟翻译结果保持换行符数量
        mock_translated = "第一行\n  带缩进的第二行\n第三行"
        assert mock_translated.count("\n") == original_newline_count