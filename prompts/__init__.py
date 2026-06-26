"""
提示词规则系统

提供语言专项规则注册表（PromptRuleRegistry），
允许根据源语言和目标语言自动为 LLM 提示词追加专项规则。

用法:
    from prompts import rule_registry

    registry = rule_registry
    rules = registry.get_rules("translation", "bo", "zh")
    # rules → list of PromptRule objects
"""

from prompts.rule_registry import PromptRule, PromptRuleRegistry, rule_registry

# 导入 language_rules 子包以触发自动注册
import prompts.language_rules  # noqa: F401

__all__ = ["PromptRule", "PromptRuleRegistry", "rule_registry"]