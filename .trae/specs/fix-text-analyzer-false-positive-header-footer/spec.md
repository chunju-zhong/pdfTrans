# 修复18页文本被误判为非正文导致不翻译的问题 Spec

## Why

18页的文本（如 "has talked about three stages in the development of a"）被 OCR 正确识别为 `is_body=True`，但后续 `text_analyzer.py` 的页眉页脚检测逻辑将其误判为非正文（`is_body_text=False`），导致翻译服务跳过这些文本块。日志显示 `[13, 14, 15, 16, 17, 18, 19, 20]` 全部无正文块。

## What Changes

- **修复 `_add_similar_blocks` 的误判问题**：当 OCR 文本存在识别误差时，不同页面的不同内容可能因 LCS 相似度≥90% 被误判为页眉页脚。需要增加额外条件避免误判
- **增加最小文本长度阈值**：短文本（如 "xii | Foreword" 和 "xiv | Foreword"）的 LCS 相似度天然很高，但它们不是页眉页脚，而是页面编号
- **增加 OCR 模式下的容错**：OCR 识别的文本存在误差，相似度阈值应更严格

## Impact

- Affected code: `modules/extractors/text_analyzer.py` 的 `_add_similar_blocks` 和 `identify_header_footer` 函数
- 行为变更：页眉页脚检测更精确，减少误判

## ADDED Requirements

### Requirement: 页眉页脚检测增加最小文本长度阈值

系统 SHALL 在页眉页脚相似度检测中增加最小文本长度阈值，短文本不应仅凭相似度被标记为非正文。

#### Scenario: 短文本相似但不是页眉页脚

- **WHEN** 两个文本块长度均小于20个字符且相似度≥90%
- **THEN** 不应仅凭相似度标记为非正文，还需要满足频率条件（在≥70%的页面出现）

#### Scenario: 长文本相似且是页眉页脚

- **WHEN** 两个文本块长度均≥20个字符且相似度≥90%
- **THEN** 标记为非正文（当前行为不变）

### Requirement: OCR 模式下页眉页脚检测更严格

系统 SHALL 在 OCR 模式下使用更严格的相似度阈值，因为 OCR 文本存在识别误差。

#### Scenario: OCR 文本相似度在 90%-95% 之间

- **WHEN** OCR 提取的文本块相似度在 90%-95% 之间
- **THEN** 不应标记为非正文（可能是不同内容但有 OCR 误差）

## MODIFIED Requirements

### Requirement: _add_similar_blocks 函数

`_add_similar_blocks` SHALL 增加以下条件避免误判：
1. 两个文本块长度均≥20个字符时，才使用相似度≥90%的阈值
2. 两个文本块长度均<20个字符时，仅当文本完全相同（相似度=100%）时才标记为非正文
3. 长文本和短文本之间比较时，使用相似度≥95%的阈值

## REMOVED Requirements

（无移除的需求）

## 根因分析

### 问题：18页文本被误判为非正文

**日志证据**：
```
任务 7fc3e6b4 以下页面无正文块，可能存在内容丢失: [13, 14, 15, 16, 17, 18, 19, 20]
任务 7fc3e6b4 没有找到需要翻译的文本块
```

但 OCR 提取阶段18页有7个 `is_body=True` 的文本块。

**根因**：`text_analyzer.py` 的 `_add_similar_blocks` 函数比较顶部15%和底部15%区域的文本块，当 LCS 相似度≥90%时标记为非正文。

问题1：**短文本误判**。例如 "xii | Foreword" 和 "xiv | Foreword" 的 LCS 相似度 = LCS长度/最大长度。LCS="xi | foreword"（13字符），最大长度=14，相似度=13/14=92.9%≥90%，被误判为页眉页脚。

问题2：**OCR 误差导致不同内容相似度高**。OCR 识别的文本存在误差，不同页面的不同段落可能因 OCR 误差导致 LCS 相似度≥90%。例如 "David Liddle" 和 "DavID LiDDLe" 的 LCS 相似度很高。

问题3：**顶部/底部区域范围过大**。15%的页面高度范围可能包含正文内容，特别是在页边距较小的文档中。

**修改方案**：
1. 短文本（<20字符）仅当完全相同时才标记为非正文
2. 长短文本之间使用更严格的阈值（≥95%）
3. 长文本之间保持当前阈值（≥90%）
