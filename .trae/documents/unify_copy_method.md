# 统一 PdfTable 和 PdfImage 的 copy 方法计划

## 问题
当前 `PdfTable.copy()` 方法只硬编码排除了 `cells` 属性，而 `PdfImage.copy()` 使用通用的循环方式处理排除属性。这两种实现不一致，且 PdfTable 的方式不够通用。

## 解决方案
将 `PdfTable.copy()` 方法修改为与 `PdfImage.copy()` 相同的通用方式，使用循环来处理所有需要排除的属性。

## 修改步骤
1. 修改 `PdfTable.copy()` 方法，使用通用的循环方式处理排除属性
2. 验证代码语法正确

## 预期结果
```python
def copy(self, exclude_attrs=None):
    exclude_attrs = exclude_attrs or []
    new_table = copy_module.copy(self)
    for attr in exclude_attrs:
        setattr(new_table, attr, None)
    return new_table
```

这样两种实现方式一致，且更加通用。
