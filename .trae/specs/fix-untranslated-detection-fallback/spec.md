# 修复未翻译文本检测和回退机制

## Why
LLM 翻译技术文档时，经常返回原文英文而不翻译（尤其是包含技术术语、代码示例、Ctrl+F 操作指引等内容的段落）。当前 `_is_translation_unchanged` 只检测"完全相同"和"含 ||| 分隔符"两种情况，无法识别"几乎相同的英文原文（仅有断字还原等微小差异）"这种未翻译场景。导致大量段落以英文原文出现在最终输出中，用户误以为是回退机制触发了，实际是 LLM 根本没有翻译。

## What Changes
- 增强 `_is_translation_unchanged` 方法，添加"高相似度未翻译"检测：当译文与原文去除空白/断字标记后的相似度超过阈值时，判定为未翻译
- 未翻译检测触发后，执行一次重试翻译（在 prompt 中强调必须翻译为目标语言），若重试仍未翻译则回退使用原文并记录 WARNING

## Impact
- Affected specs: fix-translation-garbage-output-fallback（新增另一类翻译异常场景的处理）
- Affected code: `services/translation_content.py`（`_is_translation_unchanged` 方法、`translate_merged_block` 和 `translate_original_block` 流程）

## ADDED Requirements

### Requirement: 高相似度未翻译检测
系统 SHALL 在翻译结果与原文之间进行去除断字标记（如 `Simi‐\nlarly` → `Similarly`）后的相似度比较。当相似度超过 85% 且译文不含目标语言字符时，判定为未翻译。

#### Scenario: LLM 返回断字还原后的原文
- **WHEN** LLM 对 "The average native English speaker has a vocabulary of 20,000–35,000 words. Simi‐\nlarly, every language model..." 返回 "The average native English speaker has a vocabulary of 20,000–35,000 words. Similarly, every language model..."（几乎相同，仅断字还原）
- **THEN** 系统检测到译文与原文高度相似且不含中文字符，判定为未翻译

#### Scenario: LLM 返回完全不同的中文翻译
- **WHEN** LLM 返回 "英语母语者的词汇量通常在20,000到35,000之间..."
- **THEN** 系统判定为已翻译，不做额外处理

### Requirement: 未翻译时重试翻译
系统 SHALL 在检测到未翻译结果时，执行一次重试翻译。重试时在用户消息开头追加强调指令（如"【重要】请将以下文本翻译为中文，不要返回原文："）。若重试结果仍为未翻译，则回退使用原文并记录 WARNING 日志。

#### Scenario: 重试成功翻译
- **WHEN** 首次翻译结果被判定为未翻译，系统重试翻译
- **AND** 重试返回了有效的中文翻译
- **THEN** 使用重试的翻译结果

#### Scenario: 重试仍未翻译
- **WHEN** 首次翻译结果被判定为未翻译，系统重试翻译
- **AND** 重试仍返回未翻译的英文
- **THEN** 回退使用原文，记录 WARNING 日志（含原文长度、译文长度、相似度、重试状态）

### Requirement: translate_original_block 同样集成未翻译检测和重试
系统 SHALL 在 `translate_original_block` 方法中也集成与 `translate_merged_block` 相同的未翻译检测和重试逻辑。

#### Scenario: 单个块翻译未翻译检测
- **WHEN** `translate_original_block` 中 LLM 返回未翻译结果
- **THEN** 执行重试逻辑，与合并块处理一致

## MODIFIED Requirements

### Requirement: _is_translation_unchanged 方法增强
原方法仅检测"完全相同"和"含 ||| 分隔符"两种情况。修改后新增第三种检测：

1. 去除原文和译文中的断字标记（`‐\n` 或 `-\n` 或连字符后换行）
2. 去除首尾空白后比较
3. 若去除断字后的文本相似度 > 85%（使用简单字符级比较），且译文不含目标语言字符（中文字符 \u4e00-\u9fff），则判定为未翻译
