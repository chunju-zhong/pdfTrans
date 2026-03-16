# 数据模型 Copy 机制抽象化规格文档

## Why

当前 `PdfTable` 和 `PdfImage` 类各自实现了 `copy()` 方法，代码重复。应该将 copy 功能抽象为一个通用的机制，使所有数据模型都可以获得此功能。

## What Changes
- 创建一个独立的 `CopyableMixin` 类文件 `models/copyable.py`
- `PdfTable` 和 `PdfImage` 类继承该 Mixin
- 移除重复的 `copy()` 方法实现
- 确保所有数据模型都能使用 copy 功能

## Impact
- Affected specs: 数据模型层
- Affected code:
  - `models/copyable.py` - 新建 CopyableMixin 基类文件
  - `models/extraction.py` - 修改 PdfTable 和 PdfImage 继承 CopyableMixin
  - `models/text_block.py` - 考虑是否需要添加 copy 功能

## 技术方案

### 新建 models/copyable.py 文件
创建独立的 Mixin 类文件：

```python
# models/copyable.py
"""数据模型可复制功能 Mixin"""
import copy as copy_module


class CopyableMixin:
    """提供 copy 功能的 Mixin 类"""
    
    def copy(self, exclude_attrs=None):
        """创建对象的浅拷贝
        
        Args:
            exclude_attrs (list): 要排除的属性名列表，默认不排除任何属性
            
        Returns:
            新的对象实例
        """
        exclude_attrs = exclude_attrs or []
        
        new_obj = copy_module.copy(self)
        
        for attr in exclude_attrs:
            setattr(new_obj, attr, None)
        
        return new_obj
    
    def deepcopy(self, exclude_attrs=None):
        """创建对象的深拷贝
        
        Args:
            exclude_attrs (list): 要排除的属性名列表，默认不排除任何属性
            
        Returns:
            新的对象实例
        """
        exclude_attrs = exclude_attrs or []
        
        new_obj = copy_module.deepcopy(self)
        
        for attr in exclude_attrs:
            setattr(new_obj, attr, None)
        
        return new_obj
```

### 在 extraction.py 中导入并使用
在 extraction.py 中导入 CopyableMixin：

```python
from models.copyable import CopyableMixin


class PdfTable(CopyableMixin):
    # ... 其他代码保持不变
    pass
```

### 优势
1. **独立文件**：将 Mixin 放在单独的文件中，便于管理和维护
2. **代码复用**：避免在每个类中重复实现 copy 方法
3. **易于扩展**：新增的数据模型只需继承 Mixin 即可获得 copy 功能
4. **灵活性**：支持排除特定属性

## ADDED Requirements

### Requirement: 创建独立的 copyable.py 文件
在 models 目录下创建独立的 Mixin 类文件。

#### Scenario: 创建 CopyableMixin 文件
- **WHEN** 创建 `models/copyable.py` 文件
- **THEN** 文件包含 CopyableMixin 类
- **AND** 包含通用的 copy() 方法实现

#### Scenario: Mixin 提供 copy 功能

* **GIVEN** 继承自 CopyableMixin 的类

* **WHEN** 调用 copy() 方法

* **THEN** 返回一个新的对象实例，包含所有相同的属性值

* **AND** 支持 exclude_attrs 参数排除特定属性

#### Scenario: Mixin 提供 deepcopy 功能

* **GIVEN** 继承自 CopyableMixin 的类

* **WHEN** 调用 deepcopy() 方法

* **THEN** 返回一个新的对象实例，包含所有相同的属性值（深拷贝）

* **AND** 支持 exclude_attrs 参数排除特定属性

### Requirement: PdfTable 继承 Mixin

修改 PdfTable 类继承 CopyableMixin。

#### Scenario: PdfTable 使用 Mixin

* **GIVEN** PdfTable 类

* **WHEN** 定义类时继承 CopyableMixin

* **THEN** PdfTable 自动获得 copy() 方法

* **AND** 移除现有的重复 copy() 方法

### Requirement: PdfImage 继承 Mixin

修改 PdfImage 类继承 CopyableMixin。

#### Scenario: PdfImage 使用 Mixin

* **GIVEN** PdfImage 类

* **WHEN** 定义类时继承 CopyableMixin

* **THEN** PdfImage 自动获得 copy() 方法

* **AND** 移除现有的重复 copy() 方法

### Requirement: 其他模型扩展（可选）

考虑为其他数据模型添加 copy 功能。

#### Scenario: TextBlock 使用 Mixin

* **GIVEN** TextBlock 类

* **WHEN** 需要创建副本时

* **THEN** 可以继承 CopyableMixin 获得 copy 功能

## Acceptance Criteria

### AC-1: Mixin 正确工作

* **GIVEN** 继承 CopyableMixin 的类

* **WHEN** 调用 copy()

* **THEN** 返回包含所有相同属性的新对象

### AC-2: 排除属性功能

* **GIVEN** 继承 CopyableMixin 的类

* **WHEN** 调用 copy(exclude\_attrs=\['cells'])

* **THEN** 返回的新对象不包含被排除的属性

### AC-3: PdfTable 和 PdfImage 正常工作

* **GIVEN** PdfTable 或 PdfImage 实例

* **WHEN** 调用 copy() 方法

* **THEN** 返回正确的新实例

### AC-4: 向后兼容

* **GIVEN** 现有的代码使用 copy() 方法

* **WHEN** 使用 Mixin 后

* **AND** 现有代码仍然正常工作

