# 修复 LLM OCR 藏文惩罚参数回归 Spec

## Why

上一次 `fix-llm-ocr-repetition-overshoot` spec 为了抑制藏文 OCR 的重复输出问题，引入了 `frequency_penalty=0.3`、`presence_penalty=0.2`、`temperature=0.3`，并修改了 `DEEPSEEK_OCR_PROMPT` 加入防重复提示语。这些修改在 6-10 页藏文 PDF 上造成了严重的回归：

- **第 6 页**：模型回显改写后的 prompt 指令 "If the text is not visible, do not output. Output length must match the visible text amount..."（completion=345 tokens，无任何藏文）
- **第 7 页**：模型输出为空（completion=1 token），解析失败，页面无任何文本块
- **第 8 页**：模型产生真实藏文但伴随幻觉重复 "པོའི" 数十次（completion=477 tokens）
- **第 9 页**：模型精确回显 prompt 原文 "Only transcribe text actually visible in the image. Do not repeat the same phrase..."（completion=28 tokens，无任何藏文）
- **第 10 页**：模型产生真实藏文 + 幻觉序列 "6.5.7.8.9.10.11..."（completion=365 tokens）

**根本原因**：
1. `frequency_penalty=0.3` 对 OCR/转录任务不适用。OCR 要求逐字转录源文本，而藏文宗教文本本身就含有大量合法重复（语法粒子 "པོའི"、咒语、目录编号等）。惩罚机制阻止模型生成已出现的 token，迫使模型回退到回显 prompt 指令（prompt 内容不被惩罚）或产生空响应/幻觉内容。
2. `presence_penalty=0.2` 同样鼓励"话题切换"，与转录任务的逐字一致性要求冲突。
3. `temperature=0.3`（从 0.1 提升）引入随机性，加剧了模型从严格转录漂移到回显 prompt 的行为。
4. `DEEPSEEK_OCR_PROMPT` 新增的英文短语（"Only transcribe text actually visible in the image"、"Do not repeat the same phrase"、"Output length must match the visible text amount"）被模型当作"可安全生成的内容"回显——当 frequency_penalty 阻止其生成藏文时，prompt 文本成为模型唯一能产出的内容。

**与上一 spec 的关系**：`fix-llm-ocr-repetition-overshoot` 试图通过模型参数从源头抑制重复，但选错了工具。该 spec 自己也承认"后处理去重逻辑不在本次 spec 范围内，留待后续独立 spec 处理"。正确做法是：OCR 阶段保持忠实转录（零惩罚、低温度），重复问题通过后处理去重解决。

## What Changes

- 将 `OCR_LLM_FREQUENCY_PENALTY` 默认值从 `0.3` 改为 `0.0`（关闭频率惩罚）
- 将 `OCR_LLM_PRESENCE_PENALTY` 默认值从 `0.2` 改为 `0.0`（关闭存在惩罚）
- 将 `OCR_LLM_TEMPERATURE` 默认值从 `0.3` 恢复为 `0.1`（低温度适合确定性转录）
- 将 `OCR_LLM_MAX_TOKENS` 默认值从 `4096` 恢复为 `8000`（恢复原值，避免长页面被截断）
- 简化 `DEEPSEEK_OCR_PROMPT`，移除被模型回显的英文短语，恢复为 DeepSeek-OCR 原生简洁格式
- **为 DeepSeek-OCR 模式加载并追加 `lang_hint`**（语言专项提示）：当前 `lang_hint` 仅在 VLM（非 DeepSeek）分支生效，DeepSeek-OCR 分支使用固定的 `DEEPSEEK_OCR_PROMPT` 完全忽略语言专项规则。本 spec 将 `lang_hint` 加载逻辑提取为共享代码，DeepSeek-OCR 模式也根据 `source_lang` 加载 `prompts/language_rules/` 中的 OCR 规则并追加到 prompt 末尾，使藏文 OCR 获得 bbox 行宽、易混淆字形、藏文数字、藏文标点等专项指导
- 同步更新 `.env.example` 注释与默认值
- 同步更新 `prompts/language_rules/bo_to_zh.py` 的 OCR 规则，移除"不要重复"相关条目（这些条目可能被模型当作内容回显）

## Impact

- Affected specs:
  - `fix-llm-ocr-repetition-overshoot` — 本 spec 部分回滚该 spec 的参数修改（penalty、temperature、max_tokens、prompt）。该 spec 描述的重复问题需要后续通过后处理去重独立 spec 解决
  - `fix-llm-ocr-tibetan-recognition` — 该 spec 修复藏文识别（注入源语言信息），与本 spec 正交
  - `diagnose-glm4v-tibetan-retry` — 该 spec 修复超时（120s→300s），与本 spec 正交
- Affected code:
  - `config.py` — 修改 `OCR_LLM_FREQUENCY_PENALTY`、`OCR_LLM_PRESENCE_PENALTY`、`OCR_LLM_TEMPERATURE`、`OCR_LLM_MAX_TOKENS` 默认值
  - `modules/ocr/llm_extractor.py` — 简化 `DEEPSEEK_OCR_PROMPT` 常量；将 `lang_hint` 加载逻辑提取为共享代码（私有方法 `_build_lang_hint`），DeepSeek-OCR 与 VLM 两个分支都调用该方法获取语言专项提示并追加到 user 消息文本末尾
  - `.env.example` — 同步注释与默认值
  - `prompts/language_rules/bo_to_zh.py` — 移除 OCR 规则中的防重复条目（保留第 1-5 条，这些条目将通过新增的 `lang_hint` 注入机制在 DeepSeek-OCR 模式下生效）

## ADDED Requirements

### Requirement: LLM OCR 默认关闭频率惩罚与存在惩罚

`config.OCR_LLM_FREQUENCY_PENALTY` 默认值 SHALL 为 `0.0`，`config.OCR_LLM_PRESENCE_PENALTY` 默认值 SHALL 为 `0.0`。OCR 是转录任务，需要逐字忠实输出源文本内容，不应惩罚合法的 token 重复。

#### Scenario: 默认参数下藏文 OCR 正常转录
- **WHEN** 用户未设置 `OCR_LLM_FREQUENCY_PENALTY` 和 `OCR_LLM_PRESENCE_PENALTY` 环境变量
- **AND** 使用 DeepSeek-OCR 模型对藏文页面进行 OCR
- **THEN** `chat.completions.create` 调用包含 `frequency_penalty=0.0`、`presence_penalty=0.0`
- **AND** 模型能正常转录藏文中的合法重复内容（如语法粒子、咒语、目录编号）
- **AND** 模型不再回显 prompt 指令作为响应内容

#### Scenario: 用户自定义惩罚参数
- **WHEN** 用户显式设置 `OCR_LLM_FREQUENCY_PENALTY=0.5`
- **THEN** 调用使用 0.5 作为 `frequency_penalty`（用户自担风险）

### Requirement: LLM OCR 默认温度恢复为 0.1

`config.OCR_LLM_TEMPERATURE` 默认值 SHALL 为 `0.1`。OCR 需要确定性输出，低温度适合转录任务。

#### Scenario: 用户未配置温度
- **WHEN** 用户未设置 `OCR_LLM_TEMPERATURE` 环境变量
- **THEN** 使用默认值 `0.1`

### Requirement: LLM OCR 默认 max_tokens 恢复为 8000

`config.OCR_LLM_MAX_TOKENS` 默认值 SHALL 为 `8000`，避免长页面被截断。

#### Scenario: 用户未配置 max_tokens
- **WHEN** 用户未设置 `OCR_LLM_MAX_TOKENS` 环境变量
- **THEN** 使用默认值 `8000`

### Requirement: DeepSeek-OCR prompt 恢复为原生简洁格式

`DEEPSEEK_OCR_PROMPT` SHALL 仅包含 DeepSeek-OCR 原生指令，不包含任何可被模型回显的英文防重复/防幻觉指导短语。DeepSeek-OCR 是专门训练的 OCR 模型，不需要额外的防重复提示。

#### Scenario: DeepSeek-OCR 模型调用
- **WHEN** 使用 DeepSeek-OCR 模型
- **THEN** prompt 为 `"<image>\n<|grounding|>Convert the document to markdown."`
- **AND** prompt 不包含 "Only transcribe text actually visible in the image"
- **AND** prompt 不包含 "Do not repeat the same phrase"
- **AND** prompt 不包含 "Output length must match the visible text amount"

### Requirement: DeepSeek-OCR 模式注入语言专项提示 lang_hint

`LlmOcrExtractor._extract_page` 中 DeepSeek-OCR 分支 SHALL 与 VLM 分支共享 `lang_hint` 加载逻辑，根据 `source_lang` 从 `prompts/rule_registry` 加载 `task_type="ocr"` 的语言专项规则，并追加到 user 消息文本末尾（`DEEPSEEK_OCR_PROMPT` 之后）。

当前实现仅在 VLM 分支加载 `lang_hint`，DeepSeek-OCR 分支完全忽略语言专项规则，导致藏文 OCR 无法获得 bbox 行宽、易混淆字形、藏文数字、藏文标点等专项指导。

#### Scenario: DeepSeek-OCR 处理藏文页面
- **WHEN** 使用 DeepSeek-OCR 模型且 `source_lang="bo"`
- **THEN** user 消息文本为 `DEEPSEEK_OCR_PROMPT + lang_hint`
- **AND** `lang_hint` 包含 `prompts/language_rules/bo_to_zh.py` 中 OCR 规则的内容（bbox 行宽、易混淆字形、藏文数字、藏文标点、分隔符保留）
- **AND** `lang_hint` 包含 `prompts/language_rules/base.py` 中通用 OCR 规则的内容（逐行提取、多行不合并）

#### Scenario: DeepSeek-OCR 处理非藏文页面
- **WHEN** 使用 DeepSeek-OCR 模型且 `source_lang="en"`（或其他非藏文语言）
- **THEN** user 消息文本为 `DEEPSEEK_OCR_PROMPT + lang_hint`
- **AND** `lang_hint` 仅包含 `base.py` 中的通用 OCR 规则（无语言专项规则时 `lang_hint` 可能仅含通用规则或为空）

#### Scenario: 规则注册表加载失败
- **WHEN** `prompts.rule_registry` 导入失败（ImportError）
- **THEN** `lang_hint` 为空字符串
- **AND** user 消息文本仅为 `DEEPSEEK_OCR_PROMPT`（向后兼容）

#### Scenario: lang_hint 加载逻辑共享
- **WHEN** 审查 `LlmOcrExtractor._extract_page` 代码
- **THEN** `lang_hint` 加载逻辑被提取为私有方法（如 `_build_lang_hint`）
- **AND** DeepSeek-OCR 分支与 VLM 分支都调用该方法，不重复实现

### Requirement: 藏文 OCR 专项规则移除防重复条目

`prompts/language_rules/bo_to_zh.py` 中 `task_type="ocr"` 的规则 SHALL 移除以下条目（原第 6、7、8 条）：
- "仅识别图像中实际可见的藏文字符，不要根据上下文或已有内容编造、推断或重复输出未在图像中出现的文字"
- "不要重复输出同一短语——即使图像中确实有相似内容，每条文本应只识别一次；如发现模型开始重复同一短语，应立即停止"
- "输出长度应与图像实际文字量匹配，避免无意义的重复填充以达到 max_tokens 上限"

这些条目可能被模型当作内容回显，且对 DeepSeek-OCR 模型不生效（DeepSeek-OCR 走 `DEEPSEEK_OCR_PROMPT` 路径，不读取 `lang_hint`）。

#### Scenario: 藏文 OCR 规则不再包含防重复条目
- **WHEN** 加载 `prompts/language_rules/bo_to_zh.py` 的 OCR 规则
- **THEN** 规则内容不包含 "不要重复输出同一短语"
- **AND** 规则内容不包含 "输出长度应与图像实际文字量匹配"
- **AND** 保留原第 1-5 条（bbox 行宽、易混淆字形、藏文数字、藏文标点、分隔符保留）

## MODIFIED Requirements

### Requirement: `.env.example` 同步更新 OCR LLM 参数注释与默认值

`.env.example` 中的 OCR LLM 参数注释 SHALL 反映新的默认值，并移除"频率惩罚抑制重复"、"存在惩罚鼓励新话题"等误导性注释。

#### Scenario: 用户查看 .env.example
- **WHEN** 用户查看 `.env.example` 中的 OCR LLM 参数部分
- **THEN** 注释显示 `# OCR_LLM_MAX_TOKENS=8000`
- **AND** 注释显示 `# OCR_LLM_TEMPERATURE=0.1`
- **AND** 注释显示 `# OCR_LLM_FREQUENCY_PENALTY=0.0` 并附说明"OCR 转录任务不应使用频率惩罚"
- **AND** 注释显示 `# OCR_LLM_PRESENCE_PENALTY=0.0` 并附说明"OCR 转录任务不应使用存在惩罚"

## REMOVED Requirements

### Requirement: fix-llm-ocr-repetition-overshoot 中的频率/存在惩罚默认值

**Reason**: 该 spec 引入的 `frequency_penalty=0.3`、`presence_penalty=0.2` 导致藏文 OCR 严重回归（prompt 回显、空响应、幻觉内容）。OCR 转录任务不应使用惩罚参数。

**Migration**: 重复输出问题应通过后处理去重（独立 spec）解决，而非通过模型参数从源头抑制。用户若确实需要惩罚参数，可通过环境变量显式设置。
