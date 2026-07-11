# pdfTrans 技术方案文档

本文档详细描述 pdfTrans 项目的核心技术实现方案，涵盖 OCR 管线、翻译管线、语义合并、多格式生成、表格处理、公式渲染、术语提取、错误处理和进度管理等子系统。

---

## 1. OCR 管线架构

### 1.1 双引擎设计

项目采用双 OCR 引擎架构，通过工厂模式按需创建：

- **PaddleOCR 本地引擎**（`PaddleOcrExtractor`）：基于 PP-StructureV3，支持版面分析、表格识别、公式检测，适合本地高性能处理
- **LLM 云端引擎**（`LlmOcrExtractor`）：基于 DeepSeek-OCR / VLM JSON，支持视觉理解式文档解析，适合复杂版面和扫描件

工厂函数 `create_ocr_extractor(ocr_type='paddleocr', **kwargs)` 定义于 `modules/ocr/factory.py`，`SUPPORTED_OCR_ENGINES = ['paddleocr', 'llm']`。

抽象基类 `OcrExtractor(ABC)` 定义于 `modules/ocr/base.py`，核心接口：

```python
@abstractmethod
def extract_from_pdf(self, pdf_path, pages=None, temp_images_dir=None):
    pass
```

### 1.2 PaddleOCR 引擎

#### 1.2.1 分步加载策略

`PaddleOcrExtractor` 采用 PP-StructureV3 分步加载，避免一次性加载全部模型：

- `STEP_LAYOUT_OCR = 1`：版面分析 + 文本 OCR
- `STEP_IMAGE_CROP = 2`：图像裁剪

`_create_pipeline()` 方法创建 PPStructure 管线时，禁用不必要的预处理以提升性能：

```python
kwargs = dict(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    text_det_thresh=0.3,
    text_det_box_thresh=0.5,
    text_rec_score_thresh=0.5,
)
```

#### 1.2.2 标签分类体系

PP-StructureV3 输出的标签分为四组：

| 标签集 | 包含标签 | 用途 |
|--------|---------|------|
| `TEXT_LABELS` | text | 正文文本 |
| `TITLE_LABELS` | title | 标题 |
| `IMAGE_LABELS` | figure, figure_caption, table | 图像与表格区域 |
| `NON_BODY_LABELS` | header, footer, reference, equation | 非正文区域 |

#### 1.2.3 补充捕获机制

`_filter_uncovered_textlines()` 检测版面分析未覆盖的文本行，使用 5px 扩展容差和 15px 垂直分组阈值将遗漏文本行归入最近的父区域。

#### 1.2.4 表格网格计算

`_compute_table_grid()` 基于 textline 的行/列紧密 bbox 计算网格布局：

1. 按 textline 的 y 坐标聚类为行
2. 按 x 坐标聚类为列
3. 累积计算网格布局
4. 检测单元格对齐关系
5. 计算 `estimated_lines`（单元格预估文本行数）

#### 1.2.5 HTML 表格解析

`_TableHtmlParser` 类负责解析 PP-StructureV3 输出的 HTML 格式表格，`_parse_html_table()` 和 `_expand_html_table()` 处理合并单元格（rowspan/colspan）。

### 1.3 LLM OCR 引擎

#### 1.3.1 三阶段响应解析

`LlmOcrExtractor._parse_response()` 实现三阶段解析管线：

1. **格式检测**：自动识别响应格式（`<|ref|>` 标签 / JSON / Markdown）
2. **结构化解析**：按格式调用对应解析器
   - `_parse_ref_tags_to_blocks()`：解析 DeepSeek-OCR 的 `<|ref|>` 标签格式
   - `_parse_json_to_blocks()`：解析 VLM JSON 格式
   - `_parse_markdown_to_blocks()`：解析 Markdown 格式
3. **模型映射**：`_map_ocr_blocks_to_models()` 将 `OcrBlock` 数据类映射为内部模型

#### 1.3.1a 解析器拆分

LLM OCR 的响应解析已从 `LlmOcrExtractor` 拆分为独立模块：

- `modules/ocr/llm_response_parser.py`（`LlmOcrResponseParser`）：负责文本内容的格式检测与结构化解析（`<|ref|>` 标签 / JSON / Markdown）
- `modules/ocr/llm_table_parser.py`（`LlmTableParser`）：负责表格布局计算，实现行高优先迭代优化算法

拆分后 `LlmOcrExtractor` 仅负责 API 调用和页面级编排，解析逻辑委托给上述两个解析器。

#### 1.3.1b 空白页检测

`LlmOcrExtractor` 新增 `_is_blank_image()` 方法，在调用 LLM API 前检测页面是否为空白：

- 计算图像像素的标准差，低于阈值时判定为空白页
- 空白页跳过 LLM 调用，返回空结果，节省 API 调用成本

#### 1.3.1c 超时处理

LLM OCR 调用新增 `APITimeoutError` 捕获，超时时记录警告并跳过当前页面，不中断整体流程。

#### 1.3.2 DeepSeek-OCR 归一化坐标

DeepSeek-OCR 使用 0-999 归一化坐标系，`_pixel_to_pdf_coords()` 通过 `is_normalized` 参数处理坐标转换：

```python
def _pixel_to_pdf_coords(self, bbox, page_width, page_height, is_normalized=False):
    if is_normalized:
        # DeepSeek-OCR: 0-999 归一化坐标
        x0 = bbox.x0 * page_width / 999
        y0 = bbox.y0 * page_height / 999
        x1 = bbox.x1 * page_width / 999
        y1 = bbox.y1 * page_height / 999
```

#### 1.3.3 提示词设计

- DeepSeek-OCR：`DEEPSEEK_OCR_PROMPT = "<image>\n<|grounding|>Convert the document to markdown."`
- VLM JSON：`VLM_JSON_SYSTEM_PROMPT`（7 规则 JSON 提取提示词）

#### 1.3.4 表格布局优化

`_compute_table_layout()` 实现行高优先迭代优化算法：

- 默认参数：`font_size=9.0`，`single_line_height=font_size*1.2`，`min_col_ratio=0.1`，`max_col_ratio=0.5`
- 迭代控制：`max_iterations=3`，`convergence_threshold=0.5`
- 每次迭代根据文本内容重新计算行高，直到布局收敛

### 1.4 子进程隔离

`modules/ocr/ocr_worker.py` 实现子进程隔离，防止 PaddleOCR 内存泄漏影响主进程。

#### 1.4.1 子进程环境变量

```python
env = {
    'FLAGS_fraction_of_gpu_memory_to_use': '0.5',
    'KMP_DUPLICATE_LIB_OK': 'TRUE',
    'MKL_THREADING_LAYER': 'sequential',
}
# 无 GPU 时
if not use_gpu:
    env['CUDA_VISIBLE_DEVICES'] = '-1'
```

#### 1.4.2 参数退化策略

`_degrade_params()` 在每次重试时退化参数：

| 参数 | 退化规则 |
|------|---------|
| 线程数 | -1 |
| 内存因子 | ×0.8 |
| 内存上限 | ×0.8 |
| DPI | -20（最小 72） |
| 超时 | ×2.0 |
| 跳过表格 | attempt ≥ 1 时跳过 |
| 跳过公式 | attempt ≥ 2 时跳过 |

#### 1.4.3 重试机制

`run_ocr_in_subprocess()` 实现指数退避重试（×1.5），支持 `skip_pages` 断点续传。

### 1.5 系统自适应参数

`modules/ocr/system_profiler.py` 的 `OcrParameterCalculator` 根据系统资源自动计算 OCR 参数。

#### 1.5.1 五级内存分级

| 级别 | 内存范围 | 内存因子 | 布局上限 | 表格上限 | 公式上限 | DPI |
|------|---------|---------|---------|---------|---------|-----|
| minimal | 0-8GB | 0.35 | 1000MB | 800MB | 500MB | 120 |
| low | 8-17GB | 0.45 | 1400MB | 1200MB | 800MB | 120 |
| medium | 17-33GB | 0.55 | 1800MB | 1600MB | 1000MB | 150 |
| high | 33-65GB | 0.60 | 2600MB | 2400MB | 1500MB | 150 |
| unlimited | 65GB+ | 0.65 | 3400MB | 3200MB | 2000MB | 200 |

#### 1.5.2 模型选择

各级别对应不同规模的模型：

| 级别 | 版面模型 | 公式模型 | OCR 模型 | 表格模型 |
|------|---------|---------|---------|---------|
| minimal | PP-DocLayout-S | PP-FormulaNet_plus-S | PP-OCRv4_mobile | SLANet |
| low | PP-DocLayout-S | PP-FormulaNet_plus-S | PP-OCRv4_mobile | SLANet |
| medium | PP-DocLayout-M | PP-FormulaNet_plus-M | PP-OCRv4_server | SLANet_plus |
| high | PP-DocLayout-L | PP-FormulaNet_plus-L | PP-OCRv4_server | SLANet_plus |
| unlimited | PP-DocLayout-L | PP-FormulaNet_plus-L | PP-OCRv4_server | SLANet_plus |

GPU 可用时，模型级别自动提升一级。

#### 1.5.3 高负载检测

当内存使用 >85% 或负载均值 > CPU 核数 ×0.8 时，触发高负载模式：线程数 = `max(1, cpu//4)`，内存因子 ×0.85。

---

## 2. 翻译管线架构

### 2.1 三翻译器设计

| 翻译器 | 类名 | 流式 | 重试 | extra_body |
|--------|------|------|------|-----------|
| Aiping | `AipingTranslator` | `stream=True` | `max_retries=3` | `config.AIPING_EXTRA_BODY` |
| SiliconFlow | `SiliconFlowTranslator` | `stream=True` | `max_retries=0` | `config.SILICON_FLOW_EXTRA_BODY` |
| 百度千帆 | `QianfanTranslator` | `stream=True` | `max_retries=0` | `config.QIANFAN_EXTRA_BODY` |

三者共享基类 `Translator`（`modules/translator.py`），通用参数：`temperature=0.1`，`top_p=0.9`，`max_tokens` 动态计算（见 2.6）。`QianfanTranslator` 使用百度千帆 OpenAI 兼容 API（默认地址 `https://qianfan.baidubce.com/v2`），通过 `QIANFAN_API_KEY` 认证。

### 2.2 四节结构系统提示词

`Translator._generate_system_prompt()` 生成包含 4 节结构的系统提示词：

1. **核心原则**：语义连贯、自然过渡、风格一致、简洁
2. **语义与风格**：术语一致、不增不减、语法正确、技术精确
3. **保持格式**：不翻译 URL、保留代码格式、长度控制、不翻译公式、不解释缩写、保留列表格式、保留单元格分隔符 `|||`
4. **禁止元注释**：不输出元注解/原文

提示词通过 `rule_registry.merge_into_prompt()` 注入语言专项规则（详见第 9 节「语言专项规则系统」），实现按翻译方向动态扩展。

### 2.3 预处理与后处理

- **同语言直接返回**：源语言与目标语言相同时，跳过翻译
- **空文本/`"..."`回退**：空字符串或仅含省略号时，返回原文
- **后处理**：`_postprocess_text()` 清理翻译结果中的冗余标记

### 2.4 截断检测

两个翻译器均实现截断检测：

```python
if finish_reason == "length":
    truncation_info = TruncationInfo(truncated=True, ...)
```

### 2.5 流式响应处理

三个翻译器均使用 `stream=True` 流式调用，逐 chunk 拼接 `delta.content`。`AipingTranslator` 额外跳过 `reasoning_content`（推理内容），仅统计其长度用于诊断：

```python
if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content:
    reasoning_length += len(chunk.choices[0].delta.reasoning_content)
    continue  # 跳过推理内容
```

`format_blocks` 排版调用同样使用流式，但异常不内部捕获，向上抛出由调用方 `translation_content.py` 通过 `task.add_warning` 上报 UI（详见 10.3）。

### 2.6 动态 max_tokens 计算

翻译器和排版模型不再使用固定 `max_tokens`，而是根据输入文本长度动态计算：

```python
# Translator 基类实例方法
def _calculate_max_tokens(self, input_text, max_ceiling=None):
    estimated_tokens = len(input_text) / CHARS_PER_TOKEN  # CHARS_PER_TOKEN=3
    dynamic = max(MIN_OUTPUT_TOKENS, int(estimated_tokens * EXPANSION_FACTOR))  # EXPANSION_FACTOR=3, MIN_OUTPUT_TOKENS=256
    ceiling = max_ceiling if max_ceiling is not None else self.max_tokens
    return min(dynamic, ceiling)

# 独立函数（供非 Translator 子类使用）
def calculate_max_tokens(input_text, max_ceiling, chars_per_token=3, expansion_factor=3, min_output_tokens=256):
    ...
```

- **翻译调用**：三个翻译器均使用 `self._calculate_max_tokens(text)`，上限为 `self.max_tokens`（默认 8192）
- **排版调用**：`format_blocks` 使用 `self._calculate_max_tokens(blocks_text, max_ceiling=config.LAYOUT_MAX_TOKENS)`；`MarkdownGenerator` 使用 `calculate_max_tokens(user_prompt, self.max_tokens)`

### 2.7 翻译质量检测与重试

#### 2.7.1 未翻译检测

`_is_translation_unchanged` 采用双重策略检测 LLM 未翻译的情况：

1. **原有策略**：`|||` 分段检测 — 将译文按 `|||` 分段，判断所有分段是否均来自原文
2. **新增策略**：高相似度 + 无目标语言字符 — 去除断字标记后计算归一化相似度 >85% 且译文不含目标语言（默认中文 CJK）字符

辅助方法：
- `_normalize_for_comparison`：去除软连字符断字标记和多余空白
- `_calculate_similarity`：短文本（≤500字符）使用 LCS，长文本使用字符集交集近似
- `_contains_target_language_chars`：检测是否包含 CJK 统一汉字（U+4E00-U+9FFF）

#### 2.7.2 垃圾输出检测

`_is_translation_garbage` 检测 LLM 输出异常：

- **膨胀检测**：译文长度 > 原文长度 × 5
- **重复模式检测**：同一子串（2-50字符）连续重复 > 10 次

#### 2.7.3 自动重试

合并块和原始块翻译流程中，检测到未翻译时自动重试一次：

```python
if self._is_translation_unchanged(translated_text, original_text):
    retry_result = translator.translate(original_text, ...)
    if not self._is_translation_unchanged(retry_result.content, original_text):
        translated_text = retry_result.content  # 重试成功
    else:
        translated_text = original_text  # 重试失败，回退原文
```

垃圾输出检测在截断检测之后执行，覆盖正常和截断两种场景，检测到时直接回退原文。

### 2.8 格式排版开关

翻译后 LLM 格式排版通过 `ENABLE_FORMAT_BLOCKS` 配置控制：

| 值 | 行为 |
|----|------|
| `false`（默认） | 不执行格式排版 |
| `true` | 始终执行格式排版 |
| `auto` | 仅当输出格式包含 PDF 时执行（`output_format` 为 `pdf`/`pdf_docx`/`all`） |

`_translate_content` 方法接收 `output_format` 参数，结合 `config.ENABLE_FORMAT_BLOCKS` 判断是否执行排版步骤。

---

## 3. 语义合并策略

### 3.1 规则合并

`merge_semantic_blocks()`（`utils/text_processing.py`）基于规则判断文本块是否应合并：

**合并条件**（同时满足）：
- 垂直相邻（距离 < 10px）
- 满足以下之一：
  - 有章节信息
  - 前一块不是完整句子结束
  - 当前块是句子延续

**强制分割条件**：
- 章节标题与正文之间
- 不同章节之间
- 对齐方式变化
- 公式块独立成块

**空格处理**：合并时智能添加空格——前块不以空格结尾且后块不以空格开头时插入一个空格。

### 3.2 LLM 合并

`merge_semantic_blocks_with_llm()` 使用语义分析器批量判断合并关系：

- 批量大小：`batch_size=10`
- 每批包含前一个块的文本作为上下文
- 分析失败时跳过当前批次

### 3.3 两阶段并行合并

`merge_semantic_blocks_with_llm_two_phase()` 实现两阶段架构：

**阶段 1**：并行调用 LLM 获取所有文本对的合并判断

- 使用 `parallel_batch_analyze()` 函数
- overlap-1-block 批次策略：相邻批次重叠 1 个块，确保边界对也被分析
- 参数：`max_workers=5`，`batch_size=20`，`max_retries=3`
- 每批失败时返回 `[False] * (len(batch) - 1)` 作为默认值

**阶段 2**：根据预存的判断结果顺序执行合并

### 3.4 语义角色分析

`SemanticAnalyzer`（`modules/semantic_analyzer.py`）实现两步分析：

1. **语义角色识别**：将文本块分类为 body、title、signature、list_item、quote_body
2. **合并决策矩阵**：

| 前块角色 | 后块角色 | 决策 |
|---------|---------|------|
| body | body | 进一步检查 |
| body | title | 不合并 |
| body | signature | 不合并 |
| body | list_item | 进一步检查 |
| title | * | 多数不合并 |
| signature | * | 始终不合并 |
| list_item | list_item | 延续性检查 |

容错策略：3 次重试，结果数量不匹配时用 `False` 填充，JSON 解析失败时返回 `[False] * count`。

### 3.5 翻译结果拆分

`split_translated_result()` 将合并翻译结果按原始文本块长度比例拆分：

- 最小字符数：`min_characters_per_block=3`
- 拆分位置调整：`adjust_split_position()` 确保英文单词完整性、标点不在块首、左成对字符不在块尾
- 空块修复：从相邻块借用内容
- 最终检查：块首标点调整 + 块尾左成对字符修复

---

## 4. PDF 生成技术

### 4.0 渲染器拆分

`PdfGenerator`（`modules/pdf_generator.py`）的渲染逻辑已拆分为两个独立模块：

- `modules/pdf_text_renderer.py`（`PdfTextRenderer`）：负责文本绘制，包括两遍绘制策略、字体选择链、字体大小估算、行高倍率计算、文本溢出处理
- `modules/pdf_table_renderer.py`（`PdfTableRenderer`）：负责表格绘制，包括表格两遍策略、合并单元格处理、可见线段计算、单元格字体大小动态计算

拆分后 `PdfGenerator` 作为门面类协调两个渲染器，保持对外接口不变。

### 4.1 两遍绘制策略

`PdfGenerator._draw_translated_text()`（`modules/pdf_generator.py`）采用两遍绘制：

**第一遍**：添加 redaction 标注，标记需要删除的原文区域

```python
page.add_redact_annot(bg_rect, fill=(1, 1, 1))
# ...
page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
```

- 水平内边距：`h_padding = max(5, min(font_size * 0.5, 12))`
- 垂直内边距：`v_padding = max(3, min(font_size * 0.3, 6))`
- `images=fitz.PDF_REDACT_IMAGE_NONE` 确保不删除图片

**第二遍**：按原文样式渲染翻译文本

### 4.2 字体选择链

`_get_suitable_font()` 按优先级选择字体：

1. 检查原始字体是否支持目标语言（`_check_embedded_font_support()`）
2. 查找 Arial Unicode 字体（多语言通用）
3. 遍历系统字体查找兼容字体（`_check_font_support()`）
4. 无法找到时抛出 `ValueError`

字体缓存：`font_cache` 以 `(original_font, target_lang)` 为键缓存查找结果，避免重复的文件系统查找。

### 4.3 字体大小估算

当 `font_size == 0`（如 LLM OCR 无样式信息）时，根据 bbox 高度估算：

```python
if original_font_size == 0:
    original_font_size = min(bbox_height * 0.75, 36)
```

### 4.4 行高倍率计算

```python
estimated_lines = max(1, round(bbox_height / (font_size * 1.2)))
original_lineheight = bbox_height / (font_size * estimated_lines)
original_lineheight = max(1.0, min(original_lineheight, 2.0))
```

### 4.5 公式渲染降级链

`_render_formula_image()` 实现四级降级：

| 级别 | 方法 | 说明 |
|------|------|------|
| 1 | usetex | 系统安装 LaTeX 时使用，支持完整 LaTeX 命令 |
| 2 | mathtext 原始 | 用原始 LaTeX 尝试 mathtext 渲染 |
| 3 | mathtext 预处理 | `_preprocess_latex_for_mathtext()` 预处理后渲染 |
| 4 | 返回 None | 渲染完全失败，降级为文本 |

LaTeX 可用性检测（`_check_latex_available()`）使用双重检测：先检查 PATH，再探测常见安装路径（macOS/Linux/Windows），结果缓存在类变量 `_latex_available` 中。

### 4.6 LaTeX 预处理

`_preprocess_latex_for_mathtext()` 执行以下转换：

1. `\(...\)` → `$...$`，`\[...\]` → `$$...$$`
2. `$$...$$` → `$...$`（mathtext 不支持 display math）
3. 去除数学字体命令：`\text{}`、`\mathrm{}`、`\mathbf{}` 等
4. 去除环境包装：`\begin{aligned}...\end{aligned}` 等
5. 希腊字母替换：`\alpha` → `α`，`\beta` → `β` 等
6. 数学符号替换：`\circ` → `°`，`\cdot` → `·` 等
7. 去除 `\left` 和 `\right` 命令

### 4.7 混合公式文本渲染

`_render_mixed_text_formula_image()` 处理包含 LaTeX 公式片段的非公式文本块，同样遵循 usetex → mathtext 降级链。

### 4.8 文本溢出处理

`_draw_translated_text()` 实现五级溢出处理：

1. **字体缩小**（5 次尝试）：每次缩小 10%，最小不低于原大小的 70%
2. **极限缩小**：缩小到 60% 和 50%
3. **行高调整**：尝试 lineheight=1.5、1.8、2.0
4. **智能截断**：按单词边界截断（英文）或按字符数截断（CJK），保留至少 30%
5. **机械截断**：每次截断 10%，保留至少 30%

### 4.9 表格绘制

`_draw_translated_table()` 同样采用两遍策略（redaction + 插入），并实现：

- 合并单元格内部网格线跳过绘制
- `_compute_visible_segments()` 计算可见线段
- 单元格字体大小动态计算：`base_font_size = min(cell_height * 0.8, 12)`
- `estimated_lines` 预判单元格容量

### 4.10 文档压缩

保存时启用压缩优化：

```python
new_doc.save(output_pdf_path, deflate=True, garbage=4, clean=True)
```

---

## 5. DOCX 生成技术

### 5.1 LaTeX → MathML → OMML 转换链

`DocxGenerator`（`modules/docx_generator.py`）实现 LaTeX 公式到 Word OMML 的转换：

1. LaTeX 字体命令预处理：去除 `\mathsf`、`\mathrm`、`\mathbf`、`\mathit`、`\mathcal`、`\mathbb`、`\mathfrak`、`\mathscr`、`\mathtt`
2. `latex2mathml` 库将 LaTeX 转为 MathML
3. `_mathml_to_omml_element()` 将 MathML 转为 Office Math Markup Language (OMML)

### 5.2 OMML 元素处理

`_make_mr()` 和相关方法处理以下 OMML 元素：

| MathML 元素 | OMML 元素 | 说明 |
|------------|----------|------|
| math | oMath | 数学区域 |
| mrow | r | 行 |
| mstyle | r | 样式 |
| mi | r | 标识符（变量名） |
| mo | r | 运算符 |
| mn | r | 数字 |
| mtext | r | 文本 |
| mfrac | f | 分数 |
| msup | sSup | 上标 |
| msub | sSub | 下标 |
| msubsup | sSubSup | 上下标 |
| msqrt | rad | 平方根 |
| mover | acc | 上方标记 |
| munder | sSub | 下方标记 |

### 5.3 表格处理

- 固定布局：`MAX_TABLE_WIDTH_INCHES = 6.5`
- 列宽：按 PDF 原始比例分配
- 行高：从 PDF 原始数据获取
- 合并单元格：`word_table.cell().merge()`
- 单元格对齐：左/居中/右对齐

### 5.4 图表定位

`_find_chart_position()` 和 `_find_merged_block()` 通过 y 坐标查找图表在原始文本块中的位置，确定插入点。

### 5.5 XML 兼容性

`_clean_xml_compatible_text()` 清理文本中的不兼容字符，保留可打印 ASCII（32-126）、制表/换行/回车（9/10/13）和 Unicode 字符（128+）。

---

## 6. Markdown 生成技术

### 6.1 LLM 驱动排版

`MarkdownGenerator`（`modules/markdown_generator.py`）使用 LLM 将翻译文本格式化为结构化 Markdown：

- `_format_with_layout_model()` 调用布局模型
- `_load_layout_prompt()` 加载排版提示词模板
- 布局提示词包含 6 条规范：内容结构、突出重点、格式规范、禁止代码块标记、保留图像、保留数学公式

### 6.2 公式保护占位符

`_format_with_layout_model()` 在调用 LLM 前保护公式内容：

1. 提取公式并替换为 `__FORMULA_N__` 占位符
2. 先替换独立行公式 `$$...$$`，再替换行内公式 `$...$`
3. LLM 响应后恢复占位符为原始公式

```python
text_for_llm = re.sub(r'\$\$(.+?)\$\$', replace_formula, text, flags=re.DOTALL)
text_for_llm = re.sub(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', replace_formula, text_for_llm)
```

### 6.3 截断检测

```python
truncated = finish_reason == "length"
```

### 6.4 章节拆分并行生成

`_generate_chapter_markdowns()` 使用 `ThreadPoolExecutor(max_workers=config.MAX_WORKERS)` 并行生成各章节的 Markdown。

### 6.5 Aiping 变体

`AipingMarkdownGenerator` 覆写 `_call_api()` 方法，使用 `extra_body=config.AIPING_EXTRA_BODY`。

### 6.6 工厂函数

```python
create_markdown_generator(api_type, api_key, api_url, model)
```

根据 `api_type` 创建对应的 Markdown 生成器实例。

---

## 7. 表格处理管线

### 7.1 双引擎提取

#### 7.1.1 Camelot 提取（非 OCR）

`extract_tables_by_camelot()`（`modules/extractors/table_processor.py`）使用 Camelot 库提取表格：

- 优先使用 `lattice` 模式（基于线条检测）
- 失败时回退到 `stream` 模式（基于空白检测）
- 坐标系转换：`convert_pdf_to_pymupdf_coords()` 将 PDF 标准坐标（原点左下）转为 PyMuPDF 坐标（原点左上）

#### 7.1.2 PyMuPDF 提取（非 OCR）

`extract_tables_by_pymupdf()` 使用 PyMuPDF 内置表格检测，支持精确的单元格 bbox。

### 7.2 精确字符分配

`extract_table_cells_by_bbox()` 使用 50% 面积重叠判断将字符分配到单元格：

1. 从 `page.get_text("rawdict")` 获取字符级数据
2. 表格 bbox 过滤：2px 容差，排除表外字符
3. 对每个字符，计算与各单元格的交集面积
4. 重叠超过 50% 才分配到该单元格
5. 按阅读顺序（y 坐标 → x 坐标）排序字符并拼接

### 7.3 合并单元格推断

`compute_span_from_none_positions()`（`modules/extractors/coordinate_utils.py`）从 PyMuPDF 返回的 None 位置推断合并单元格：

1. 向右扫描同行连续 None，确定 col_span
2. 标记被 col_span 覆盖的 None 位置
3. 向下扫描确定 row_span，跳过已被 col_span 覆盖的 None
4. 基于 row_span 重新验证 col_span

### 7.4 网格布局计算

- `calculate_row_heights_from_bboxes()`：从真实单元格 bbox 推算行高，取同行最大高度
- `calculate_col_widths_from_bboxes()`：从真实单元格 bbox 推算列宽，合并单元格宽度按跨列数等分分配，最终按比例缩放使总和等于表格实际宽度

### 7.5 对齐方式检测

- `extract_cell_alignment()`：文本中心与单元格中心偏移 < 15% → 居中；左边缘偏移 < 10% → 左对齐；右边缘偏移 < 10% → 右对齐
- `detect_text_block_alignment()`：左/右对齐优先于居中检测；宽块（>55% 页面宽度）判定为左对齐

### 7.6 OCR 表格处理

PaddleOCR：`_TableHtmlParser` 解析 HTML 格式表格，`_compute_table_grid()` 基于 textline 计算网格布局。

LLM OCR：`_compute_table_layout()` 实现行高优先迭代优化算法（见 1.3.4），`_parse_html_table()` 解析 HTML 表格。

---

## 8. 公式检测与渲染

### 8.1 检测规则

`LlmOcrExtractor._detect_formula()` 检测以下格式的公式：

- 独立行公式：`$$...$$`
- 行内公式：`$...$`
- LaTeX 定界符：`\(...\)`、`\[...\]`
- LaTeX 数学环境：aligned、gathered、cases、equation、align、gather、matrix 变体

### 8.2 LaTeX 清理

`PaddleOcrExtractor._clean_latex()` 清理 PaddleOCR 输出的 LaTeX：

- 去除多余的转义
- 修复常见的 OCR 错误
- 标准化公式格式

### 8.3 多级渲染降级

PDF 输出中的公式渲染降级链（详见 4.5）：

```
usetex → mathtext 原始 → mathtext 预处理 → 跳过（纯文本）
```

DOCX 输出中的公式转换链：

```
LaTeX → MathML → OMML（Word 原生公式格式）
```

Markdown 输出中的公式保护：

```
$$...$$ / $...$ → __FORMULA_N__ 占位符 → LLM 处理 → 恢复原始公式
```

### 8.4 混合公式文本

`PdfGenerator._contains_latex_formula()` 检测非公式文本块中的 LaTeX 片段，`_render_mixed_text_formula_image()` 整体渲染混合文本。

---

## 9. 术语表提取与章节识别

### 9.1 术语表提取

#### 9.1.1 双提取器设计

`modules/glossary_extractor.py` 定义抽象基类和两个实现：

| 提取器 | 类名 | extra_body | 超时 |
|--------|------|-----------|------|
| Aiping | `AipingGlossaryExtractor` | `config.AIPING_EXTRA_BODY` | 30s |
| SiliconFlow | `SiliconFlowGlossaryExtractor` | `config.SILICON_FLOW_EXTRA_BODY` | 30s |

工厂函数：`create_glossary_extractor(extractor_type)`，支持 `'aiping'` 和 `'silicon_flow'` 两种类型。

#### 9.1.2 NO_GLOSSARY 哨兵值

当 LLM 判断文本中没有专业术语时，返回 `NO_GLOSSARY` 标识。`_format_glossary()` 方法跳过包含 `NO_GLOSSARY` 的行。

#### 9.1.3 提取规则

提示词包含以下核心规则：
- 只提取指定领域的真正专业术语
- 排除普通词汇、日常用语、人名、地名、公司名
- 约定俗成词汇保持原样（AI、ML、LLM、ChatGPT 等）
- 源语言与目标语言相同时不提供翻译
- 每个术语只提取一次
- 输入文本截断为前 5000 字符

#### 9.1.4 输出格式

每行一个术语，格式为 `术语: 翻译`。

### 9.2 章节识别

#### 9.2.1 书签提取

`ChapterIdentifier`（`modules/chapter_identifier.py`）从 PDF 书签构建章节树：

```python
bookmarks = doc.get_toc(simple=False)
chapters = self._build_chapter_tree(bookmarks, doc)
```

#### 9.2.2 标题定位

`_locate_title_blocks()` 在页面中查找章节标题对应的文本块，使用三级匹配策略：

1. **精确匹配**（score=100）：文本完全相同
2. **高相似度匹配**（score=90+）：`difflib.SequenceMatcher` 相似度 > 0.9
3. **子字符串匹配**（score=50）：标题是文本的子串
4. **跨块匹配**（score=80+）：合并最多 3 个连续文本块

#### 9.2.3 章节树构建

`_build_chapter_tree()` 使用栈结构构建层级关系：

- 最大层级：`max_level=3`
- 标题截断：`max_title_length=20`，超出部分添加 `...`

#### 9.2.4 默认章节

当 PDF 开头有书签未覆盖的页面时，`_create_default_chapters()` 创建默认章节：

- 智能命名（`use_smart_naming=True`）：使用页面第一个文本块作为标题
- 回退命名：`{文件名}-第{页码}页`

#### 9.2.5 元素关联

- `associate_text_blocks()`：将文本块关联到对应章节
- `associate_tables()`：将表格关联到对应章节
- `associate_images()`：将图像关联到对应章节

关联算法：`_find_best_chapter()` 根据页码和 y 坐标查找最匹配的章节。

---

## 10. 错误处理与重试机制

### 10.1 OCR 三层保护

`modules/ocr/ocr_worker.py` 实现三层保护机制：

| 层级 | 机制 | 参数 |
|------|------|------|
| 心跳监控 | `_heartbeat_sender()` | 15 秒间隔（`stop_event.wait(15)`） |
| 停滞检测 | 超时检查 | 动态超时 = `avg_time_per_page × 1.5` |
| 总超时 | 全局超时 | 用户配置的超时时间 |

#### 10.1.1 心跳超时

主进程监控子进程心跳，心跳超时时触发重试。

#### 10.1.2 停滞检测

`_run_ocr_once()` 检测处理停滞：如果当前页面处理时间超过平均时间的 1.5 倍，视为停滞。

#### 10.1.3 部分结果保留

超时或错误时，已成功提取的页面结果会被保留，通过 `skip_pages` 参数在重试时跳过已处理页面。

### 10.2 OCR 参数退化

每次重试时参数退化（详见 1.4.2），逐步降低资源消耗以提高成功率。

### 10.3 翻译重试与错误分类

- Aiping：`max_retries=3`，指数退避
- SiliconFlow：`max_retries=0`（无 SDK 重试）
- 百度千帆：`max_retries=0`（无 SDK 重试）
- 所有翻译器均捕获异常并通过 `modules/llm_error_handler.py` 的 `classify_llm_error(e)` 统一分类，映射为中文用户友好消息（如认证失败/速率限制/请求超时/服务内部错误等），超时时记录警告并跳过当前文本块，不中断整体流程
- `format_blocks` 排版调用异常不再内部吞没，向上抛出由 `translation_content.py` 通过 `task.add_warning` 上报 UI，使用 `classify_llm_error` 生成友好消息

### 10.4 语义分析容错

- 3 次重试
- 结果数量不匹配时用 `False` 填充
- JSON 解析失败时返回 `[False] * count`
- 批量分析失败时跳过当前批次

### 10.5 生成降级

#### 10.5.1 PDF 公式渲染降级

```
usetex → mathtext 原始 → mathtext 预处理 → 纯文本
```

#### 10.5.2 PDF 文本溢出降级

```
字体缩小 → 极限缩小 → 行高调整 → 智能截断 → 机械截断
```

#### 10.5.3 Markdown 生成降级

布局模型请求失败时重试 3 次（`max_retries=3`，`retry_delay=2s`），最终失败抛出异常。

### 10.6 PPStructureV3 日志污染修复

`PaddleOcrExtractor._restore_logger_state()` 在 OCR 处理前后保存和恢复 logger 配置，防止 PPStructureV3 修改全局日志级别。

---

## 11. 进度管理模型

### 11.1 七阶段进度配置

`PHASE_CONFIG`（`models/phase_config.py`）定义翻译任务的 7 个阶段：

| 阶段 | ID | 名称 | 进度范围 |
|------|-----|------|---------|
| 1 | init | 初始化 | 0-5 |
| 2 | extraction | 文本图表提取 | 5-40 |
| 3 | semantic_merge | 语义合并 | 40-50 |
| 4 | translation | 文本翻译 | 50-85 |
| 5 | table_translation | 表格翻译 | 85-92 |
| 6 | generation | 生成输出 | 92-98 |
| 7 | clean | 清理临时文件 | 98-100 |

### 11.2 术语提取三阶段配置

`GLOSSARY_PHASE_CONFIG` 定义术语提取任务的 3 个阶段：

| 阶段 | ID | 名称 | 进度范围 |
|------|-----|------|---------|
| 1 | init | 开始提取 | 0-5 |
| 2 | pdf_extraction | 文本提取 | 5-30 |
| 3 | term_extraction | 术语提取 | 30-100 |

### 11.3 Task 状态机

`Task`（`models/task.py`）继承 `CopyableMixin`，状态流转：

```
pending → processing → completed
                    → error
                    → canceled
```

状态枚举：`TASK_STATUS = {'PENDING': 'pending', 'PROCESSING': 'processing', 'COMPLETED': 'completed', 'ERROR': 'error'}`

### 11.4 进度更新

- `update_progress(progress, message)`：直接设置整体进度（0-100）
- `update_phase_progress(phase, phase_percent, message)`：按阶段计算整体进度

阶段内进度到整体进度的映射：

```python
overall_progress = start + round((end - start) * phase_percent / 100)
```

### 11.5 线程安全

`Task` 使用 `threading.RLock()` 保护所有状态变更操作，确保多线程环境下的数据一致性。

### 11.6 任务类型

`set_task_type(task_type)` 切换任务类型：

- `'translation'`：使用 `PHASE_CONFIG`
- `'glossary'`：使用 `GLOSSARY_PHASE_CONFIG`

---

## 9. 语言专项规则系统

### 9.1 规则注册表

`PromptRuleRegistry`（`prompts/rule_registry.py`）是语言专项规则的单例注册表，负责按翻译方向（源语言→目标语言）查找并注入额外提示词规则。

核心方法：

- `merge_into_prompt(base_prompt, source_lang, target_lang)`：将匹配的语言专项规则追加到基础提示词末尾，返回增强后的完整提示词
- `register(source_lang, target_lang, rules)`：注册一条语言专项规则

### 9.2 规则文件组织

```
prompts/
├── __init__.py                 # 模块初始化
├── rule_registry.py            # PromptRuleRegistry — 规则注册表（单例）
└── language_rules/             # 语言专项规则目录
    ├── __init__.py             # 自动发现与注册规则
    ├── base.py                 # 通用基础规则
    └── bo_to_zh.py             # 藏文→中文专项规则
```

### 9.3 规则自动发现

`language_rules/__init__.py` 在模块加载时自动扫描同目录下的规则文件，调用 `rule_registry.register()` 完成注册。新增语言专项规则只需在 `language_rules/` 目录下添加规则文件并实现注册即可，无需修改其他代码。

### 9.4 现有规则

| 源语言 | 目标语言 | 规则文件 | 说明 |
|--------|---------|---------|------|
| — | — | `base.py` | 通用基础规则，适用于所有翻译方向 |
| `bo` | `zh` | `bo_to_zh.py` | 藏文→中文专项规则，处理藏文特有翻译问题 |

### 11.7 取消机制

`cancel()` 方法设置 `canceled=True`，`update_progress()` 和 `update_phase_progress()` 在取消后返回 `False`，停止进度更新。

### 11.8 配置验证

`validate_phase_config()` 验证阶段配置的有效性：

- 每个阶段必须有 start 和 end
- start 和 end 必须是数字
- 范围必须在 0-100 之间
- start 必须小于 end
