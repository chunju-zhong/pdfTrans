"""
提示词规则注册表

提供 PromptRule dataclass 和 PromptRuleRegistry 单例，
用于管理按语言对和任务类型分类的 LLM 专项提示词规则。
"""

from __future__ import annotations

import os
import importlib
import pkgutil
from dataclasses import dataclass, field
from typing import List, Optional

from utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class PromptRule:
    """一条语言专项规则

    Attributes:
        task_type: 任务类型标识
            "translation" — 翻译
            "glossary"    — 术语提取
            "semantic"    — 语义分析
            "ocr"         — LLM OCR 提取
            "layout"      — Markdown 排版
            "*"           — 所有任务通用
        source_lang: 源语言代码，如 "bo"、"zh"、"en"，"*" 表示所有源语言
        target_lang: 目标语言代码，如 "zh"、"en"、"*" 表示所有目标语言
        priority: 优先级，数值越大越优先（精确匹配 > 通配匹配）
        content: 规则文本，将追加到基础提示词末尾
    """
    task_type: str
    source_lang: str
    target_lang: str
    priority: int = 100
    content: str = ""


class PromptRuleRegistry:
    """提示词规则注册表（单例）

    注册 → 匹配 → 合并 三步操作：
        1. 调用 register() 注册规则
        2. 调用 get_rules() 根据 task_type + source_lang + target_lang 匹配
        3. 调用 merge_into_prompt() 将匹配的规则追加到基础提示词
    """

    _instance: Optional["PromptRuleRegistry"] = None

    def __init__(self):
        self._rules: List[PromptRule] = []

    @staticmethod
    def get_instance() -> "PromptRuleRegistry":
        """获取规则注册表全局单例"""
        if PromptRuleRegistry._instance is None:
            PromptRuleRegistry._instance = PromptRuleRegistry()
        return PromptRuleRegistry._instance

    def register(self, rule: PromptRule) -> None:
        """注册一条规则

        Args:
            rule: PromptRule 实例
        """
        self._rules.append(rule)
        logger.debug(
            "注册规则: task_type=%s, source=%s, target=%s, priority=%d",
            rule.task_type, rule.source_lang, rule.target_lang, rule.priority,
        )

    def register_rules(self, rules: List[PromptRule]) -> None:
        """批量注册规则

        Args:
            rules: PromptRule 实例列表
        """
        for rule in rules:
            self.register(rule)

    def get_rules(
        self,
        task_type: str,
        source_lang: str,
        target_lang: str = "*",
    ) -> List[PromptRule]:
        """获取适用于指定任务和语言对的所有规则

        匹配优先级：精确匹配 > source 通配 > target 通配 > 双通配
        同优先级内按注册顺序返回。

        Args:
            task_type: 任务类型
            source_lang: 源语言代码
            target_lang: 目标语言代码（默认 "*" 表示通配）

        Returns:
            按优先级降序排列的规则列表
        """
        matched: List[PromptRule] = []

        for rule in self._rules:
            # 任务类型匹配
            if rule.task_type != task_type and rule.task_type != "*":
                continue

            # 源语言匹配
            if not self._match_lang(rule.source_lang, source_lang):
                continue

            # 目标语言匹配
            if not self._match_lang(rule.target_lang, target_lang):
                continue

            matched.append(rule)

        # 按 priority 降序排列
        matched.sort(key=lambda r: r.priority, reverse=True)
        return matched

    @staticmethod
    def _match_lang(rule_lang: str, query_lang: str) -> bool:
        """判断规则语言是否匹配查询语言

        规则语言为 "*" 时匹配任何查询值。
        规则语言与查询语言大小写不敏感比较。

        Args:
            rule_lang: 规则中指定的语言
            query_lang: 查询的语言

        Returns:
            True 表示匹配
        """
        if rule_lang == "*":
            return True
        return rule_lang.lower() == query_lang.lower()

    def merge_into_prompt(
        self,
        base_prompt: str,
        task_type: str,
        source_lang: str,
        target_lang: str = "*",
    ) -> str:
        """将匹配的规则追加到基础提示词末尾

        如果没有匹配的规则，返回原始提示词。

        Args:
            base_prompt: 基础提示词
            task_type: 任务类型
            source_lang: 源语言代码
            target_lang: 目标语言代码

        Returns:
            追加规则后的提示词
        """
        rules = self.get_rules(task_type, source_lang, target_lang)
        if not rules:
            logger.info(
                "为 task_type=%s, source=%s, target=%s 未匹配到语言专项规则，使用基础提示词",
                task_type, source_lang, target_lang,
            )
            return base_prompt

        extra_parts = []
        for rule in rules:
            extra_parts.append(rule.content)

        rule_section = "\n\n" + "\n\n".join(extra_parts)
        logger.info(
            "为 task_type=%s, source=%s, target=%s 追加了 %d 条语言专项规则",
            task_type, source_lang, target_lang, len(rules),
        )
        return base_prompt + rule_section

    def clear(self) -> None:
        """清空所有规则（主要用于测试）"""
        self._rules.clear()

    @property
    def rule_count(self) -> int:
        return len(self._rules)


# 模块级单例（懒加载，通过 get_instance() 获取）
rule_registry: PromptRuleRegistry = PromptRuleRegistry.get_instance()