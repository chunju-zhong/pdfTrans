# PdfTable 对象 COPY 机制规格文档

## Why
当前在 `_build_translated_tables` 方法中，创建新的 `PdfTable` 对象时，需要手动指定需要复制的属性（如 `chapter_id`、`chapter_title` 等）。这种方式不灵活，当添加新的属性时，需要手动更新复制代码。

## What Changes
- 在 `PdfTable` 类中添加 `copy()` 方法，支持自动复制所有属性
- 修改 `_build_translated_tables` 方法，使用 `copy()` 方法创建翻译后的表格对象
- 支持排除特定属性（如翻译后的内容）

## Impact
- Affected specs: 翻译服务中的表格处理
- Affected code:
  - `models/extraction.py` - PdfTable 类
  - `services/translation_service.py` - _build_translated_tables 方法

## ADDED Requirements

### Requirement: PdfTable.copy() 方法
PdfTable 类应该提供一个 `copy()` 方法，能够自动复制所有实例属性。

#### Scenario: 复制基本属性
- **GIVEN** 一个包含所有属性的 PdfTable 对象
- **WHEN** 调用 `copy()` 方法
- **THEN** 返回一个新的 PdfTable 对象，包含所有相同的属性值
- **AND** 返回的对象是一个新的实例（不是同一个对象）

#### Scenario: 复制时排除特定属性
- **GIVEN** 一个包含所有属性的 PdfTable 对象，包括需要排除的属性（如翻译后的 cells）
- **WHEN** 调用 `copy(exclude_attrs=['cells'])` 方法
- **THEN** 返回的新对象不包含被排除的属性
- **AND** 其他所有属性都被正确复制

### Requirement: _build_translated_tables 使用 copy 方法
修改 `_build_translated_tables` 方法，使用 `copy()` 方法创建翻译后的表格对象。

#### Scenario: 创建翻译后的表格
- **GIVEN** 原始表格对象 `table`，包含所有原始属性（chapter_id, chapter_title 等）
- **WHEN** 创建翻译后的表格对象
- **THEN** 使用 `table.copy(exclude_attrs=['cells'])` 创建新对象
- **AND** 然后更新 cells 属性为翻译后的内容

### Requirement: 其他数据模型的 COPY 机制（可选扩展）
考虑为其他数据模型（如 PdfImage）添加类似的 COPY 机制。

#### Scenario: PdfImage 复制
- **GIVEN** PdfImage 对象
- **WHEN** 需要创建副本时
- **THEN** 可以使用类似的 copy 机制

## MODIFIED Requirements

### Requirement: PdfTable 类增强
在 `models/extraction.py` 中修改 PdfTable 类。

#### Scenario: 添加 copy 方法
- **WHEN** 定义 PdfTable 类
- **THEN** 添加 `copy(exclude_attrs=None)` 方法
- **AND** 该方法使用 `copy.copy()` 或手动创建新对象
- **AND** 复制所有实例属性，排除指定的属性

### Requirement: translation_service.py 修改
修改 `_build_translated_tables` 方法。

#### Scenario: 使用 copy 方法
- **WHEN** 创建翻译后的表格对象
- **THEN** 使用 `translated_table = table.copy(exclude_attrs=['cells'])` 
- **AND** 然后更新 `translated_table.cells = translated_cells`

## Acceptance Criteria

### AC-1: copy 方法正确工作
- **GIVEN** 包含所有属性的 PdfTable 对象
- **WHEN** 调用 copy()
- **THEN** 返回包含所有相同属性的新对象
- **AND** 修改新对象不影响原始对象

### AC-2: 排除属性功能
- **GIVEN** 包含所有属性的 PdfTable 对象
- **WHEN** 调用 copy(exclude_attrs=['cells'])
- **THEN** 返回的新对象不包含 cells 属性
- **AND** 其他属性都被正确复制

### AC-3: 翻译服务正确使用
- **GIVEN** 原始表格对象
- **WHEN** _build_translated_tables 方法执行
- **THEN** 翻译后的表格对象包含原始的 chapter_id 等属性
- **AND** cells 属性被更新为翻译后的内容

### AC-4: 向后兼容性
- **GIVEN** 现有的代码使用 PdfTable 构造函数
- **WHEN** 添加 copy 方法后
- **THEN** 现有代码仍然正常工作
