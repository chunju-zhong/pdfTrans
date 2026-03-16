# 所有 Models 类增加 Copy 支持规格文档

## Why
当前只有 `PdfTable` 和 `PdfImage` 类继承了 `CopyableMixin`，其他 models 类也需要支持 copy 功能，以保持一致性和灵活性。

## What Changes
- `models/extraction.py`: 让 `PdfPage`、`PdfCell`、`PdfExtraction` 继承 CopyableMixin
- `models/merged_block.py`: 让 `MergedBlock` 继承 CopyableMixin
- `models/text_block.py`: 让 `TextBlock` 继承 CopyableMixin
- `models/task.py`: 让 `Task` 继承 CopyableMixin
- `models/result_types.py`: 让相关类继承 CopyableMixin（可选，因为这些类比较简单）

## Impact
- Affected code:
  - `models/extraction.py`
  - `models/merged_block.py`
  - `models/text_block.py`
  - `models/task.py`
  - `models/result_types.py`

## 技术方案

### 使用 Mixin 类
所有需要 copy 功能的类都继承 `CopyableMixin`：

```python
from models.copyable import CopyableMixin

class TextBlock(CopyableMixin):
    pass

class MergedBlock(CopyableMixin):
    pass

class Task(CopyableMixin):
    pass
```

### 注意
- `phase_config.py` 只有函数，没有类，不需要修改
- `result_types.py` 中的类较简单，可以选择性添加

## ADDED Requirements

### Requirement: extraction.py 中的类
让 `PdfPage`、`PdfCell`、`PdfExtraction` 继承 CopyableMixin。

#### Scenario: PdfPage 继承 Mixin
- **GIVEN** PdfPage 类
- **WHEN** 继承 CopyableMixin
- **THEN** PdfPage 自动获得 copy() 和 deepcopy() 方法

#### Scenario: PdfCell 继承 Mixin
- **GIVEN** PdfCell 类
- **WHEN** 继承 CopyableMixin
- **THEN** PdfCell 自动获得 copy() 和 deepcopy() 方法

#### Scenario: PdfExtraction 继承 Mixin
- **GIVEN** PdfExtraction 类
- **WHEN** 继承 CopyableMixin
- **THEN** PdfExtraction 自动获得 copy() 和 deepcopy() 方法

### Requirement: text_block.py 中的类
让 `TextBlock` 继承 CopyableMixin。

#### Scenario: TextBlock 继承 Mixin
- **GIVEN** TextBlock 类
- **WHEN** 继承 CopyableMixin
- **THEN** TextBlock 自动获得 copy() 和 deepcopy() 方法

### Requirement: merged_block.py 中的类
让 `MergedBlock` 继承 CopyableMixin。

#### Scenario: MergedBlock 继承 Mixin
- **GIVEN** MergedBlock 类
- **WHEN** 继承 CopyableMixin
- **THEN** MergedBlock 自动获得 copy() 和 deepcopy() 方法

### Requirement: task.py 中的类
让 `Task` 继承 CopyableMixin。

#### Scenario: Task 继承 Mixin
- **GIVEN** Task 类
- **WHEN** 继承 CopyableMixin
- **THEN** Task 自动获得 copy() 和 deepcopy() 方法

### Requirement: result_types.py 中的类（可选）
考虑让相关类继承 CopyableMixin。

#### Scenario: 结果类继承 Mixin
- **GIVEN** 结果类（TruncationInfo, Result, OpenAIResult 等）
- **WHEN** 继承 CopyableMixin
- **THEN** 自动获得 copy() 和 deepcopy() 方法

## Acceptance Criteria

### AC-1: 所有指定类都继承 CopyableMixin
- **GIVEN** 指定的 models 类
- **WHEN** 继承 CopyableMixin
- **THEN** 所有类都自动获得 copy() 和 deepcopy() 方法

### AC-2: 向后兼容
- **GIVEN** 现有的代码使用这些类
- **WHEN** 添加 CopyableMixin 后
- **AND** 现有代码仍然正常工作
