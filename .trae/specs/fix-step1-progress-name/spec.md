# 修正步骤名称并消除硬编码 Spec

## Why
步骤 1 的 `step_name` 为"版面分析+文本OCR"，但实际执行版面分析+文本OCR+公式识别+表格识别。此外，step_name 和 step 编号在 `paddle_extractor.py` 和 `translation_service.py` 中多处硬编码，应提取为常量集中管理，避免不一致和重复。

## What Changes
- 在 `paddle_extractor.py` 类级别定义步骤常量（步骤编号和名称），消除硬编码
- 将步骤 1 名称从"版面分析+文本OCR"改为"版面分析+文本+公式+表格"
- 所有 status_callback 调用和日志消息引用常量而非硬编码字符串
- `translation_service.py` 中 `STEP_WEIGHTS` 的键引用常量而非硬编码数字

## Impact
- Affected code: `modules/ocr/paddle_extractor.py`、`services/translation_service.py`

## ADDED Requirements

### Requirement: 步骤常量集中定义
`PaddleOcrExtractor` 类 SHALL 定义步骤常量，集中管理步骤编号和名称：

```python
STEP_LAYOUT_OCR = 1
STEP_LAYOUT_OCR_NAME = '版面分析+文本+公式+表格'
STEP_IMAGE_CROP = 2
STEP_IMAGE_CROP_NAME = '图像裁剪'
```

#### Scenario: 步骤名称统一管理
- **WHEN** 需要修改步骤名称
- **THEN** 只需修改常量定义，无需搜索所有硬编码字符串

### Requirement: 步骤 1 名称反映实际操作
步骤 1 的名称 SHALL 为"版面分析+文本+公式+表格"，反映其执行的全部操作。

#### Scenario: OCR 进度提示显示正确步骤名称
- **WHEN** 步骤 1 开始或完成时发送进度回调
- **THEN** 用户看到的进度消息为"OCR提取: 版面分析+文本+公式+表格 X/Y页"

### Requirement: STEP_WEIGHTS 键引用常量
`translation_service.py` 中 `STEP_WEIGHTS` 的键 SHALL 引用 `PaddleOcrExtractor` 的步骤常量，而非硬编码数字。

#### Scenario: STEP_WEIGHTS 使用常量
- **WHEN** 查看 STEP_WEIGHTS 定义
- **THEN** 键为 `PaddleOcrExtractor.STEP_LAYOUT_OCR` 和 `PaddleOcrExtractor.STEP_IMAGE_CROP`，而非 `1` 和 `2`

## MODIFIED Requirements

### Requirement: status_callback 和日志使用常量
`extract_from_pdf` 中所有 `status_callback` 调用和日志消息 SHALL 引用步骤常量，而非硬编码字符串。

涉及位置：
- `step_start` 回调：使用 `self.STEP_LAYOUT_OCR` 和 `self.STEP_LAYOUT_OCR_NAME`
- `step_progress` 回调：使用 `self.STEP_LAYOUT_OCR`
- `step_complete` 回调：使用 `self.STEP_LAYOUT_OCR` 和 `self.STEP_LAYOUT_OCR_NAME`
- 步骤 2 的 `step_start`/`step_complete`：使用 `self.STEP_IMAGE_CROP` 和 `self.STEP_IMAGE_CROP_NAME`
- 日志消息：引用常量
- 内存检查中的 step_name：引用常量
