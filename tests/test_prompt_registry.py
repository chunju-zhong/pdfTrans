"""PromptRuleRegistry 单元测试"""

import pytest
from prompts.rule_registry import PromptRule, PromptRuleRegistry


@pytest.fixture
def registry():
    reg = PromptRuleRegistry()
    reg.clear()
    reg.register(PromptRule(
        task_type="translation", source_lang="bo", target_lang="zh",
        priority=100, content="TIBETAN_RULE",
    ))
    reg.register(PromptRule(
        task_type="translation", source_lang="*", target_lang="*",
        priority=50, content="GENERAL_RULE",
    ))
    reg.register(PromptRule(
        task_type="semantic", source_lang="bo", target_lang="*",
        priority=100, content="SEMANTIC_BO",
    ))
    reg.register(PromptRule(
        task_type="ocr", source_lang="*", target_lang="*",
        priority=50, content="OCR_GENERAL",
    ))
    return reg


class TestPromptRuleRegistry:
    def test_exact_match(self, registry):
        """精确匹配应返回高优先级规则"""
        rules = registry.get_rules("translation", "bo", "zh")
        contents = [r.content for r in rules]
        assert "TIBETAN_RULE" in contents
        assert "GENERAL_RULE" in contents
        assert rules[0].priority >= rules[-1].priority  # 按优先级降序

    def test_wildcard_source(self, registry):
        """源语言通配 * 应匹配任何查询"""
        rules = registry.get_rules("translation", "en", "zh")
        contents = [r.content for r in rules]
        assert "TIBETAN_RULE" not in contents  # bo→zh 不应匹配 en→zh
        assert "GENERAL_RULE" in contents       # *→* 应匹配

    def test_semantic_bo(self, registry):
        """语义分析的 bo→* 规则应匹配 bo→zh"""
        rules = registry.get_rules("semantic", "bo", "zh")
        assert len(rules) == 1
        assert rules[0].content == "SEMANTIC_BO"

    def test_semantic_en(self, registry):
        """语义分析 bo→* 不应匹配 en→*"""
        rules = registry.get_rules("semantic", "en", "zh")
        assert len(rules) == 0

    def test_task_type_filter(self, registry):
        """不同 task_type 不应交叉匹配"""
        trans = registry.get_rules("translation", "bo", "zh")
        ocr = registry.get_rules("ocr", "bo", "zh")
        assert any("TIBETAN_RULE" in r.content for r in trans)
        assert not any("TIBETAN_RULE" in r.content for r in ocr)

    def test_merge_into_prompt_no_rules(self, registry):
        """无匹配规则时应返回原始 prompt"""
        result = registry.merge_into_prompt("BASE", "glossary", "xx", "yy")
        assert result == "BASE"

    def test_merge_into_prompt_with_rules(self, registry):
        """有匹配规则时应追加"""
        result = registry.merge_into_prompt("BASE", "translation", "bo", "zh")
        assert result != "BASE"
        assert "TIBETAN_RULE" in result
        assert result.startswith("BASE")

    def test_priority_order(self, registry):
        """更高优先级的规则应排在前面"""
        rules = registry.get_rules("translation", "bo", "zh")
        assert len(rules) >= 2
        assert rules[0].priority >= rules[1].priority

    def test_clear(self, registry):
        """clear 后应无规则"""
        registry.clear()
        assert registry.rule_count == 0

    def test_single_instance(self):
        """get_instance 应返回单例"""
        r1 = PromptRuleRegistry.get_instance()
        r2 = PromptRuleRegistry.get_instance()
        assert r1 is r2