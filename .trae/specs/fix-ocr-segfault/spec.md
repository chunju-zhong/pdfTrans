# 修复OCR段错误与内存超限 Spec

## Why

OCR功能在16GB内存的Mac上运行时，PP-StructureV3全量加载9个AI模型（2.5GB+）导致内存峰值超限触发段错误，进程崩溃。核心问题是模型全量同时加载，需要改为分步骤加载——每步只加载当前步骤需要的模型，完成后释放，再加载下一步的模型。

## 硬件约束

- CPU: 2.6 GHz 6-Core Intel Core i7
- GPU: Intel UHD Graphics 630 1536 MB（无CUDA，仅CPU模式）
- 内存: 16 GB 2400 MHz DDR4
- macOS对Python进程默认内存限制约4GB，实际可用约3GB

## What Changes

- 修复 `chapter_split` 未传递给 `extract_pdf_content` 的参数断裂问题
- 重构 `PaddleOcrExtractor` 为分步骤提取：原始图片 -> 文本OCR -> 表格识别 -> 公式识别 -> 图表/印章裁剪，每步加载对应模型、完成后释放
- OCR 模式下也提取 PDF 嵌入的原始图片（PyMuPDF 直接提取，无需 OCR）
- 添加内存预检机制：加载模型前检查可用内存，不足时跳过并降级
- 实现 OCR 进程隔离：将 OCR 任务放在子进程中运行，避免主进程崩溃
- 移除 config.py 中 `OCR_USE_TABLE_RECOGNITION` 等功能开关（全部内容类型都识别，无需选择）

## Impact

- Affected specs: OCR功能、翻译流程
- Affected code: `services/translation_service.py`, `modules/pdf_extractor.py`, `modules/ocr/paddle_extractor.py`, `config.py`

## ADDED Requirements

### Requirement: 参数传递一致性

系统 SHALL 确保前端 `chapter_split` 参数正确传递到 PDF 提取阶段。`extract_chapter` 控制的是"是否提取章节信息"，与 OCR 模型加载策略无关。

#### Scenario: 用户未勾选章节拆分

- **WHEN** 前端传入 `chapter_split=False`
- **THEN** `extract_pdf_content` 的 `extract_chapter` 参数为 `False`
- **AND** 不提取章节/书签信息

#### Scenario: 用户勾选章节拆分

- **WHEN** 前端传入 `chapter_split=True`
- **THEN** `extract_pdf_content` 的 `extract_chapter` 参数为 `True`
- **AND** 提取章节/书签信息

### Requirement: OCR 分步骤模型加载与释放

系统 SHALL 将 OCR 提取分为多个步骤，每步只加载当前步骤需要的模型，完成后释放模型内存，再进行下一步。所有内容类型（文本、表格、公式、图表、印章）都识别，无需用户选择。

提取步骤及内存峰值：

| 步骤 | 加载模型 | 内存峰值 | 输出 |
|------|---------|---------|------|
| 0. 原始图片提取 | 无（PyMuPDF直接提取） | ~0MB | PDF嵌入的原始图片 |
| 1. 版面分析+文本OCR | PP-DocBlockLayout + PP-DocLayout_plus-L + PP-OCRv5_det + PP-OCRv5_rec | ~1400MB | 文本块 + 各区域边界框 |
| 2. 表格识别 | PP-LCNet_table_cls + SLANeXt_wired + SLANet_plus + RT-DETR-L x2 | ~1300MB | 结构化表格 |
| 3. 公式识别 | LaTeX OCR | ~200MB | LaTeX 文本 |
| 4. 图表/印章裁剪 | 无额外模型（从渲染图像裁剪） | ~0MB | PdfImage |

每步完成后：删除 PPStructureV3 实例 -> `gc.collect()` -> 内存释放 -> 进入下一步。

#### Scenario: 分步骤提取流程

- **WHEN** 用户启用 OCR 模式
- **THEN** 系统按步骤执行：原始图片提取 -> 版面分析+文本OCR -> 释放 -> 表格识别 -> 释放 -> 公式识别 -> 释放 -> 图表/印章裁剪
- **AND** 每步仅加载该步骤需要的模型
- **AND** 每步完成后释放模型内存
- **AND** 所有内容类型都被识别，无需用户手动选择

#### Scenario: 原始图片提取

- **WHEN** OCR 模式处理 PDF
- **THEN** 使用 PyMuPDF 直接提取 PDF 中嵌入的原始图片（无需 OCR）
- **AND** 原始图片保留完整分辨率和质量，用于目标 PDF 重建

#### Scenario: 某步骤无对应内容

- **WHEN** 版面分析结果显示某页没有表格区域
- **THEN** 跳过该页的表格识别步骤
- **AND** 不加载表格识别模型处理该页

#### Scenario: 内存释放验证

- **WHEN** 某步骤的模型处理完成并释放后
- **THEN** Python 进程的内存占用回落到接近步骤开始前的水平
- **AND** 下一步骤有足够内存加载新模型

### Requirement: 内存预检机制

系统 SHALL 在每个步骤加载模型前检查系统可用内存，防止内存超限导致段错误。

#### Scenario: 可用内存不足

- **WHEN** 某步骤需要加载模型但可用内存低于该步骤的预估需求
- **THEN** 系统跳过该步骤，记录警告日志，继续执行后续步骤
- **AND** 被跳过步骤的内容降级处理（如表格区域保存为图片而非结构化表格）

#### Scenario: 可用内存充足

- **WHEN** 可用内存满足当前步骤的最低需求
- **THEN** 正常加载模型并执行

### Requirement: OCR 进程隔离

系统 SHALL 将 OCR 处理放在独立子进程中运行，OCR 崩溃不影响 Flask 主进程。

#### Scenario: OCR 子进程崩溃

- **WHEN** OCR 子进程因段错误或其他原因崩溃
- **THEN** Flask 主进程保持运行
- **AND** 翻译任务状态更新为错误，显示"OCR处理失败"提示
- **AND** 信号量等 IPC 资源被正确清理

#### Scenario: OCR 子进程正常完成

- **WHEN** OCR 子进程正常完成提取
- **THEN** 提取结果通过序列化方式传回主进程
- **AND** 子进程退出，释放所有模型内存

## MODIFIED Requirements

### Requirement: 移除 OCR 功能开关配置

OCR 识别所有内容类型（文本、表格、公式、图表、印章），不再需要用户选择。移除以下 config 项：

- `OCR_USE_TABLE_RECOGNITION` -- 删除
- `OCR_USE_FORMULA_RECOGNITION` -- 删除

### Requirement: PaddleOcrExtractor 重构为分步骤提取

原设计：一次性创建 PPStructureV3 全量管线，所有模型同时加载。

新设计：分步骤创建不同配置的 PPStructureV3 实例，每步完成后释放：

```python
def extract_from_pdf(self, pdf_path, pages=None, temp_images_dir=None):
    # 步骤0: 提取PDF嵌入的原始图片（无需OCR）
    original_images = self._extract_original_images(pdf_path, pages, temp_images_dir)

    # 步骤1: 版面分析 + 文本OCR
    layout_pipeline = self._create_pipeline(use_table=False, use_formula=False)
    layout_results = self._run_layout_analysis(layout_pipeline, ...)
    del layout_pipeline; gc.collect()

    # 步骤2: 表格识别（仅处理有表格区域的页面）
    if has_table_regions(layout_results):
        table_pipeline = self._create_pipeline(use_table=True, use_formula=False)
        tables = self._run_table_recognition(table_pipeline, ...)
        del table_pipeline; gc.collect()

    # 步骤3: 公式识别
    if has_formula_regions(layout_results):
        formula_pipeline = self._create_pipeline(use_table=False, use_formula=True)
        formulas = self._run_formula_recognition(formula_pipeline, ...)
        del formula_pipeline; gc.collect()

    # 步骤4: 图表/印章裁剪（无额外模型，从渲染图像裁剪）
    chart_seal_images = self._extract_chart_seal_images(layout_results, ...)
```

## REMOVED Requirements

无
