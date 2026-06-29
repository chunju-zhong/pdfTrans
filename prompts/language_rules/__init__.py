"""
语言专项规则模块

所有语言对的规则定义文件放入此目录。每个文件定义一个或多个 PromptRule。

自动扫描机制：此 __init__.py 在导入时自动扫描同级所有 .py 文件（自身除外），
调用每个模块中的 RULES 列表（List[PromptRule]）并将其注册到全局 PromptRuleRegistry。
"""

from __future__ import annotations

import importlib
import pkgutil
import os
from typing import List

from prompts.rule_registry import PromptRule, PromptRuleRegistry
from utils.logging_config import get_logger

logger = get_logger(__name__)

# 在此 __init__.py 导入时自动注册所有语言规则模块
_loaded = False


def _auto_register_rules() -> None:
    """自动扫描并注册所有规则模块"""
    global _loaded
    if _loaded:
        return
    _loaded = True

    registry = PromptRuleRegistry.get_instance()
    package_dir = os.path.dirname(__file__)
    package_name = __name__

    for importer, modname, is_pkg in pkgutil.iter_modules([package_dir]):
        # 跳过自身和包
        if is_pkg or modname == "__init__":
            continue

        try:
            module = importlib.import_module(f"{package_name}.{modname}")
            rules: List[PromptRule] = getattr(module, "RULES", [])
            if rules:
                registry.register_rules(rules)
                logger.debug(
                    "已注册语言规则模块 '%s': %d 条规则到全局注册表（按语言对过滤后才会应用）",
                    modname, len(rules),
                )
            else:
                logger.debug("规则模块 '%s' 无 RULES 列表，跳过", modname)
        except Exception as e:
            logger.warning("加载语言规则模块 '%s' 失败: %s", modname, e)


# 模块导入时自动注册
_auto_register_rules()