# 重构语义合并为顺序块列表模式 Spec

## Why

当前语义合并采用"成对文本对"方式传入 LLM，多对文本中上一对的块2与下一对的块1是重复的（滑动窗口重叠），浪费了 token 且 LLM 对每对独立判断，无法参考更广上下文。改为顺序列出所有块、输出相邻块是否合并的 JSON，可以消除重复、节省 token，并让 LLM 在判断时参考前面多个块的上下文，提升合并准确性。

## What Changes

- **BREAKING** 重构 `_generate_batch_semantic_analysis_prompt`：输入从 `text_pairs: [(text1, text2), ...]` 改为 `blocks: [text1, text2, text3, ...]`，顺序列出所有块，LLM 输出 N-1 个相邻块对的合并判断
- **BREAKING** 重构 `batch_analyze_semantic_relationship`：接口从接收 `text_pairs` 改为接收 `blocks`（有序文本块列表），返回长度为 `len(blocks) - 1` 的布尔列表
- 重构 `merge_semantic_blocks_with_llm_two_phase`：构建块列表而非文本对，调用新接口
- 重构 `parallel_batch_analyze`：适配新的块列表输入
- 更新 `AipingSemanticAnalyzer.batch_analyze_semantic_relationship` 适配新接口
- 提示词中增加上下文参考指引：LLM 在判断块 i 与块 i+1 是否合并时，可参考块 i-2, i-1 等前面块的语义角色和内容

## Impact

- Affected specs: 无
- Affected code:
  - `modules/semantic_analyzer.py` — `batch_analyze_semantic_relationship`、`_generate_batch_semantic_analysis_prompt`
  - `modules/aiping_semantic_analyzer.py` — `batch_analyze_semantic_relationship`
  - `utils/text_processing.py` — `merge_semantic_blocks_with_llm_two_phase`、`parallel_batch_analyze`、`merge_semantic_blocks_with_llm`
- Affected tests: `tests/test_batch_semantic_analysis.py`、`tests/test_semantic_analyzer.py`、`tests/test_two_phase_merge.py` 等

## ADDED Requirements

### Requirement: 顺序块列表输入模式

系统 SHALL 支持以顺序块列表（而非重复的文本对）作为 LLM 语义分析的输入格式。

#### Scenario: 输入块列表并获取合并判断
- **WHEN** 调用 `batch_analyze_semantic_relationship(blocks, source_lang)`，其中 `blocks = ["块A", "块B", "块C", "块D"]`
- **THEN** LLM 收到的提示词中顺序列出所有块（块1: "块A", 块2: "块B", 块3: "块C", 块4: "块D"），LLM 返回 3 个合并判断 `{"merge": [true, false, true]}`，分别表示块1-块2、块2-块3、块3-块4 是否合并

#### Scenario: 单个块输入
- **WHEN** 调用 `batch_analyze_semantic_relationship(blocks, source_lang)`，其中 `blocks` 只有 1 个元素
- **THEN** 直接返回空列表 `[]`（无需判断合并）

### Requirement: 上下文感知合并判断

系统 SHALL 在提示词中指示 LLM 在判断块 i 与块 i+1 是否合并时，参考前面多个块的语义角色和内容上下文。

#### Scenario: 利用前文上下文判断合并
- **GIVEN** 块列表为 [签名行, 新引用正文, 引用正文续行]
- **WHEN** LLM 判断块2与块3是否合并
- **THEN** LLM 能参考块1是签名行（标志前文引用结束），从而更准确地判断块2是新引用的开始，块3是块2的续行，应合并块2-块3

#### Scenario: 段落边界上下文判断
- **GIVEN** 块列表为 [完整段落A结尾, 段落B开头, 段落B续行]
- **WHEN** LLM 判断块1-块2和块2-块3
- **THEN** LLM 能参考块1以终结标点结尾，判断块1-块2不合并；同时判断块2-块3是同一句延续应合并

### Requirement: 消除重复文本

系统 SHALL 不再在 LLM 输入中重复传入同一块文本（当前模式中上一对的块2等于下一对的块1）。

#### Scenario: 4个块不再重复
- **GIVEN** 4个文本块 A, B, C, D
- **WHEN** 构建LLM输入
- **THEN** 提示词中每个块只出现一次（当前模式：A-B, B-C, C-D 中 B、C 各出现两次；新模式：A, B, C, D 各出现一次）

### Requirement: 向后兼容的单对分析接口

系统 SHALL 保留 `analyze_semantic_relationship(text1, text2, source_lang)` 单对分析接口不变，用于单对场景的回退。

#### Scenario: 单对分析仍可用
- **WHEN** 调用 `analyze_semantic_relationship(text1, text2, source_lang)`
- **THEN** 行为与当前完全一致，返回布尔值

## MODIFIED Requirements

### Requirement: batch_analyze_semantic_relationship 接口签名

原接口：`batch_analyze_semantic_relationship(self, text_pairs, source_lang) -> list[bool]`
- `text_pairs`: 文本块对列表，每个元素是 `(text1, text2)` 元组
- 返回长度等于 `len(text_pairs)`

新接口：`batch_analyze_semantic_relationship(self, blocks, source_lang) -> list[bool]`
- `blocks`: 有序文本块列表，每个元素是字符串
- 返回长度等于 `max(0, len(blocks) - 1)`，表示每对相邻块的合并判断

### Requirement: parallel_batch_analyze 接口签名与跨批次边界处理

原接口：`parallel_batch_analyze(semantic_analyzer, text_pairs, source_lang, ...)`
新接口：`parallel_batch_analyze(semantic_analyzer, blocks, source_lang, ...)`

#### 跨批次边界问题

当块列表超过 `batch_size` 时需要分批。分批后，批次 k 的第一块与批次 k-1 的最后一块之间的合并判断归属哪个批次？

**设计方案：重叠块策略**

每个批次（除第一个外）在开头包含上一批次最后 1 个块作为"上下文重叠块"。该重叠块仅提供上下文参考，其与前一批次倒数第二块的合并判断已在上一批次中完成。本批次只需输出从重叠块开始往后的合并判断。

具体规则：
- 批次 0：块 [0, 1, 2, ..., batch_size-1]，输出 batch_size-1 个合并判断（块0-1, 块1-2, ..., 块(batch_size-2)-(batch_size-1)）
- 批次 k (k≥1)：块 [overlap_start, overlap_start+1, ..., overlap_start+batch_size]，其中 overlap_start = 上一批次最后一块的索引。输出 batch_size 个合并判断（从重叠块开始的相邻对）
- 但重叠块与上一批次倒数第二块的合并判断已在批次 k-1 中完成，因此批次 k 的结果中**第一个合并判断**（即重叠块与下一块的判断）才是新需要的

**简化方案：重叠1块，丢弃每批首个判断**

更简洁的实现：每个批次（除第一个外）多包含前一批次最后 1 个块，LLM 输出该批所有相邻对的判断，但合并结果时丢弃每批（除第一批外）的第一个判断（因为该判断与前一批次最后一个判断重复）。

#### Scenario: 20个块分2批（batch_size=10）
- **GIVEN** 20个块 [B0, B1, ..., B19]，batch_size=10
- **WHEN** 分批处理
- **THEN** 批次0：块 [B0..B9]，输出 9 个判断（B0-B1, B1-B2, ..., B8-B9）
  批次1：块 [B9..B19]（B9 为重叠块），输出 10 个判断（B9-B10, B10-B11, ..., B18-B19）
  合并时：批次0 的 9 个判断 + 批次1 的后 10 个判断（丢弃批次1首个判断 B9-B10... 不对，B9-B10 是新需要的判断）

**修正方案：重叠1块，保留每批全部判断**

重新分析：
- 批次0：块 [B0..B9]，输出 9 个判断：B0-B1, B1-B2, ..., B8-B9
- 批次1：块 [B9..B19]，输出 10 个判断：B9-B10, B10-B11, ..., B18-B19
- 合并：批次0 的 9 个 + 批次1 的 10 个 = 19 个判断 ✓（恰好等于 20-1）

重叠块 B9 在批次0中作为最后一块被分析（B8-B9 判断），在批次1中作为第一块提供上下文（B9-B10 判断）。两个判断不重复，恰好覆盖所有相邻对。

#### Scenario: 25个块分3批（batch_size=10）
- **GIVEN** 25个块 [B0..B24]，batch_size=10
- **WHEN** 分批处理
- **THEN** 批次0：块 [B0..B9]，9 个判断
  批次1：块 [B9..B18]，10 个判断
  批次2：块 [B18..B24]，7 个判断
  合并：9 + 10 + 7 = 26... 但期望 24 个判断

**问题发现**：重叠块导致多出判断。批次1的 B9-B10 和批次0的 B8-B9 不重复，但 B9-B10 是正确的。问题在于批次1的块范围是 [B9..B18] 共 10 块，输出 9 个判断（B9-B10, ..., B17-B18），不是 10 个。

重新计算：
- 批次0：块 [B0..B9]（10块），输出 9 个判断
- 批次1：块 [B9..B18]（10块），输出 9 个判断
- 批次2：块 [B18..B24]（7块），输出 6 个判断
- 合并：9 + 9 + 6 = 24 ✓

**最终规则**：每批包含前一批最后 1 个块作为重叠，N 块输出 N-1 个判断，合并时直接拼接所有批次结果即可，无需丢弃。

#### Scenario: 上下文感知在批次边界的效果
- **GIVEN** 批次0最后一块是签名行，批次1第一块（重叠块）也是该签名行
- **WHEN** 批次1判断签名行与下一块是否合并
- **THEN** LLM 能在批次1内看到签名行作为上下文，正确判断签名行后不应合并

### Requirement: merge_semantic_blocks_with_llm_two_phase 构建逻辑

原逻辑：构建 `text_pairs = [(block[i-1].text, block[i].text) for i in range(1, len(blocks))]`
新逻辑：构建 `block_texts = [block.text for block in text_blocks]`，直接传入块列表

## REMOVED Requirements

无
