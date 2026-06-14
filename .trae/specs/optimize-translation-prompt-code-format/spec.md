# 翻译提示词代码段格式化优化 Spec

## Why

当前翻译提示词（规则10）仅要求"不要翻译代码段"，但未要求对代码段进行格式化。当原文中包含代码片段时，LLM可能会改变代码段的缩进、换行和空格等格式，导致翻译后的代码段格式混乱，影响可读性和后续使用。

## What Changes

- **强化规则10**：在"不要翻译代码段"的基础上，增加代码格式化的明确要求
- **新增格式化规则**：要求LLM检测并保持代码段的正确格式化（缩进、空格、换行）
- **提供代码识别特征**：帮助LLM准确识别哪些文本属于代码段

## Impact

- Affected code: `modules/translator.py` 的 `_generate_system_prompt` 方法（第138-157行）
- 行为变更：LLM将对识别的代码段进行格式化处理
- 影响范围：所有翻译请求

## ADDED Requirements

### Requirement: 系统提示词新增代码段格式化规则

系统 SHALL 在翻译提示词中明确要求大模型对代码段进行格式化。

#### Scenario: 代码块保持缩进和换行

- **WHEN** 原文包含多行代码块（有缩进、换行结构）
- **THEN** 翻译结果中代码段必须保持正确的缩进和换行格式
- **AND** 不改变代码段的空格、缩进和换行

#### Scenario: 行内代码保持格式

- **WHEN** 原文包含行内代码（如 `` `variable_name` ``）
- **THEN** 翻译结果中行内代码保持原格式，不改变空格和标点

#### Scenario: 代码段周围文本翻译

- **WHEN** 原文包含代码段周围有普通文本
- **THEN** 普通文本正常翻译，代码段保持原样且格式化正确
- **AND** 代码段和普通文本之间的结构关系保持不变

## MODIFIED Requirements

### Requirement: 修改 _generate_system_prompt 方法

修改 `modules/translator.py` 的 `_generate_system_prompt` 方法，强化代码段处理规则。

修改前（规则10）：
```python
10. 不要翻译代码段：原文中包含的代码段（包括但不限于代码块、行内代码），保持原状，不进行翻译。
```

修改后（规则10扩展）：
```python
10. **代码段保留与格式化**：原文中包含的代码段（包括但不限于代码块、行内代码），必须：
    - 保持原状，不进行翻译；
    - **保持正确的代码格式**：包括缩进、空格、换行、对齐方式等，不可改变代码的结构化格式；
    - 代码特征识别：连续的多行缩进文本、包含常见编程关键字（如 `def`、`class`、`import`、`if`、`for`、`function`、`var`、`const` 等）、特殊符号（`=`、`=>`、`->`、`<>`、`()`、`{}`、`[]`）及特殊缩进结构的文本，应识别为代码段处理；
    - 保持代码段中的注释原文，不翻译。
```

### Requirement: 保持规则编号顺序

由于修改后规则10文本变长，不影响其他规则的编号和顺序，仅替换规则10的内容。

完整修改后的提示词相关规则（规则10部分）：
```python
10. **代码段保留与格式化**：原文中包含的代码段（包括但不限于代码块、行内代码），必须：
    - 保持原状，不进行翻译；
    - **保持正确的代码格式**：包括缩进、空格、换行、对齐方式等，不可改变代码的结构化格式；
    - 代码特征识别：连续的多行缩进文本、包含常见编程关键字（如 `def`、`class`、`import`、`if`、`for`、`function`、`var`、`const` 等）、特殊符号（`=`、`=>`、`->`、`<>`、`()`、`{}`、`[]`）及特殊缩进结构的文本，应识别为代码段处理；
    - 保持代码段中的注释原文，不翻译。
```

## REMOVED Requirements

（无移除的需求）

## 验证方法

### 测试场景1：代码块格式保持

原文包含代码块：
```
The function is defined as follows:
def calculate_sum(a, b):
    result = a + b
    return result
This function takes two parameters.
```

预期：代码段 `def calculate_sum...return result` 的缩进和换行完全保持，周围文本正常翻译。

### 测试场景2：行内代码格式保持

原文：`Use the print() function to output the result.`

预期：`` `print()` `` 保持原格式，不翻译。

### 测试场景3：多行代码块识别

原文包含带编程关键字的缩进文本：
```
To create a class in Python:
class Animal:
    def __init__(self, name):
        self.name = name
    
    def speak(self):
        print(f"{self.name} makes a sound")
```

预期：代码段缩进和结构化格式完全保持，不翻译代码内容，周围文本正常翻译。
