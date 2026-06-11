# 修复OCR第13页后文件找不到问题 Spec

## Why

PaddleOCR 的 `ImageBatchSampler` 在处理文件路径输入时，会先收集路径再由 `img_reader` 读取。当处理到第13/14页时，由于内部批处理机制，`img_reader` 在读取文件时发现文件路径无效或文件被提前清理，导致 `FileNotFoundError`。

**关键发现**：`ImageBatchSampler` 第95-99行显示，如果输入是 numpy array，直接使用不涉及文件读取。无论传递 numpy array 还是文件路径，最终图像数据都在内存中，**内存使用量相同**。

## What Changes

- 在 `_process_page_layout` 中调用 `pipeline.predict()` 前使用 cv2.imread() 读取图片到 numpy array
- 传递 numpy array 给 PaddleOCR，避免文件路径预取竞态
- 添加文件存在性检查作为防御性编程

## Impact

- Affected specs: OCR页面处理容错性
- Affected code: `modules/ocr/paddle_extractor.py` 的 `_process_page_layout`、`_process_page_tables`、`_process_page_formulas` 方法

## 内存影响分析

| 方案 | 内存使用 | 说明 |
|------|----------|------|
| 传递文件路径（当前） | ~11MB/页 | `img_reader` 内部读取到内存 |
| 传递 numpy array（新方案） | ~11MB/页 | 主线程提前读取到内存 |

**内存使用量相同**，只是读取时机不同。新方案由主线程控制读取时机，避免 PaddleOCR 内部批处理机制的竞态问题。

## ADDED Requirements

### Requirement: OCR图像输入方式优化

系统 SHALL 在调用 PaddleOCR `pipeline.predict()` 时传递 numpy array（cv2.imread 读取的图像数据）而非文件路径。

#### Scenario: 多页PDF OCR处理
- **WHEN** 处理超过12页的PDF文档
- **THEN** 每个页面的图像应在主线程中使用 cv2.imread() 读取到 numpy array
- **AND** 传递给 `pipeline.predict()` 的是 numpy array
- **AND** `ImageBatchSampler` 直接使用 numpy array，不触发文件读取
- **AND** 不应出现 `FileNotFoundError`

### Requirement: 文件存在性防御检查

系统 SHALL 在读取图像文件前检查文件是否存在，若不存在则记录错误并跳过该页面。

#### Scenario: 临时文件意外丢失
- **WHEN** 渲染的临时图片文件因外部原因被删除
- **THEN** 系统应记录错误日志并跳过该页面
- **AND** 继续处理后续页面，不中断整个OCR流程

## MODIFIED Requirements

无

## REMOVED Requirements

无