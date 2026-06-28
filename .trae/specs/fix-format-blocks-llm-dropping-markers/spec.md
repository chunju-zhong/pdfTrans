# 修复 format_blocks 中 LLM 丢失 ---块N--- 标记 Spec

## Why

最新重构把 `cleanup_blocks`（接收 `(原文, 译文)` 对）改为 `format_blocks`（只接收译文列表）并简化了 `_FORMAT_SYSTEM_PROMPT` 后，几乎每页都触发整页回退：

```
WARNING - _parse_format_result: LLM返回结果缺少 ---块N--- 标记，回退到原文
WARNING - format_blocks: LLM返回了1个块（期望3个），回退到原文
WARNING - format_blocks: LLM返回了1个块（期望4个），回退到原文
```

后果：即使 LLM 正确排版了 3 个块的文本（只是没输出标记），`_parse_format_result` 也会因为缺标记返回 `["fallback_invalid_format"]`（长度 1），计数校验失败 → **整页所有块都回退到原文**，format_blocks 形同虚设。

### 根因（已定位）

`_FORMAT_SYSTEM_PROMPT`（[modules/translator.py:8-19](file:///Users/chunju/work/pdfTrans/modules/translator.py)）与输入构造（[modules/translator.py:160](file:///Users/chunju/work/pdfTrans/modules/translator.py)）存在多处设计缺陷，共同导致 LLM 丢弃 `---块N---` 标记：

1. **输入/输出格式不一致**：输入块用 `f"--- 块{i+1} ---\n{text}\n\n"`（`--- 块N ---`，带空格），但 prompt 要求输出 `用 ---块N--- 标记`（无空格）。LLM 看到的输入格式与被告知的输出格式不一致 → 困惑，倾向按输入"带空格"格式输出或干脆不输出。
2. **指令自相矛盾**：prompt 同时说"不要输出任何解释、元标记或格式标记"和"（除了规定的 ---块N--- 标记）"。LLM 容易把 `---块N---` 也归入"应避免的格式标记"，主导指令"不输出格式标记"压倒弱化的例外子句。
3. **输入标记被当脚手架剥离**：LLM 把输入里的 `--- 块N ---` 头当作输入脚手架（类似旧 `cleanup_blocks` 的 `原文:`/`译文:` 标签），而非需要回显的结构，排版时直接剥掉只留正文。
4. **缺具体输出示例**：prompt 只用一句话要求"用 ---块N--- 标记"，没有给出期望输出的 few-shot 样例。LLM 对 prose 格式指令的遵循度远低于对样例的模仿。
5. **任务措辞宽泛诱导改写**："格式排版优化"+"不新增内容、不修改正确的文本"组合下，LLM 倾向把 `---块N---` 当作"非正文内容"清理掉，以"不新增内容"为由省略标记。

### 与流式改造无关

`fix-format-blocks-timeout-retry` 把 `stream=False` 改为 `stream=True` 只改变 token 传输方式，不改变 LLM 生成内容。流式累积 `delta.content` 后得到的 `result_text` 与非流式 `response.choices[0].message.content` 完全等价。标记丢失是 prompt 设计缺陷，与流式无关。

### 解析器放大失败

`_parse_format_result`（[modules/translator.py:226-231](file:///Users/chunju/work/pdfTrans/modules/translator.py)）在缺标记时返回 `["fallback_invalid_format"]`（长度 1），必然触发 `format_blocks` 的计数校验（1 != N）→ 整页回退。即使 LLM 内容正确（只是漏标记），也全部丢弃，是严格的"全或无"失败模式。

## What Changes

- **统一标记格式**：输入构造与 prompt 指令使用**完全相同**的标记格式 `---块N---`（无空格），消除输入/输出不一致。
- **消除指令矛盾**：重写 prompt，把"输出 ---块N--- 标记"从"例外子句"提升为**首要、显式的硬性输出要求**；删除"不要输出格式标记"这种易与标记要求冲突的笼统措辞，改为精确的"不要输出解释、注释、备注"。
- **增加 few-shot 输出示例**：在 prompt 中给出一个具体的输入→输出样例，明确示范"输入的 `---块N---` 标记必须在输出中按相同位置回显"，让 LLM 通过模仿而非理解 prose 来遵循格式。
- **明确输入标记语义**：在 user prompt 中告知 LLM"输入中的 `---块N---` 标记是结构分隔符，输出时必须为每个块保留对应标记"，消除"脚手架被剥离"的歧义。
- **解析器增加行级回退**（防御纵深）：当 `---块N---` 标记完全缺失时，尝试按非空行分割作为回退（恢复旧 `_parse_cleanup_result` 的行级回退策略），避免一处缺标记导致整页回退。仅当行级回退后数量仍不匹配时才回退原文。
- 不改动 `format_blocks` 的流式调用逻辑（由 `fix-format-blocks-timeout-retry` spec 负责，保持不变）。
- 不改动 `_generate_system_prompt`（翻译主流程提示词，由 `fix-format-prompt-toc-line-collapse` spec 负责）。
- 不改动 `services/translation_content.py` 的调用方逻辑。

## Impact

- Affected specs:
  - 与 `fix-format-blocks-timeout-retry` 互补（前者修超时传输，本次修 prompt 与解析器鲁棒性）
  - 与 `fix-format-prompt-toc-line-collapse` 互补（前者修翻译主流程换行保留，本次修 format_blocks 标记保留）
- Affected code:
  - [modules/translator.py](file:///Users/chunju/work/pdfTrans/modules/translator.py) — `_FORMAT_SYSTEM_PROMPT` 常量、`format_blocks` 的输入构造与 user prompt、`_parse_format_result` 的缺标记回退分支
- 不影响翻译主流程、OCR、PDF 生成、子类（AipingTranslator / QianfanTranslator / SiliconFlowTranslator 继承同一基类，无需各自改动）。
- 不改变 `format_blocks` 的函数签名、返回值结构、流式调用方式、计数校验位置；仅改变 prompt 文本、输入标记格式、解析器缺标记分支的回退策略。

## ADDED Requirements

### Requirement: format_blocks 输入与输出标记格式统一

`format_blocks` 构造输入块时 SHALL 使用与 prompt 指示完全相同的 `---块N---` 格式（`---` + `块` + 数字 + `---`，无额外空格），消除输入与输出格式不一致导致的 LLM 困惑。

#### Scenario: 输入块标记与 prompt 指示一致
- **WHEN** `format_blocks` 构造输入文本时
- **THEN** 每个块以 `---块N---` 开头（N 从 1 开始，无空格）
- **AND** 与 `_FORMAT_SYSTEM_PROMPT` 中指示的输出标记格式字符完全相同

### Requirement: format_blocks prompt 显式要求回显标记

`_FORMAT_SYSTEM_PROMPT` SHALL 把"输出每个块前必须以 `---块N---` 标记开头"作为首要、显式的输出格式要求，而非以"例外子句"形式附在"不要输出格式标记"之后。prompt SHALL 不再使用"不要输出任何格式标记"这类与标记要求冲突的笼统措辞，改为精确的"不要输出解释、注释、备注、思考过程"。

#### Scenario: prompt 不再包含矛盾措辞
- **WHEN** 检查 `_FORMAT_SYSTEM_PROMPT` 文本
- **THEN** 不出现"不要输出...格式标记...（除了 ---块N---）"这类自相矛盾的措辞
- **AND** "输出每个块前必须以 `---块N---` 标记开头"作为独立、显式、靠前的输出格式要求出现

### Requirement: format_blocks prompt 包含 few-shot 输出示例

`_FORMAT_SYSTEM_PROMPT` 或 user prompt SHALL 包含一个具体的输入→输出样例，明确示范"输入的 `---块N---` 标记在输出中按相同位置回显，正文内容可被排版优化但标记不变"。

#### Scenario: prompt 含具体输出样例
- **WHEN** 检查 prompt 内容
- **THEN** 存在至少一个 few-shot 样例展示 `---块N---` 标记在输出中的正确位置
- **AND** 样例明确示意标记是必须回显的结构分隔符，而非可剥离的脚手架

### Requirement: format_blocks user prompt 明确输入标记语义

`format_blocks` 构造的 user prompt SHALL 显式告知 LLM"输入中的 `---块N---` 标记是结构分隔符，输出时必须为每个块保留对应编号的标记，不得剥离"。

#### Scenario: user prompt 解释输入标记
- **WHEN** `format_blocks` 生成 user prompt
- **THEN** user prompt 包含对输入 `---块N---` 标记语义的明确说明（结构分隔符，需保留）
- **AND** 不再将输入标记呈现为可能被当作脚手架剥离的格式

### Requirement: _parse_format_result 缺标记时行级回退

`_parse_format_result` 在 `---块N---` 标记完全缺失时 SHALL 尝试按非空行分割作为回退解析策略，仅当行级回退后块数量仍与期望不符时才触发回退原文。不再因单处缺标记导致整页所有块回退。

#### Scenario: 缺标记但内容分行正确
- **WHEN** LLM 返回结果不含 `---块N---` 标记，但包含 N 行非空内容（与期望块数一致）
- **THEN** `_parse_format_result` 按非空行分割返回 N 个块
- **AND** 不输出"缺少 ---块N--- 标记"警告
- **AND** `format_blocks` 接受该结果，不触发整页回退

#### Scenario: 缺标记且行数也不匹配
- **WHEN** LLM 返回结果不含 `---块N---` 标记，且按非空行分割后行数与期望块数不一致
- **THEN** `_parse_format_result` 输出警告并返回长度 1 的回退标记列表
- **AND** `format_blocks` 触发计数校验失败，回退到原文（与现状一致）

## MODIFIED Requirements

### Requirement: _FORMAT_SYSTEM_PROMPT 排版规则

`_FORMAT_SYSTEM_PROMPT`（[modules/translator.py:8-19](file:///Users/chunju/work/pdfTrans/modules/translator.py)）修改：

1. **输出格式要求提前并强化**：把"输出每个块前必须以 `---块N---` 标记开头"作为靠前的、独立的硬性要求，不再以"（除了规定的 ---块N--- 标记）"例外子句形式附在"不要输出格式标记"之后。
2. **删除矛盾措辞**：移除"不要输出任何解释、元标记或格式标记"中"格式标记"一词，改为"不要输出解释、注释、备注、思考过程"，避免与标记要求冲突。
3. **新增 few-shot 样例**：在输出格式说明后追加一个简短的输入→输出样例，展示 `---块N---` 标记在输出中的正确位置。
4. **保留**：核心原则（只做格式排版优化、不新增内容、不修改正确文本、空块输出空字符串、不确定时保持不变）语义不变，仅调整措辞顺序与强度。

### Requirement: format_blocks 输入构造与 user prompt

`format_blocks`（[modules/translator.py:159-163](file:///Users/chunju/work/pdfTrans/modules/translator.py)）修改：

1. 输入块标记格式从 `f"--- 块{i+1} ---\n{text}\n\n"` 改为 `f"---块{i+1}---\n{text}\n\n"`（移除 `块` 与数字两侧空格），与 prompt 指示的输出格式完全一致。
2. user prompt 增加对输入 `---块N---` 标记语义的说明："输入中的 `---块N---` 标记是结构分隔符，输出时必须为每个块保留对应编号的标记"。

### Requirement: _parse_format_result 缺标记回退分支

`_parse_format_result`（[modules/translator.py:226-231](file:///Users/chunju/work/pdfTrans/modules/translator.py)）修改：

- 现状：`len(parts) < 3`（缺标记）时直接返回 `["fallback_invalid_format"]`。
- 修改为：缺标记时先尝试按非空行分割 `result_text`，取前 `expected_count` 行作为回退结果；仅当行级回退后数量与 `expected_count` 不符时才返回 `["fallback_invalid_format"]` 触发整页回退。

## REMOVED Requirements

无删除项。`format_blocks` 流式调用、计数校验、异常回退、`_get_format_api_kwargs` 钩子、子类继承语义均保持不变。
