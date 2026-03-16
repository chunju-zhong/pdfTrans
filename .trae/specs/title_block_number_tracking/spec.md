# 标题块编号记录方案 Spec

## Why

标题文本 "From Predictive AI to Autonomous Agents" 在语义合并时没有被识别为标题，并与后面的文本合并成了合并块。原因是PDF解析时标题包含换行符，导致文本匹配失败。

## What Changes

* 修改 `Chapter` 类，添加 `title_block_nos` 属性

* 修改 `_find_title_position` 方法，返回位置坐标和块编号列表

* 修改章节创建逻辑，保存标题块编号列表

* 修改章节分配逻辑，为标题块设置 `is_title_block` 属性

* 修改语义合并逻辑，直接使用 `is_title_block` 属性判断

## Impact

* Affected specs: 语义合并、章节识别

* Affected code:

  * `modules/chapter_identifier.py`

  * `utils/text_processing.py`

  * `models/text_block.py`

## ADDED Requirements

### Requirement: 标题块精确识别

在章节识别过程中，记录每个章节标题对应的文本块编号，语义合并时直接使用 `is_title_block` 属性判断。

#### Scenario: 跨块标题识别

* **WHEN** 标题跨多个文本块（如有换行符 "From Predictive AI to \n Autonomous Agents"）

* **THEN** 所有属于该标题的块都被标记为 `is_title_block = True`，正确合并

#### Scenario: 语义合并

* **WHEN** 语义合并时判断当前块是否为章节标题

* **THEN** 直接使用 `is_title_block` 属性，无需文本匹配

## MODIFIED Requirements

### Requirement: 语义合并标题判断逻辑

将基于文本匹配的标题判断改为基于 `is_title_block` 属性的判断。

## REMOVED Requirements

### Requirement: 基于文本匹配的标题判断

**Reason**: 文本匹配无法处理换行符和空格差异，导致误判
**Migration**: 使用 `is_title_block` 属性替代
