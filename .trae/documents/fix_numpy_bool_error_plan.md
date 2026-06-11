# Fix numpy boolean error plan

## Problem
`_compute_cell_bboxes` 方法中的条件判断 `if not cells or not textline_boxes:` 导致 ValueError，因为 `textline_boxes` 可能是 numpy 数组，直接进行布尔判断会产生歧义。

## Solution
修改第 1173 行的条件判断，使用 `is not None` 和 `len()` 进行安全检查。

## Files to modify
- `/Users/chunju/work/pdfTrans/modules/ocr/paddle_extractor.py`

## Changes
将第 1173 行：
```python
if not cells or not textline_boxes:
```
改为：
```python
if not cells or textline_boxes is None or len(textline_boxes) == 0:
```

## Risk
低风险，只是修复布尔判断方式，不影响逻辑。

## Testing
运行语法检查和现有测试。
