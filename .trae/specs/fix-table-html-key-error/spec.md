# 修复 OCR 表格识别结果 HTML 提取键名错误 Spec

## Why

OCR 表格识别步骤2（`_process_page_tables`）从 PP-StructureV3 的 `table_res` 中提取 HTML 时，使用了错误的键名 `'html'`，而 PaddleX 的 `SingleTableRecognitionResult.html` 属性返回 `{"pred": "<html>..."}`，实际键名是 `'pred'`。这导致 `html` 变量为空字符串，表格被跳过，最终输出 0 个表格。

## 根因分析

### 问题链路

1. 步骤1布局分析检测到 `table` 标签，设置 `has_table = True`
2. 步骤2创建 `use_table=True` 的 PP-StructureV3 管线，调用 `pipeline.predict()`
3. 结果中 `table_res_list` 包含 `SingleTableRecognitionResult` 对象
4. `table_res.html` 属性返回 `{"pred": self["pred_html"]}`（键名为 `'pred'`）
5. 代码执行 `html_dict.get('html', '')`，键名 `'html'` 不存在，返回空字符串
6. `if not html: continue` 跳过该表格
7. 最终输出 0 个表格，表格内容完全丢失

### 日志证据

```
[LAYOUT_DEBUG] page=1: {'footer': 1, 'header': 1, 'number': 1, 'table': 1, 'text': 2}
步骤2完成: 表格识别，管线已释放
OCR提取完成: 共1页, 0个表格, 0个图像
```

布局分析检测到 1 个表格，但步骤2输出 0 个表格。

### PaddleX 源码验证

`SingleTableRecognitionResult._to_html()` 返回 `{"pred": self["pred_html"]}`，键名是 `'pred'` 而非 `'html'`。

文件路径：`paddlex/inference/pipelines/table_recognition/result.py` 第48行：
```python
def _to_html(self) -> Dict[str, str]:
    return {"pred": self["pred_html"]}
```

## 方案对比

### 方案A：修复键名（最小改动）

仅将 `html_dict.get('html', '')` 改为 `html_dict.get('pred', '')`，保持现有的两步架构不变。

**优点**：改动最小，风险最低
**缺点**：
1. 步骤2需要单独创建管线，增加总处理时间
2. 两步架构并不能真正降低内存峰值（见下方分析）

### 方案B：步骤1启用 `use_table=True`（合并步骤）

在步骤1中直接使用 `use_table=True`，PP-StructureV3 在布局分析的同时完成表格识别，结果直接包含 `table_res_list`，无需步骤2。

**优点**：
1. 减少一次管线创建/销毁，降低总处理时间
2. 表格识别和布局分析在同一次管线调用中完成，结果一致性更好
3. 避免步骤2中 `table_res_list` 为空的问题（表格识别在布局分析时同步完成）
4. 简化代码，减少步骤2相关的管线管理逻辑
5. 内存峰值与方案A相同（见下方分析）

**缺点**：
1. 每页都会运行表格识别（即使没有表格），但 PP-StructureV3 只在检测到表格区域时才运行表格识别模型，无表格页面开销极小

### 两步架构的内存分析

当前两步架构的设计意图是：步骤1加载布局+OCR+公式模型（~1600MB），处理完后释放，再加载步骤2表格识别模型（~1300MB），从而降低峰值内存。

**但实际效果有限**，原因：
1. **PaddlePaddle C++ 内存池不释放**：PaddlePaddle 使用 C++ 后端分配 tensor 内存，Python 的 `gc.collect()` 只能释放 Python 对象，无法释放 C++ 内部分配的内存
2. **`malloc_zone_pressure_relief` / `malloc_trim` 无效**：只能释放 C 标准库分配的内存碎片，不能释放 PaddlePaddle C++ 内存池的内存
3. **实际内存行为**：步骤1 `del pipeline` + `gc.collect()` 后，C++ 层内存可能不会归还给操作系统，步骤2加载时实际内存 = 步骤1残留（~1600MB）+ 步骤2新增（~1300MB）= ~2900MB
4. **结论**：两步架构的内存峰值与方案B（步骤1直接 `use_table=True`）相同，约 2900MB

**推荐方案B**：步骤1启用 `use_table=True`，在步骤1中直接处理 `table_res_list`，移除步骤2。理由：
1. PP-StructureV3 的 `use_table_recognition=True` 设计就是在布局分析时同步完成表格识别，这是官方推荐用法
2. 当前步骤2单独创建管线时 `table_res_list` 为空，很可能是因为 PP-StructureV3 在独立运行时无法正确关联布局分析和表格识别的结果
3. 两步架构并不能真正降低内存峰值（C++ 层内存不释放），合并步骤不会增加内存压力
4. 减少一次管线创建/销毁，降低总处理时间

## What Changes

- **步骤1启用表格识别**：将 `_create_pipeline(use_table=False, ...)` 改为 `_create_pipeline(use_table=True, ...)`
- **步骤1处理 `table_res_list`**：在步骤1的 `result` 处理中，从 `result["table_res_list"]` 提取表格 HTML 和 bbox，创建 `PdfTable` 对象
- **移除步骤2**：移除 `_process_page_tables` 方法和步骤2的调用逻辑
- **修复 HTML 提取键名**：使用 `html_dict.get('pred', '')` 替代 `html_dict.get('html', '')`
- **增加诊断日志**：记录表格识别结果

## Impact

- Affected code: `modules/ocr/paddle_extractor.py`
- Affected specs: `fix-table-ocr-translation`（端到端验证未通过，根因在此）

## ADDED Requirements

### Requirement: 步骤1启用表格识别

系统在步骤1布局分析时，必须启用 `use_table_recognition=True`，使 PP-StructureV3 在布局分析的同时完成表格识别。

#### Scenario: 步骤1包含表格识别
- **WHEN** 系统执行步骤1布局分析
- **THEN** PP-StructureV3 管线使用 `use_table_recognition=True`
- **AND** `result` 中包含 `table_res_list`

### Requirement: 步骤1处理表格识别结果

系统在步骤1中处理 `result` 时，必须从 `table_res_list` 提取表格 HTML 和 bbox，创建 `PdfTable` 对象。

#### Scenario: 步骤1提取表格
- **WHEN** 步骤1的 `result` 包含 `table_res_list`
- **AND** `table_res_list` 非空
- **THEN** 系统从 `table_res.html` 中使用键名 `'pred'` 提取 HTML
- **AND** 创建 `PdfTable` 对象并添加到结果中

### Requirement: 修复表格 HTML 提取键名

系统在从 `table_res` 中提取 HTML 时，必须使用正确的键名 `'pred'`（PaddleX `SingleTableRecognitionResult.html` 属性返回 `{"pred": ...}`）。

#### Scenario: 表格识别结果包含 HTML
- **WHEN** PP-StructureV3 表格识别返回 `table_res_list`
- **AND** `table_res.html` 返回 `{"pred": "<html>..."}`
- **THEN** 系统使用 `html_dict.get('pred', '')` 提取 HTML
- **AND** HTML 内容非空，表格被正确解析

### Requirement: 移除步骤2

系统不再需要步骤2（`_process_page_tables`），因为表格识别已在步骤1中完成。

#### Scenario: 表格处理流程简化
- **WHEN** 系统执行 OCR 提取
- **THEN** 步骤1同时完成布局分析和表格识别
- **AND** 不再创建步骤2的单独管线

### Requirement: 表格识别诊断日志

系统在步骤1中处理表格识别结果时，必须记录诊断日志，包括 `table_res_list` 长度、每个表格的 HTML 提取结果。

#### Scenario: 表格识别步骤执行
- **WHEN** 步骤1处理 `table_res_list`
- **THEN** 记录 `table_res_list` 长度
- **AND** 如果 `table_res_list` 为空但检测到 `table` 标签，记录 WARNING
- **AND** 如果 HTML 提取为空，记录 WARNING

## MODIFIED Requirements

（无修改的需求）

## REMOVED Requirements

（无移除的需求）
