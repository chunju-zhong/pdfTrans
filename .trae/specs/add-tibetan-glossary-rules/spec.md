# 藏语术语提取支持方案 Spec

## Why

当前的藏文（bo）专项规则覆盖了 `translation`、`semantic`、`ocr` 三种任务类型，但**未覆盖 `glossary`（术语提取）**。当用户从藏文 PDF 提取术语时，术语提取提示词完全不包含藏文专项指导，完全依赖 LLM 的通用能力。

藏文术语提取场景有其特殊性：
- 藏文佛教典籍中的专业术语（如 `གཏེར་སྟོན`、`རྫོགས་པ་ཆེན་པོ`）具有高度专业性，通用提示词无法有效引导
- 藏文数字符号（`༠-༩`）在术语中可能以编号形式出现
- 藏文复合词的边界模糊，通用提示词没有针对性处理

## What Changes

1. **`prompts/language_rules/bo_to_zh.py`** — 新增 `task_type="glossary"` 的 `PromptRule`，包含：
   - 藏文佛教术语翻译对照表（复用 translation 规则中的术语表）
   - 藏文复合词提取规则
   - 藏文数字/编号处理规则
   - 术语过滤规则（区分专业术语与普通藏语词汇）
2. **`modules/glossary_extractor.py`** — （可选优化）通用提示词中使用语言名称代替语言代码，提高 LLM 理解
3. **测试** — 新增藏文术语提取测试用例

## Impact

- Affected code:
  - `prompts/language_rules/bo_to_zh.py` — 新增 glossary 规则
  - `modules/glossary_extractor.py` — 可能的提示词优化
  - `tests/` — 新增测试文件
- Affected specs: 当前已完成的 `add-tibetan-source-language` 的能力扩展

## ADDED Requirements

### Requirement: 藏文术语提取专项规则

系统 SHALL 在术语提取任务中应用藏文专项规则。

#### Scenario: 藏文→中文术语提取
- **WHEN** 用户对藏文 PDF 执行术语提取操作（源语言=bo，目标语言=zh）
- **THEN** 术语提取提示词中包含藏文专项规则
- **AND** 专项规则包含关键的藏文佛教术语翻译对照表
- **AND** 专项规则包含藏文复合词提取指导
- **AND** 专项规则包含区分专业术语与普通藏语词汇的过滤规则

#### Scenario: 藏文→英文术语提取
- **WHEN** 用户对藏文 PDF 执行术语提取（源语言=bo，目标语言=en）
- **THEN** 术语提取提示词中同样匹配藏文源语言规则（因为规则中 target_lang="*"）

#### Scenario: 非藏文术语提取不受影响
- **WHEN** 用户对其他语言（如英文→中文）执行术语提取
- **THEN** 藏文专项规则不被匹配，提示词维持原有内容

### Requirement: 术语提取准确性验证

系统 SHALL 提供验证藏文术语提取准确性的测试。

#### Scenario: 藏文佛学术语提取
- **WHEN** 给定包含藏文佛教术语的文本
- **THEN** 提取结果包含正确的术语:翻译对
- **AND** 格式严格为 `术语: 翻译` 每行一个

#### Scenario: 普通藏文文本无术语
- **WHEN** 给定不含专业术语的普通藏文文本
- **THEN** 提取结果返回空字符串或 `NO_GLOSSARY`

## MODIFIED Requirements

（无）

## REMOVED Requirements

（无）