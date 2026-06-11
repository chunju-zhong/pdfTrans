# 修复合并块拆分后第二个块为空导致翻译文本丢失 Spec

## Why

原文 "have taken care to not cover topics that I am not confident will stand the test of time." 的翻译在最终 PDF 输出中丢失，被截断为"我已..."。根因是 `split_translated_result()` 中 `adjust_split_position()` 将第一个块的分割点向前推进过多，消耗了全部翻译文本，导致第二个块为空。

## 根因分析

### 合并+翻译+拆分流程

1. 标题块 "What This Book Does Not Cover" 与正文块 "I have taken care to not cover topics..." 被合并为一个 MergedBlock（2个 original_blocks）
2. 合并文本被一起翻译为："本书不涉及的内容 为了使本书保持合理的篇幅，某些主题被认定超出范围。我已经确保不会涵盖那些我不确定能否经得起时间考验的主题。"
3. `split_translated_result(translation, 2 blocks)` 拆分该翻译文本

### 拆分时的错误场景

`utils/text_processing.py` 关键代码如下：

第456行：`target_len = ceil(remaining_len / remaining_blocks)`（均等分配）

第460行：`end_pos = start_pos + target_len`

第469行：`actual_end = adjust_split_position(text, end_pos)` 
→ `adjust_split_position` 最多可以向前推进 ~30 个字符（单词边界最多10 + 跳过错点最多10 + 左成对字符最多10）

**当翻译文本较短时**：如果 `actual_end >= translation_len`，则第一个块消耗了全部文本。
第531行：`start_pos = actual_end`
第535行：`if start_pos >= translation_len: break` → 第二个块永远无法执行，为空。

**空块恢复逻辑**（第543-565行）：从第一个块中间切一半给第二个块。但切分点是**任意的**（按字符长度中点），不基于内容结构。第一个块仍然保留了近一半的文本（远超其小 bbox 容量），导致 PDF 渲染时截断。

### 关键发现

1. `split_translated_result` 使用 `for i in range(num_blocks)` + 手动维护 `start_pos = actual_end`，不存在 range 迭代器的间隙问题
2. 问题是 `adjust_split_position` 的前向推进 + 均等分配的组合：均等分配给了太多文本 + 前向推进消耗了全部文本
3. 空块恢复虽然分了一些文本给第二个块，但第一个块仍然太多，超出标题 bbox 容量

## What Changes

- **修改 `split_translated_result()` 的分配策略**：在分配文本时，确保每个块至少分配其原始块文本长度比例对应的翻译文本，避免因 `adjust_split_position` 推进导致某块为空

## Impact

- Affected code: `utils/text_processing.py` 的 `split_translated_result()` 函数
- 行为变更：翻译文本分配时考虑各块的原始文本长度比例，长度相差大的块不再被均等分配
- 影响范围：所有使用语义合并的翻译流程

## ADDED Requirements

### Requirement: 按原始文本长度比例分配翻译文本

系统 SHALL 在 `split_translated_result()` 中按原始块的文本长度比例分配翻译文本。

#### Scenario: 标题+正文合并块的拆分

- **WHEN** 合并块包含一个短标题（30字符）和一个长段落（200字符）
- **AND** 翻译文本总长度为130字符
- **THEN** 标题块分到约 130 * (30/230) ≈ 17 字符
- **AND** 段落块分到约 130 * (200/230) ≈ 113 字符
- **AND** 段落块不为空

#### Scenario: 原始文本为空的块

- **WHEN** 某个原始块的文本为空
- **THEN** 该块分配最小字符数（min_characters_per_block）

### Requirement: `adjust_split_position` 调整后确保不消耗全部文本

系统 SHALL 在 `adjust_split_position` 调整分割点后，确保非最后一个块不消耗全部剩余文本。

#### Scenario: 分割点调整到文本末尾

- **WHEN** `adjust_split_position` 将分割点推进到文本末尾
- **AND** 当前块不是最后一个块
- **THEN** 限制 `actual_end = start_pos + min(target_len, translation_len - min_characters_per_block * remaining_blocks)`

## MODIFIED Requirements

（无修改的需求）

## REMOVED Requirements

（无移除的需求）
