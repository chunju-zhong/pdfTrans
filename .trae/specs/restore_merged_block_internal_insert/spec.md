# 恢复合并块内部图表插入功能规格文档

## Why
2026年2月9日的重构（commit 8b63114）简化了Word和Markdown生成器的图表插入逻辑，移除了元素位于文本块内部时拆分文本并插入图表的功能。这导致当图表位置处于合并块的范围内时，图表只能插入到合并块之前或之后，无法在合并块内部精确定位。

## What Changes
- 恢复Word生成器（docx_generator.py）在合并块内部插入图表的功能
- 恢复Markdown生成器（markdown_generator.py）在合并块内部插入图表的功能
- 复用现有的 `_insert_element_in_text_block` 函数或创建对应的Markdown版本
- 支持两种生成模式：完整Markdown和按章节生成Markdown
- 采用增强的"基于合并块和原始块位置关系"方法

## Impact
- Affected specs: 图表位置处理逻辑
- Affected code:
  - `modules/docx_generator.py` - `_process_page_elements` 方法及相关方法
  - `modules/markdown_generator.py` - `_process_page_elements` 方法及相关方法

## 技术方案说明

### 两种方法对比分析

**方法1: 基于 y_position 和 block.bbox（旧的，已移除）**

原理：直接比较图表y坐标与文本块bbox范围

优点：
- 简单直接，逻辑清晰
- 不依赖合并块信息

缺点：
- 无法处理合并块情况 - 合并后只能检测到合并块，无法知道原块位置
- 当文本被合并后，原来的两个块变成一个块，无法准确判断

**方法2: 基于合并块和原始块位置关系（当前）**

原理：通过原始块定位，判断图表相对于合并块的位置

优点：
- 能处理合并块情况 - 通过原始块追踪
- 与现有合并逻辑一致

缺点：
- 当前实现只能判断"在块之前"或"在块之后"
- 当before_block和after_block属于同一合并块时（图表在合并块内部），需要增强判断

### 选择方法2并进行增强

经过分析，方法2更好但需要增强：
- 保留现有的 `_find_chart_position` 和 `_find_merged_block` 方法
- 增强判断逻辑：当 before_block 和 after_block 属于同一个合并块时，计算图表在合并块内的精确位置
- 在合并块内部时，调用拆分插入方法

## ADDED Requirements

### Requirement: 检测图表是否位于合并块内部
当通过 `_find_chart_position` 和 `_find_merged_block` 定位到图表在某个原始块之前或之后时，需要额外检查这个位置是否处于合并块的内部范围。

#### Scenario: 图表位置处于合并块内部
- **GIVEN** 图表定位到 before_block（图表之前的原始块）和 after_block（图表之后的原始块）
- **AND** before_block 和 after_block 属于同一个合并块（merged_block）
- **WHEN** 计算图表在合并块中的相对位置
- **THEN** 计算插入点比例 = (图表y坐标 - 合并块起始y坐标) / 合并块高度
- **AND** 调用 `_insert_element_in_text_block` 函数拆分合并块并插入图表

#### Scenario: 图表位置不处于合并块内部
- **GIVEN** 图表定位到 before_block 和 after_block
- **AND** before_block 和 after_block 不属于同一个合并块
- **WHEN** 处理图表插入
- **THEN** 保持现有逻辑：在找到的合并块之前或之后插入图表

### Requirement: Word生成器内部插入功能
Word生成器需要支持在合并块内部插入图表/表格。

#### Scenario: Word文档中图表位于合并块内部
- **WHEN** 处理页面元素时检测到图表需要插入到合并块内部
- **THEN** 调用 `_insert_element_in_text_block` 方法拆分合并块文本并插入图表/表格

### Requirement: Markdown生成器内部插入功能
Markdown生成器需要支持在合并块内部插入图表/表格，包括完整Markdown和按章节生成两种模式。

#### Scenario: Markdown文档中图表位于合并块内部
- **WHEN** 处理页面元素时检测到图表需要插入到合并块内部
- **THEN** 创建一个新的辅助方法 `_insert_element_in_merged_block`
- **AND** 该方法将合并块文本拆分为前后两部分
- **AND** 在适当位置插入Markdown格式的图像或表格

#### Scenario: 按章节生成Markdown时图表位于合并块内部
- **GIVEN** 章节页面内容
- **WHEN** `_process_chapter_pages` 方法处理页面元素
- **THEN** 同样应用合并块内部插入逻辑

## MODIFIED Requirements

### Requirement: _process_page_elements 方法修改
修改 docx_generator.py 和 markdown_generator.py 中的 `_process_page_elements` 方法，增加检测图表是否位于合并块内部的逻辑。

#### Scenario: 修改后的处理流程
- **WHEN** 获取到 chart_insertions 列表
- **FOR EACH** 图表插入项 (merged_block, position, chart)
- **DO**:
  1. 检查 merged_block 是否包含多个原始块
  2. 如果是，计算图表在合并块内的精确位置
  3. 如果位置在合并块范围内，调用拆分插入方法
  4. 否则使用现有逻辑（在合并块之前或之后插入）

### Requirement: _find_merged_block 方法增强
增强 `_find_merged_block` 方法，返回更多信息用于判断图表是否位于合并块内部。

#### Scenario: 增强返回值
- **GIVEN** 查找合并块的请求
- **WHEN** before_block 和 after_block 属于同一个合并块
- **THEN** 返回 `is_within_merged_block=True` 和 `insertion_ratio`
- **WHERE**:
  - `is_within_merged_block`: 图表是否位于合并块内部范围
  - `insertion_ratio`: 图表在合并块中的相对位置比例（0-1）

### 具体计算逻辑

当 before_block 和 after_block 属于同一个合并块时：
1. 获取合并块的所有原始块
2. 获取合并块起始y坐标（第一个原始块的y0）
3. 获取合并块结束y坐标（最后一个原始块的y1）
4. 计算插入点比例 = (图表y坐标 - 起始y坐标) / (结束y坐标 - 起始y坐标)

## REMOVED Requirements

### Requirement: 移除旧的内部插入检测逻辑
旧的基于 y_position 和 block.bbox 的文本块内部检测逻辑已被移除。

**Reason**: 重构后改为基于合并块和原始块的位置关系来判断
**Migration**: 使用新的基于合并块内部的检测逻辑

## 技术实现要点

### 1. 检测逻辑
- 合并块有 `original_blocks` 属性，包含多个原始块
- 每个原始块有 `block_bbox` 属性，表示其位置
- 通过比较图表y坐标和原始块bbox，确定图表相对于合并块的位置

### 2. 拆分插入方法
- `_insert_element_in_text_block` (Word版本): 已有实现
- 需要新增 Markdown 版本的方法：`_insert_element_in_merged_block`

### 3. 两种生成模式
- 完整Markdown: `_process_pages` -> `_process_page_elements`
- 按章节生成: `_process_chapter_pages` -> `_process_page_elements`

## Acceptance Criteria

### AC-1: Word生成器内部插入
- **GIVEN** 图表定位到合并块内部的原始块之间
- **WHEN** 生成Word文档
- **THEN** 图表被插入到合并块文本的适当位置，文本被拆分
- **Verification**: 检查生成的Word文档内容

### AC-2: Markdown生成器内部插入（完整模式）
- **GIVEN** 图表定位到合并块内部的原始块之间
- **WHEN** 生成完整Markdown文档
- **THEN** 图表被插入到合并块文本的适当位置，文本被拆分
- **Verification**: 检查生成的Markdown内容顺序

### AC-3: Markdown生成器内部插入（章节模式）
- **GIVEN** 章节中图表定位到合并块内部的原始块之间
- **WHEN** 按章节生成Markdown文档
- **THEN** 图表被插入到合并块文本的适当位置，文本被拆分
- **Verification**: 检查生成的章节Markdown内容顺序

### AC-4: 兼容性
- **GIVEN** 图表位于合并块外部（两个不同合并块之间）
- **WHEN** 生成文档
- **THEN** 使用现有的在合并块之前/之后插入的逻辑
- **Verification**: 现有测试用例应继续通过
