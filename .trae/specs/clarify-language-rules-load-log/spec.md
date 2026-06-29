# 澄清语言规则加载日志 Spec

## Why

英译中（en→zh）翻译启动时，日志出现：

```
prompts.language_rules - INFO - 已加载语言规则模块 'base': 2 条规则
prompts.language_rules - INFO - 已加载语言规则模块 'bo_to_zh': 3 条规则
```

用户合理地误以为 `bo_to_zh`（藏文→中文）的 3 条规则被应用到了英译中翻译，但实际上这些规则只是**注册到全局规则注册表**，并未被 en→zh 翻译使用（`get_rules("translation", "en", "zh")` 会因 `source_lang="bo"` 不匹配 `"en"` 而过滤掉它们）。

**根因**：`prompts/language_rules/__init__.py` 在 import 时无条件扫描并注册所有规则模块（registry 模式的正常行为），但日志文案"已加载"没有区分"注册到注册表"与"应用到当前翻译"，造成误导。

**功能结论**：无功能 bug——`bo_to_zh` 规则不会被 en→zh 翻译使用。但日志缺乏上下文信息（未说明"加载 ≠ 应用"），且未记录实际应用到当前翻译的规则数量，导致用户无法从日志判断规则是否被正确过滤。

## What Changes

- **修改加载日志文案**：将 `language_rules/__init__.py` 中"已加载语言规则模块 '%s': %d 条规则"改为"已注册语言规则模块 '%s': %d 条规则到全局注册表（按语言对过滤后才会应用）"，明确区分"注册"与"应用"。
- **降低加载日志级别**：将模块注册日志从 INFO 降为 DEBUG——注册是启动时的内部行为，对用户无实际可见影响；INFO 级别应保留给"实际应用到当前翻译的规则"这类用户关心的信息。
- **保留应用日志**：`rule_registry.py` 的 `merge_into_prompt` 已在 INFO 级别记录"为 task_type=%s, source=%s, target=%s 追加了 %d 条语言专项规则"——这才是用户关心的"实际应用了哪些规则"的日志，保持不变。
- **新增无规则应用的 INFO 日志**：当 `merge_into_prompt` 没有匹配到任何规则时，当前直接返回 `base_prompt` 无日志。新增一条 INFO 日志记录"未匹配到语言专项规则，使用基础提示词"，让用户能从日志确认当前翻译未应用任何专项规则（如 en→zh 不会应用 bo_to_zh 规则）。

## Impact

- Affected specs: 无直接影响其他 spec
- Affected code:
  - [prompts/language_rules/__init__.py](file:///Users/chunju/work/pdfTrans/prompts/language_rules/__init__.py) — 加载日志文案与级别（line 47-50）
  - [prompts/rule_registry.py](file:///Users/chunju/work/pdfTrans/prompts/rule_registry.py) — `merge_into_prompt` 无匹配规则时新增 INFO 日志（line 165-167）
- 行为变更：仅日志输出变化，不改变任何规则加载/匹配/应用逻辑
- 风险：极低——日志级别调整可能影响依赖 INFO 级别日志的监控/调试脚本，但加载日志本身不是关键诊断信息

## ADDED Requirements

### Requirement: 语言规则注册日志应区分"注册"与"应用"

系统 SHALL 在日志中明确区分"规则注册到全局注册表"与"规则应用到当前翻译"两个概念，避免用户误以为所有注册的规则都会应用到当前翻译。

#### Scenario: en→zh 翻译启动时日志清晰
- **WHEN** 用户发起 en→zh 翻译，触发 `prompts.language_rules` 模块导入
- **THEN** 模块注册日志在 DEBUG 级别输出（如"已注册语言规则模块 'bo_to_zh': 3 条规则到全局注册表"）
- **AND** 不在 INFO 级别输出注册日志，避免与"应用"混淆

#### Scenario: en→zh 翻译应用规则时日志清晰
- **WHEN** `merge_into_prompt` 为 en→zh 翻译匹配规则
- **THEN** 在 INFO 级别输出实际应用的规则数量（如"为 task_type=translation, source=en, target=zh 追加了 1 条语言专项规则"）
- **AND** 仅 `base.py` 的通用规则（source_lang="*"）被应用，`bo_to_zh` 规则被过滤

#### Scenario: 无匹配规则时记录 INFO 日志
- **WHEN** `merge_into_prompt` 为某语言对未匹配到任何规则
- **THEN** 在 INFO 级别输出"未匹配到语言专项规则，使用基础提示词"
- **AND** 用户可从日志确认当前翻译未应用任何专项规则

## MODIFIED Requirements

### Requirement: language_rules 模块加载日志

`prompts/language_rules/__init__.py`（line 47-50）修改：

1. 现状（INFO 级别，文案模糊）：
   ```python
   logger.info(
       "已加载语言规则模块 '%s': %d 条规则",
       modname, len(rules),
   )
   ```
2. 修改为（DEBUG 级别，文案明确"注册到全局注册表"）：
   ```python
   logger.debug(
       "已注册语言规则模块 '%s': %d 条规则到全局注册表（按语言对过滤后才会应用）",
       modname, len(rules),
   )
   ```

### Requirement: merge_into_prompt 无匹配规则日志

`prompts/rule_registry.py`（line 165-167）修改：

1. 现状（无匹配时静默返回）：
   ```python
   rules = self.get_rules(task_type, source_lang, target_lang)
   if not rules:
       return base_prompt
   ```
2. 修改为（无匹配时记录 INFO 日志）：
   ```python
   rules = self.get_rules(task_type, source_lang, target_lang)
   if not rules:
       logger.info(
           "为 task_type=%s, source=%s, target=%s 未匹配到语言专项规则，使用基础提示词",
           task_type, source_lang, target_lang,
       )
       return base_prompt
   ```

## REMOVED Requirements

无删除项。
