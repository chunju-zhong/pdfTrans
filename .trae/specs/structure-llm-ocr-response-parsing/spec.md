# 结构化优化 LLM OCR 响应解析 Spec

## Why
当前 `LlmOcrExtractor` 的响应解析逻辑存在正则脆弱、代码重复、类型信息丢失、隐式对齐等结构性问题，且 **LLM OCR 识别到的图像区域完全缺失裁剪保存步骤**（`image_path` 硬编码为空字符串），导致 DOCX 输出图像丢失、Markdown 输出生成无效 `![]()` 引用。需要将解析流程重构为清晰的阶段化管道，消除重复代码，增强格式检测准确性，并补全图像裁剪保存功能。

## What Changes
- 将 `_parse_response` 重构为三阶段管道：格式检测 → 结构化中间表示 → 模型映射
- 引入 `OcrBlock` 中间数据类，统一 JSON/ref/Markdown 三种格式的解析输出
- 提取 `_create_text_block` 公共方法，消除 `_parse_json_response` 和 `_parse_ref_tags_response` 中的重复代码
- 修复 `_extract_json` 第三级容错误判问题，增加格式互斥检测
- 将 DeepSeek-OCR 的 `block_type`（title/sub_title/text 等）映射到 `TextBlock.block_type`
- 优化 `_parse_ref_tags_response` 的正则，改用分步解析替代单正则前瞻
- 修复 `table_bbox_map` 隐式索引对齐问题，改用显式标记关联
- 对归一化坐标增加越界钳位
- **新增图像裁剪保存功能**：根据 bbox 从原始 PDF 页面裁剪图像并保存，填充 `image_path`

## Impact
- Affected code: `modules/ocr/llm_extractor.py`
- Affected tests: `tests/test_llm_ocr.py`, `tests/test_llm_extractor_multi_bbox.py`
- Affected downstream: `modules/docx_generator.py`（图像嵌入）、`modules/markdown_generator.py`（图像引用）
- Affected specs: `fix-llm-ocr-response-parsing`, `fix-deepseek-ocr-full-parsing`

## ADDED Requirements

### Requirement: 三阶段解析管道
系统 SHALL 将响应解析重构为三个独立阶段：格式检测、结构化解析、模型映射。

#### Scenario: 格式检测阶段
- **WHEN** 收到 LLM 原始响应文本
- **THEN** 系统按优先级检测格式：ref标签 → JSON（仅严格匹配） → Markdown，且格式检测互斥

#### Scenario: 结构化解析阶段
- **WHEN** 格式确定后
- **THEN** 各格式解析器输出统一的 `OcrBlock` 列表，每个 OcrBlock 包含 text、bbox、block_type、is_image、table_html 字段

#### Scenario: 模型映射阶段
- **WHEN** OcrBlock 列表生成后
- **THEN** 统一通过 `_create_text_block` 等方法映射为 TextBlock/PdfTable/PdfImage

### Requirement: OcrBlock 中间数据类
系统 SHALL 定义 `OcrBlock` 数据类作为解析中间表示。

#### Scenario: OcrBlock 字段
- **WHEN** 创建 OcrBlock
- **THEN** 包含以下字段：`text`(str)、`bbox`(tuple)、`block_type`(str)、`is_image`(bool)、`table_html`(str|None)、`bboxes`(list[tuple]) 用于多 bbox 场景

### Requirement: 公共 TextBlock 创建方法
系统 SHALL 提取 `_create_text_block` 公共方法，统一处理公式检测、字体估算、坐标转换。

#### Scenario: 消除重复代码
- **WHEN** 从 OcrBlock 映射为 TextBlock
- **THEN** 公式检测、字体估算、is_body_text 标记、坐标转换均在此方法中统一处理，不再在各解析器中重复

### Requirement: 格式检测互斥
系统 SHALL 确保 JSON 格式检测不会从 ref 标签文本中误提取 JSON。

#### Scenario: ref 标签文本包含花括号
- **WHEN** 响应包含 `<|ref|>` 标签且文本中包含 `{...}` 子串
- **THEN** 系统优先识别为 ref 标签格式，不尝试 JSON 解析

#### Scenario: 纯 JSON 响应
- **WHEN** 响应以 `{` 开头且不包含 `<|ref|>` 标签
- **THEN** 系统识别为 JSON 格式

### Requirement: block_type 类型映射
系统 SHALL 将 DeepSeek-OCR 返回的类型标签映射到 TextBlock 的语义属性。

#### Scenario: title 类型映射
- **WHEN** `<|ref|>title<|/ref|>` 或 `<|ref|>sub_title<|/ref|>`
- **THEN** TextBlock 的 `is_body_text = False`，`block_type` 设置为标题类型

#### Scenario: text 类型映射
- **WHEN** `<|ref|>text<|/ref|>`
- **THEN** TextBlock 的 `is_body_text = True`，`block_type` 设置为正文类型

#### Scenario: 其他类型映射
- **WHEN** `<|ref|>header<|/ref|>` 或 `<|ref|>footer<|/ref|>` 或 `<|ref|>footnote<|/ref|>`
- **THEN** TextBlock 的 `is_body_text = False`

### Requirement: ref 标签分步解析
系统 SHALL 将 ref 标签解析从单正则前瞻改为分步解析，提高鲁棒性。

#### Scenario: 分步解析流程
- **WHEN** 解析 ref 标签响应
- **THEN** 先用正则提取所有 `<|ref|>...<|/ref|><|det|>...<|/det|>` 标注对及其位置，再根据位置区间提取中间文本

### Requirement: 显式表格坐标关联
系统 SHALL 用显式标记替代 `table_bbox_map` 的隐式索引对齐。

#### Scenario: 表格坐标关联
- **WHEN** ref 块包含 HTML 表格
- **THEN** 在 OcrBlock 中保存 table_html 和 bbox，映射阶段直接从 OcrBlock 取用坐标，不再依赖全文扫描索引对齐

### Requirement: 归一化坐标越界钳位
系统 SHALL 对 DeepSeek-OCR 归一化坐标进行越界钳位。

#### Scenario: 坐标超过 999
- **WHEN** `<|det|>` 中的坐标值超过 999
- **THEN** 钳位到 [0, 999] 范围后再转换为 PDF 点坐标

#### Scenario: 坐标为负数
- **WHEN** `<|det|>` 中的坐标值为负数
- **THEN** 钳位到 0 后再转换

### Requirement: LLM OCR 图像裁剪保存
系统 SHALL 在 LLM OCR 提取器中根据 bbox 从原始 PDF 页面裁剪图像并保存，使 `PdfImage.image_path` 指向实际文件。

#### Scenario: DeepSeek-OCR ref 标签中的图像
- **WHEN** DeepSeek-OCR 返回 `<|ref|>image<|/ref|><|det|>[[x1,y1,x2,y2]]<|/det|>` 标签
- **THEN** 系统根据 bbox 坐标从原始 PDF 页面裁剪图像区域，保存为 PNG 文件到 `temp_images_dir`，`PdfImage.image_path` 设置为实际保存路径

#### Scenario: JSON 格式中的图像
- **WHEN** 通用 VLM 模型返回 JSON 中的 images 数组包含 bbox
- **THEN** 同样根据 bbox 裁剪保存图像

#### Scenario: 图像裁剪实现方式
- **WHEN** 需要裁剪图像
- **THEN** 使用 fitz（PyMuPDF）的 `page.get_pixmap(clip=rect)` 方法，rect 为 PDF 点坐标的 Rect，将裁剪结果保存为 PNG

#### Scenario: DOCX 输出验证
- **WHEN** LLM OCR 提取的图像被传入 DOCX 生成器
- **THEN** `os.path.exists(image_path)` 返回 True，图像正常嵌入到 Word 文档

#### Scenario: Markdown 输出验证
- **WHEN** LLM OCR 提取的图像被传入 Markdown 生成器
- **THEN** 生成有效的 `![](images_xxx/ocr_img_p1_0.png)` 引用，图像文件被复制到输出目录

## MODIFIED Requirements

### Requirement: DeepSeek-OCR 响应解析
LLM OCR SHALL 通过三阶段管道解析 DeepSeek-OCR 响应，输出统一的 OcrBlock 中间表示，再映射为 TextBlock/PdfTable/PdfImage。

#### Scenario: ref 标签响应解析
- **WHEN** DeepSeek-OCR 返回包含 `<|ref|>` 标签的响应
- **THEN** 分步提取标注对和文本，生成 OcrBlock 列表，block_type 从 `<|ref|>` 标签提取

#### Scenario: Markdown 响应解析
- **WHEN** DeepSeek-OCR 返回纯 Markdown 文本
- **THEN** 按段落分割生成 OcrBlock 列表，block_type 为 "text"

#### Scenario: JSON 响应解析
- **WHEN** 通用 VLM 模型返回 JSON
- **THEN** 从 JSON 字段生成 OcrBlock 列表，block_type 从 "type" 字段提取

### Requirement: LLM OCR 图像输出
LLM OCR 提取的图像 SHALL 与 PaddleOCR 提取器行为一致，`image_path` 指向实际裁剪保存的图像文件。

#### Scenario: 与 PaddleOCR 一致性
- **WHEN** LLM OCR 和 PaddleOCR 都识别到同一图像区域
- **THEN** 两者创建的 PdfImage 的 `image_path` 都指向实际存在的图像文件，下游 DOCX/Markdown 生成器可正常使用
