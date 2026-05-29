# Plan: 传统OCR集成（Phase 1）

## Summary

为PDF翻译工具集成PaddleOCR PP-StructureV3引擎，添加OCR模式开关，使扫描版PDF的文字、表格和图表可被提取并翻译。OCR输出映射为现有TextBlock/PdfTable/PdfImage模型，无缝接入下游翻译和文档生成流程。

## User Story

As a 需要翻译国外技术文档的技术人员,
I want 直接使用工具提取扫描版PDF中的文字、表格和图表并翻译,
So that 无需手动使用OCR工具预处理扫描版PDF即可完成翻译。

## Problem → Solution

**Current**: 扫描版PDF无法提取文字，翻译工具报错或输出空白 → **Desired**: 启用OCR模式后，扫描版PDF可成功提取文字、表格和图表并翻译

## Metadata
- **Complexity**: Large
- **Source PRD**: `.claude/PRPs/prds/pdf-ocr-extraction.prd.md`
- **PRD Phase**: Phase 1 - 传统OCR集成
- **Estimated Files**: 14

---

## UX Design

### Before
```
┌─────────────────────────────────────────┐
│  用户上传扫描版PDF                       │
│  → 工具提取文本为空                      │
│  → 翻译结果为空/报错                     │
│  → 用户需手动OCR → 复制文字 → 翻译       │
└─────────────────────────────────────────┘
```

### After
```
┌─────────────────────────────────────────┐
│  CLI: python cli.py translate input.pdf  │
│        --ocr --source en --target zh     │
│  Web:  勾选"启用OCR提取"开关             │
│  → PP-StructureV3版面分析                │
│  → 文本/表格/图表分别提取                │
│  → 映射为TextBlock/PdfTable/PdfImage    │
│  → 进入现有翻译管线 → 输出翻译文档       │
└─────────────────────────────────────────┘
```

### Interaction Changes

| Touchpoint | Before | After | Notes |
|---|---|---|---|
| CLI translate | 无OCR参数 | 新增 `--ocr` 开关 | 默认关闭，不影响现有流程 |
| Web界面 | 无OCR选项 | 新增"启用OCR提取"复选框 | 与semantic_merge并列 |
| 翻译进度 | extraction阶段 | extraction阶段内细分OCR进度 | 进度消息区分OCR/文本提取 |
| 配置文件 | 无OCR配置 | 新增OCR相关环境变量 | 遵循现有 `os.environ.get()` 模式 |

---

## Mandatory Reading

Files that MUST be read before implementing:

| Priority | File | Lines | Why |
|---|---|---|---|
| P0 (critical) | `modules/pdf_extractor.py` | 1-310 | OCR核心插入点，理解extract流程 |
| P0 (critical) | `models/text_block.py` | all | OCR输出必须映射为TextBlock |
| P0 (critical) | `models/extraction.py` | all | PdfExtraction/PdfTable/PdfImage结构 |
| P1 (important) | `modules/extractors/table_processor.py` | 50-65 | 多引擎分发模式参照 |
| P1 (important) | `modules/glossary_extractor.py` | all | ABC基类+工厂函数模式参照 |
| P1 (important) | `services/translation_service.py` | 204-293 | extract_pdf_content数据流 |
| P1 (important) | `config.py` | all | 配置扩展模式 |
| P2 (reference) | `cli.py` | 120-185 | CLI参数定义模式 |
| P2 (reference) | `app.py` | 36-98 | Web参数传递模式 |
| P2 (reference) | `models/phase_config.py` | all | 阶段进度配置 |

## External Documentation

| Topic | Source | Key Takeaway |
|---|---|---|
| PP-StructureV3 API | PaddleOCR 3.x docs | 使用`PPStructureV3`类（非2.x的`PPStructure`），`predict()`返回迭代器 |
| PP-StructureV3 输出 | PaddleOCR 3.x docs | `layout_det_res.bboxes/labels/scores` + `table_res_list[].html` + `ocr_res.rec_texts` |
| PP-StructureV3 安装 | PaddleOCR 3.x docs | `pip install "paddleocr[all]"` + `paddlepaddle`/`paddlepaddle-gpu` |
| 版本兼容性 | 社区文档 | 3.x与2.x接口完全不兼容，`__call__`变为`predict()` |
| 性能基准 | PaddleOCR官方 | GPU: ~1s/页，CPU: ~5-15s/页 |

---

## Patterns to Mirror

### NAMING_CONVENTION
// SOURCE: modules/glossary_extractor.py, modules/semantic_analyzer.py
```python
# ABC基类：无前缀
class GlossaryExtractor(ABC):
    @abstractmethod
    def extract_glossary(self, text, source_lang, target_lang, doc_type=None) -> str: ...

# 具体实现：{Provider}{BaseName}
class AipingGlossaryExtractor(GlossaryExtractor): ...
class SiliconFlowGlossaryExtractor(GlossaryExtractor): ...

# 工厂函数：create_{entity}
def create_glossary_extractor(extractor_type: str) -> GlossaryExtractor: ...
```

### ERROR_HANDLING
// SOURCE: modules/pdf_extractor.py:131-135, services/translation_service.py:1433-1441
```python
# 验证失败 -> ValueError
if not self.pdf_path:
    raise ValueError("PDF文件路径不能为空")

# 文件不存在 -> FileNotFoundError
if not os.path.exists(self.pdf_path):
    raise FileNotFoundError(f"PDF文件不存在: {self.pdf_path}")

# 任务级异常 -> logger.error + task.set_error
except Exception as e:
    logger.error(f"任务 {task.task_id} 处理失败: {str(e)}", exc_info=True)
    task.set_error(f"翻译失败: {str(e)}")
```

### LOGGING_PATTERN
// SOURCE: modules/pdf_extractor.py:1-16, services/translation_service.py
```python
# 模块级：直接获取logger
import logging
logger = logging.getLogger(__name__)

# 级别约定：
# info  - 流程关键节点
logger.info(f"任务 {task.task_id} 开始提取PDF文本")
# debug - 详细中间数据
logger.debug(f"页面{current_page_num} 文本块 {block_no} 与表格重叠")
# warning - 非致命问题、降级
logger.warning(f"lattice模式提取失败: {e}，尝试使用stream模式")
# error - 异常、失败（带exc_info）
logger.error(f"提取PDF文本时出错: {str(e)}", exc_info=True)
```

### STRATEGY_PATTERN (多引擎分发)
// SOURCE: modules/pdf_extractor.py:25-60
```python
class PdfExtractor:
    def __init__(self, pdf_path=None, table_extractor='pymupdf'):
        self.table_extractor = table_extractor

    def extract_tables(self, pages=None):
        if self.table_extractor == 'camelot':
            return extract_tables_by_camelot(self.pdf_path, pages)
        else:
            return extract_tables_by_pymupdf(self.pdf_path, pages)
```

### CONFIG_PATTERN
// SOURCE: config.py:1-78
```python
class Config:
    # 功能开关：os.environ.get + 默认值 + .lower() == 'true'
    USE_TWO_PHASE_MERGE = os.environ.get('USE_TWO_PHASE_MERGE', 'true').lower() == 'true'
    # API配置：os.environ.get + or 默认值
    AIPING_API_KEY = os.environ.get('AIPING_API_KEY')
    AIPING_MODEL = os.environ.get('AIPING_MODEL_TRANSLATION') or 'Qwen3-32B'
    # 数值配置：int(os.environ.get(...))
    MAX_WORKERS = int(os.environ.get('MAX_WORKERS', '8'))

config = Config()  # 模块级单例
```

### TEST_STRUCTURE
// SOURCE: pytest.ini, tests/conftest.py
```python
# 测试文件：tests/test_{module}.py
# 测试类：Test{ClassName}
# 测试方法：test_{behavior}
# Fixtures：conftest.py 提供 test_pdf_path, mock_translator_response 等
# 断言：assert isinstance / assert result.xxx > 0 / with pytest.raises(...)
# Mock：unittest.mock.patch 避免真实API调用
```

---

## Files to Change

| File | Action | Justification |
|---|---|---|
| `modules/ocr/__init__.py` | CREATE | OCR模块包初始化 |
| `modules/ocr/base.py` | CREATE | OcrExtractor ABC基类 |
| `modules/ocr/paddle_extractor.py` | CREATE | PaddleOcrExtractor实现 |
| `modules/ocr/factory.py` | CREATE | create_ocr_extractor工厂函数 |
| `modules/pdf_extractor.py` | UPDATE | 添加ocr_mode参数，OCR分支逻辑 |
| `config.py` | UPDATE | 添加OCR配置项 |
| `cli.py` | UPDATE | 添加--ocr参数 |
| `cli/translate_command.py` | UPDATE | 传递ocr参数到service |
| `services/translation_service.py` | UPDATE | 传递ocr参数，调用OCR提取 |
| `app.py` | UPDATE | Web端接收ocr参数 |
| `templates/index.html` | UPDATE | 添加OCR开关UI |
| `models/phase_config.py` | UPDATE | OCR提取阶段进度 |
| `requirements.txt` | UPDATE | 添加paddleocr依赖 |
| `tests/test_ocr_extractor.py` | CREATE | OCR模块测试 |

## NOT Building

- LLM-based OCR（DeepSeek OCR/Qwen3-VL）— 属于Phase 2
- 混合策略自动选择 — 属于Phase 3
- PaddleOCR直接导出Markdown的简化管线 — 保留TextBlock管线
- 手写体识别优化
- 实时OCR翻译
- OCR语言自动检测（Should优先级，后续迭代）

---

## Step-by-Step Tasks

### Task 1: 创建OCR模块基础结构
- **ACTION**: 创建 `modules/ocr/` 目录及ABC基类
- **IMPLEMENT**:
  ```python
  # modules/ocr/__init__.py
  from .base import OcrExtractor
  from .factory import create_ocr_extractor

  # modules/ocr/base.py
  from abc import ABC, abstractmethod
  from models.extraction import PdfExtraction

  class OcrExtractor(ABC):
      """OCR提取器抽象基类"""

      @abstractmethod
      def extract_from_pdf(self, pdf_path, pages=None, temp_images_dir=None) -> PdfExtraction:
          """从PDF提取内容

          Args:
              pdf_path: PDF文件路径
              pages: 指定页码列表（1-based），None表示全部
              temp_images_dir: 临时图像目录

          Returns:
              PdfExtraction: 与文本提取模式相同的结构
          """
          pass
  ```
- **MIRROR**: GlossaryExtractor ABC模式（`modules/glossary_extractor.py`）
- **IMPORTS**: `from abc import ABC, abstractmethod`, `from models.extraction import PdfExtraction`
- **GOTCHA**: 返回类型必须是 `PdfExtraction`，与 `PdfExtractor.extract()` 完全一致
- **VALIDATE**: `python -c "from modules.ocr import OcrExtractor"` 无报错

### Task 2: 实现PaddleOcrExtractor
- **ACTION**: 创建 `modules/ocr/paddle_extractor.py`，实现PP-StructureV3集成
- **IMPLEMENT**:
  ```python
  # modules/ocr/paddle_extractor.py
  import os
  import logging
  import fitz  # PyMuPDF，用于PDF转图像
  from models.text_block import TextBlock
  from models.extraction import PdfPage, PdfTable, PdfCell, PdfImage, PdfExtraction
  from .base import OcrExtractor

  logger = logging.getLogger(__name__)

  class PaddleOcrExtractor(OcrExtractor):
      """基于PaddleOCR PP-StructureV3的OCR提取器"""

      def __init__(self, lang='ch', use_gpu=True,
                   use_table_recognition=True, use_formula_recognition=False,
                   use_seal_recognition=False, use_chart_recognition=False):
          self.lang = lang
          self.use_gpu = use_gpu
          self.use_table_recognition = use_table_recognition
          self.use_formula_recognition = use_formula_recognition
          self.use_seal_recognition = use_seal_recognition
          self.use_chart_recognition = use_chart_recognition
          self._pipeline = None

      @property
      def pipeline(self):
          """延迟初始化PP-StructureV3管线"""
          if self._pipeline is None:
              from paddleocr import PPStructureV3
              self._pipeline = PPStructureV3(
                  use_doc_orientation_classify=False,
                  use_doc_unwarping=False,
                  use_textline_orientation=False,
                  use_table_recognition=self.use_table_recognition,
                  use_formula_recognition=self.use_formula_recognition,
                  use_seal_recognition=self.use_seal_recognition,
                  use_chart_recognition=self.use_chart_recognition,
                  device="gpu:0" if self.use_gpu else "cpu",
                  lang=self.lang,
              )
          return self._pipeline

      def extract_from_pdf(self, pdf_path, pages=None, temp_images_dir=None) -> PdfExtraction:
          if not os.path.exists(pdf_path):
              raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

          if temp_images_dir is None:
              temp_images_dir = os.path.join(os.getcwd(), 'temp_images')
          os.makedirs(temp_images_dir, exist_ok=True)

          pdf_pages = []
          pdf_tables = []
          pdf_images = []

          with fitz.open(pdf_path) as doc:
              total_pages = len(doc)
              target_pages = pages if pages else range(1, total_pages + 1)

              for page_num in target_pages:
                  page_idx = page_num - 1
                  if page_idx >= total_pages:
                      continue
                  page = doc[page_idx]

                  # 渲染页面为图像
                  pix = page.get_pixmap(dpi=200)
                  img_path = os.path.join(temp_images_dir, f"page_{page_num}.png")
                  pix.save(img_path)

                  # PP-StructureV3处理
                  page_text_blocks, page_tables, page_images = self._process_page(
                      img_path, page_num, temp_images_dir
                  )

                  pdf_pages.append(PdfPage(page_num=page_num, text_blocks=page_text_blocks))
                  pdf_tables.extend(page_tables)
                  pdf_images.extend(page_images)

          return PdfExtraction(
              total_pages=total_pages,
              pages=pdf_pages,
              tables=pdf_tables,
              images=pdf_images
          )

      def _process_page(self, img_path, page_num, temp_images_dir):
          """处理单页图像，返回(text_blocks, tables, images)"""
          text_blocks = []
          tables = []
          images = []
          block_no = 0
          table_idx = 0
          image_idx = 0

          for result in self.pipeline.predict(img_path):
              res = result.res
              layout = res.get('layout_det_res', {})

              if not layout:
                  continue

              bboxes = layout.get('bboxes', [])
              labels = layout.get('labels', [])

              for i, (bbox, label) in enumerate(zip(bboxes, labels)):
                  x1, y1, x2, y2 = bbox

                  if label in ('text', 'document_title', 'section_title',
                               'abstract', 'references', 'footnote',
                               'header', 'footer', 'page_number',
                               'sidebar_text', 'text_continue'):
                      # 文本区域 -> TextBlock
                      text = self._extract_text_for_region(res, bbox, label)
                      if text and text.strip():
                          tb = TextBlock(
                              block_no=block_no,
                              text=text,
                              bbox=(float(x1), float(y1), float(x2), float(y2)),
                              block_type=0,
                              page_num=page_num
                          )
                          # 标记非正文
                          if label in ('header', 'footer', 'page_number', 'footnote'):
                              tb.is_body_text = False
                          text_blocks.append(tb)
                          block_no += 1

                  elif label == 'table':
                      # 表格区域 -> PdfTable
                      table = self._extract_table_for_region(res, bbox, page_num, table_idx)
                      if table:
                          tables.append(table)
                          table_idx += 1

                  elif label in ('image', 'chart', 'figure_caption'):
                      # 图表区域 -> PdfImage
                      img = self._extract_image_for_region(
                          img_path, bbox, page_num, image_idx, temp_images_dir
                      )
                      if img:
                          images.append(img)
                          image_idx += 1

                  elif label in ('formula', 'formula_number'):
                      # 公式区域 -> TextBlock（保留LaTeX原文）
                      formula_text = self._extract_formula_for_region(res, bbox)
                      if formula_text:
                          tb = TextBlock(
                              block_no=block_no,
                              text=formula_text,
                              bbox=(float(x1), float(y1), float(x2), float(y2)),
                              block_type=0,
                              page_num=page_num
                          )
                          text_blocks.append(tb)
                          block_no += 1

                  elif label == 'seal':
                      # 印章区域 -> PdfImage
                      img = self._extract_image_for_region(
                          img_path, bbox, page_num, image_idx, temp_images_dir
                      )
                      if img:
                          images.append(img)
                          image_idx += 1

          return text_blocks, tables, images

      def _extract_text_for_region(self, res, bbox, label):
          """从OCR结果中提取指定区域的文本"""
          ocr_res = res.get('ocr_res', {})
          rec_texts = ocr_res.get('rec_texts', [])
          dt_polys = ocr_res.get('dt_polys', [])

          if not rec_texts or dt_polys is None:
              return ''

          x1, y1, x2, y2 = bbox
          region_texts = []

          for text, poly in zip(rec_texts, dt_polys):
              # 检查文本行中心是否在区域内
              if len(poly) >= 2:
                  cx = (poly[0][0] + poly[2][0]) / 2 if len(poly) >= 4 else poly[0][0]
                  cy = (poly[0][1] + poly[2][1]) / 2 if len(poly) >= 4 else poly[0][1]
                  if x1 <= cx <= x2 and y1 <= cy <= y2:
                      region_texts.append(text)

          return '\n'.join(region_texts)

      def _extract_table_for_region(self, res, bbox, page_num, table_idx):
          """从OCR结果中提取表格"""
          table_res_list = res.get('table_res_list', [])

          for table_res in table_res_list:
              html = table_res.get('html', '')
              if not html:
                  continue

              # 解析HTML表格为PdfCell二维列表
              cells = self._parse_html_table(html)
              if cells:
                  return PdfTable(
                      page_num=page_num,
                      table_idx=table_idx,
                      cells=cells,
                      bbox=(float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
                  )
          return None

      def _parse_html_table(self, html):
          """解析HTML表格为PdfCell二维列表"""
          # 简化实现：使用正则或html.parser
          # 实际实现需处理rowspan/colspan
          from html.parser import HTMLParser

          class TableParser(HTMLParser):
              def __init__(self):
                  super().__init__()
                  self.rows = []
                  self.current_row = []
                  self.current_cell = ''
                  self.in_cell = False

              def handle_starttag(self, tag, attrs):
                  if tag == 'td' or tag == 'th':
                      self.in_cell = True
                      self.current_cell = ''

              def handle_endtag(self, tag):
                  if tag == 'td' or tag == 'th':
                      self.in_cell = False
                      self.current_row.append(self.current_cell.strip())
                  elif tag == 'tr':
                      if self.current_row:
                          self.rows.append(self.current_row)
                      self.current_row = []

              def handle_data(self, data):
                  if self.in_cell:
                      self.current_cell += data

          parser = TableParser()
          parser.feed(html)

          cells = []
          for row_idx, row in enumerate(parser.rows):
              cell_row = []
              for col_idx, cell_text in enumerate(row):
                  cell_row.append(PdfCell(
                      text=cell_text,
                      bbox=(0, 0, 0, 0),  # OCR模式无单元格级bbox
                      row_idx=row_idx,
                      col_idx=col_idx
                  ))
              cells.append(cell_row)

          return cells if cells else None

      def _extract_image_for_region(self, src_img_path, bbox, page_num, image_idx, temp_images_dir):
          """裁剪并保存图像区域"""
          try:
              import cv2
              x1, y1, x2, y2 = [int(v) for v in bbox]
              img = cv2.imread(src_img_path)
              if img is None:
                  return None
              cropped = img[y1:y2, x1:x2]
              save_path = os.path.join(temp_images_dir, f"ocr_img_p{page_num}_{image_idx}.png")
              cv2.imwrite(save_path, cropped)
              return PdfImage(
                  page_num=page_num,
                  image_idx=image_idx,
                  image_path=save_path,
                  bbox=(float(x1), float(y1), float(x2), float(y2))
              )
          except Exception as e:
              logger.warning(f"保存图像区域失败: {e}")
              return None

      def _extract_formula_for_region(self, res, bbox):
          """提取公式LaTeX文本"""
          formula_res_list = res.get('formula_res_list', [])
          x1, y1, x2, y2 = bbox

          for formula_res in formula_res_list:
              fbbox = formula_res.get('bbox', [])
              if fbbox and len(fbbox) == 4:
                  # 检查公式是否在指定区域内
                  if (fbbox[0] >= x1 and fbbox[1] >= y1 and
                      fbbox[2] <= x2 and fbbox[3] <= y2):
                      return formula_res.get('latex', '')

          return ''
  ```
- **MIRROR**: `modules/glossary_extractor.py` 的ABC+实现模式，`modules/pdf_extractor.py` 的提取流程
- **IMPORTS**: `paddleocr.PPStructureV3`, `fitz`, `cv2`, `models.text_block.TextBlock`, `models.extraction.*`
- **GOTCHA**:
  - PaddleOCR 3.x 使用 `PPStructureV3`（非2.x的`PPStructure`），`predict()`（非`__call__`）
  - `predict()` 返回迭代器，需遍历获取结果
  - 结果对象用 `.res` 属性获取字典数据
  - bbox 格式为 `[x1, y1, x2, y2]` 像素坐标
  - 延迟初始化pipeline避免import时下载模型
  - 首次运行会自动下载模型（500MB-2GB），需网络畅通
- **VALIDATE**: 创建测试PDF图像，运行 `PaddleOcrExtractor().extract_from_pdf(test_pdf)` 返回 `PdfExtraction`

### Task 3: 创建OCR工厂函数
- **ACTION**: 创建 `modules/ocr/factory.py`
- **IMPLEMENT**:
  ```python
  # modules/ocr/factory.py
  import logging
  from .base import OcrExtractor

  logger = logging.getLogger(__name__)

  def create_ocr_extractor(ocr_type='paddleocr', **kwargs) -> OcrExtractor:
      """创建OCR提取器实例

      Args:
          ocr_type: OCR引擎类型，可选 'paddleocr'
          **kwargs: 传递给提取器的参数

      Returns:
          OcrExtractor: OCR提取器实例

      Raises:
          ValueError: 不支持的OCR引擎类型
      """
      if ocr_type == 'paddleocr':
          from .paddle_extractor import PaddleOcrExtractor
          return PaddleOcrExtractor(**kwargs)
      else:
          raise ValueError(f"不支持的OCR引擎类型: {ocr_type}")
  ```
- **MIRROR**: `modules/glossary_extractor.py` 的 `create_glossary_extractor()` 工厂函数
- **IMPORTS**: `from .base import OcrExtractor`
- **GOTCHA**: Phase 2添加LLM OCR时，在此处添加 `elif ocr_type == 'llm':` 分支
- **VALIDATE**: `create_ocr_extractor('paddleocr')` 返回 `PaddleOcrExtractor` 实例

### Task 4: 扩展Config添加OCR配置
- **ACTION**: 在 `config.py` 的 `Config` 类中添加OCR配置项
- **IMPLEMENT**: 在 `Config` 类的 `USE_TWO_PHASE_MERGE` 配置之后添加：
  ```python
  # OCR配置
  USE_OCR = os.environ.get('USE_OCR', 'false').lower() == 'true'
  OCR_ENGINE = os.environ.get('OCR_ENGINE') or 'paddleocr'
  OCR_LANGUAGE = os.environ.get('OCR_LANGUAGE') or 'ch'
  OCR_USE_GPU = os.environ.get('OCR_USE_GPU', 'true').lower() == 'true'
  OCR_USE_TABLE_RECOGNITION = os.environ.get('OCR_USE_TABLE_RECOGNITION', 'true').lower() == 'true'
  OCR_USE_FORMULA_RECOGNITION = os.environ.get('OCR_USE_FORMULA_RECOGNITION', 'false').lower() == 'true'
  OCR_DPI = int(os.environ.get('OCR_DPI', '200'))
  ```
- **MIRROR**: `config.py` 中 `USE_TWO_PHASE_MERGE` 的 `os.environ.get() + .lower() == 'true'` 模式
- **IMPORTS**: 无新增
- **GOTCHA**: `USE_OCR` 默认为 `false`，不影响现有流程
- **VALIDATE**: `from config import config; print(config.USE_OCR)` 输出 `False`

### Task 5: 修改PdfExtractor添加OCR模式
- **ACTION**: 在 `PdfExtractor` 中添加 `ocr_mode` 参数和OCR分支逻辑
- **IMPLEMENT**:
  1. 修改 `__init__` 签名：
     ```python
     def __init__(self, pdf_path=None, table_extractor='pymupdf', ocr_mode=False, ocr_engine='paddleocr', ocr_lang='ch'):
         # ... 现有代码 ...
         self.ocr_mode = ocr_mode
         self.ocr_engine = ocr_engine
         self.ocr_lang = ocr_lang
         self._ocr_extractor = None
     ```
  2. 添加 `ocr_extractor` 属性（延迟初始化）：
     ```python
     @property
     def ocr_extractor(self):
         if self._ocr_extractor is None and self.ocr_mode:
             from modules.ocr.factory import create_ocr_extractor
             from config import config
             self._ocr_extractor = create_ocr_extractor(
                 self.ocr_engine,
                 lang=self.ocr_lang,
                 use_gpu=config.OCR_USE_GPU,
                 use_table_recognition=config.OCR_USE_TABLE_RECOGNITION,
                 use_formula_recognition=config.OCR_USE_FORMULA_RECOGNITION,
             )
         return self._ocr_extractor
     ```
  3. 在 `extract()` 方法中添加OCR分支（在 `try:` 块内，`with fitz.open()` 之前）：
     ```python
     if self.ocr_mode:
         logger.info(f"OCR模式: 使用 {self.ocr_engine} 提取PDF内容")
         return self.ocr_extractor.extract_from_pdf(
             self.pdf_path, pages=pages, temp_images_dir=temp_images_dir
         )
     ```
- **MIRROR**: `PdfExtractor` 中 `table_extractor` 的策略分发模式
- **IMPORTS**: `from modules.ocr.factory import create_ocr_extractor`
- **GOTCHA**: OCR模式下跳过PyMuPDF文本提取、表格提取、章节提取（扫描版PDF通常无书签），直接返回OCR结果。OCR结果中的表格已由PP-StructureV3识别，无需二次提取。
- **VALIDATE**: `PdfExtractor('test.pdf', ocr_mode=True).extract()` 走OCR路径

### Task 6: 修改TranslationService传递OCR参数
- **ACTION**: 在 `extract_pdf_content()` 和 `process_translation_sync()` 中传递OCR参数
- **IMPLEMENT**:
  1. 修改 `extract_pdf_content` 签名，添加 `ocr_mode=False, ocr_engine='paddleocr', ocr_lang='ch'` 参数
  2. 在创建 `PdfExtractor` 时传递OCR参数：
     ```python
     pdf_extractor = PdfExtractor(
         input_filepath,
         ocr_mode=ocr_mode,
         ocr_engine=ocr_engine,
         ocr_lang=ocr_lang
     )
     ```
  3. 修改 `process_translation_sync` 签名，添加 `ocr_mode=False, ocr_engine='paddleocr', ocr_lang='ch'` 参数
  4. 在调用 `extract_pdf_content` 时传递OCR参数
  5. 修改 `process_translation` 方法签名（Web异步版本），同样添加OCR参数
- **MIRROR**: `semantic_merge`、`use_llm_merging` 参数的传递模式
- **IMPORTS**: 无新增
- **GOTCHA**: `process_translation`（Web异步版）和 `process_translation_sync`（CLI同步版）都需要修改
- **VALIDATE**: `TranslationService.extract_pdf_content(task, path, '', ocr_mode=True)` 走OCR路径

### Task 7: 修改CLI添加--ocr参数
- **ACTION**: 在 `cli.py` 的 translate 子命令中添加 `--ocr` 参数
- **IMPLEMENT**:
  1. 在 `cli.py` 的 `translate_parser.add_argument` 区域添加：
     ```python
     translate_parser.add_argument(
         '--ocr',
         action='store_true',
         help='启用OCR模式提取扫描版PDF内容'
     )
     translate_parser.add_argument(
         '--ocr-engine',
         default='paddleocr',
         choices=['paddleocr'],
         help='OCR引擎类型（默认：paddleocr）'
     )
     translate_parser.add_argument(
         '--ocr-lang',
         default=None,
         help='OCR识别语言（默认：根据源语言自动选择）'
     )
     ```
  2. 在 `cli/translate_command.py` 的 `translate_handler` 中传递OCR参数：
     ```python
     # 确定OCR语言（默认跟随源语言）
     ocr_lang = args.ocr_lang or args.source

     result = translation_service.process_translation_sync(
         ...,
         ocr_mode=args.ocr,
         ocr_engine=args.ocr_engine,
         ocr_lang=ocr_lang,
     )
     ```
  3. 添加OCR模式日志：
     ```python
     if args.ocr:
         progress.log(f"启用OCR模式 (引擎: {args.ocr_engine})")
     ```
- **MIRROR**: `--semantic-merge`、`--llm-merge` 的 `action='store_true'` 模式
- **IMPORTS**: 无新增
- **GOTCHA**: `--ocr-lang` 默认跟随 `--source` 参数，避免用户手动指定OCR语言
- **VALIDATE**: `python cli.py translate test.pdf --ocr --source en --target zh` 无报错

### Task 8: 修改Web界面添加OCR开关
- **ACTION**: 在 `app.py` 和 `templates/index.html` 中添加OCR参数
- **IMPLEMENT**:
  1. 在 `app.py` 的 `translate()` 路由中提取OCR参数：
     ```python
     ocr_mode = request.form.get('ocr_mode', '') == 'on'
     ocr_engine = request.form.get('ocr_engine', 'paddleocr')
     ```
  2. 传递到 `translation_service.process_translation`：
     ```python
     threading.Thread(target=translation_service.process_translation,
         args=(task, input_filepath, source_lang, target_lang, translator_type,
               unique_id, filename, doc_type, glossary, page_range, output_format,
               semantic_merge, use_llm_merging, chapter_split,
               ocr_mode, ocr_engine, source_lang)).start()
     ```
  3. 在 `templates/index.html` 中添加OCR开关（与 `semantic_merge` 并列）：
     ```html
     <div class="form-check">
         <input type="checkbox" id="ocr_mode" name="ocr_mode">
         <label for="ocr_mode">启用OCR提取（扫描版PDF）</label>
     </div>
     ```
- **MIRROR**: `semantic_merge`、`chapter_split` 的复选框模式
- **IMPORTS**: 无新增
- **GOTCHA**: Web端OCR语言默认跟随源语言选择，无需额外UI
- **VALIDATE**: Web界面上传扫描版PDF，勾选OCR，提交翻译

### Task 9: 更新阶段进度配置
- **ACTION**: 在 `models/phase_config.py` 中调整extraction阶段，支持OCR进度
- **IMPLEMENT**: 不修改 `PHASE_CONFIG` 结构（保持现有阶段不变），在OCR提取过程中使用更细粒度的进度消息：
  ```python
  # 在 PaddleOcrExtractor.extract_from_pdf 中：
  # 每页处理完成后更新进度
  task.update_phase_progress('extraction', phase_percent, f'OCR提取第 {page_num} 页...')
  ```
  如果需要更精确的进度，可以在 `PHASE_CONFIG` 中将 extraction 拆分为 `ocr_extraction` 和 `text_extraction`，但这会增加复杂度，建议Phase 1保持简单。
- **MIRROR**: `models/phase_config.py` 中 `extraction` 阶段的进度更新模式
- **IMPORTS**: 无新增
- **GOTCHA**: `PaddleOcrExtractor` 不直接持有 `task` 引用，进度更新需通过回调或返回值实现。Phase 1建议在 `TranslationService.extract_pdf_content()` 中根据OCR模式调整进度消息。
- **VALIDATE**: OCR模式下进度消息显示"OCR提取第X页..."

### Task 10: 更新requirements.txt
- **ACTION**: 添加PaddleOCR依赖（作为可选依赖注释说明）
- **IMPLEMENT**:
  ```
  # OCR支持（可选，扫描版PDF需要）
  # paddleocr>=3.0.0       # PaddleOCR PP-StructureV3
  # paddlepaddle>=3.0.0    # CPU版本
  # paddlepaddle-gpu>=3.0.0  # GPU版本（与CPU版本二选一）
  ```
- **MIRROR**: 现有 `requirements.txt` 的格式
- **IMPORTS**: 无
- **GOTCHA**: PaddleOCR和PaddlePaddle体积大（数百MB），建议作为可选依赖，注释说明安装方式
- **VALIDATE**: `pip install paddleocr paddlepaddle` 成功

### Task 11: 编写OCR模块测试
- **ACTION**: 创建 `tests/test_ocr_extractor.py`
- **IMPLEMENT**:
  ```python
  import pytest
  from unittest.mock import patch, MagicMock
  from modules.ocr.base import OcrExtractor
  from modules.ocr.factory import create_ocr_extractor
  from modules.ocr.paddle_extractor import PaddleOcrExtractor
  from models.extraction import PdfExtraction

  class TestOcrExtractor:
      def test_create_paddle_extractor(self):
          extractor = create_ocr_extractor('paddleocr', lang='en')
          assert isinstance(extractor, PaddleOcrExtractor)
          assert isinstance(extractor, OcrExtractor)

      def test_create_unsupported_extractor(self):
          with pytest.raises(ValueError, match="不支持的OCR引擎类型"):
              create_ocr_extractor('tesseract')

      @patch('modules.ocr.paddle_extractor.PaddleOcrExtractor.pipeline', new_callable=lambda: property)
      def test_extract_from_pdf_mock(self, mock_pipeline):
          """测试OCR提取流程（mock PaddleOCR）"""
          extractor = PaddleOcrExtractor(lang='en')

          # Mock PP-StructureV3 结果
          mock_result = MagicMock()
          mock_result.res = {
              'layout_det_res': {
                  'bboxes': [[10, 10, 200, 50]],
                  'labels': ['text'],
              },
              'ocr_res': {
                  'rec_texts': ['Hello World'],
                  'dt_polys': [[[10, 10], [200, 10], [200, 50], [10, 50]]],
              },
              'table_res_list': [],
              'formula_res_list': [],
          }
          mock_pipeline_instance = MagicMock()
          mock_pipeline_instance.predict.return_value = [mock_result]

          # 测试需要mock fitz.open和pipeline
          # ...详细mock逻辑

      def test_ocr_mode_in_pdf_extractor(self):
          """测试PdfExtractor的OCR模式"""
          from modules.pdf_extractor import PdfExtractor
          extractor = PdfExtractor(ocr_mode=True, ocr_engine='paddleocr')
          assert extractor.ocr_mode is True
          assert extractor.ocr_engine == 'paddleocr'

      def test_ocr_disabled_by_default(self):
          """测试OCR默认关闭"""
          from modules.pdf_extractor import PdfExtractor
          extractor = PdfExtractor()
          assert extractor.ocr_mode is False

  class TestOcrConfig:
      def test_ocr_config_defaults(self):
          from config import Config
          assert Config.USE_OCR is False  # 默认关闭
          assert Config.OCR_ENGINE == 'paddleocr'
          assert Config.OCR_USE_GPU is True
  ```
- **MIRROR**: `tests/test_pdf_extractor.py` 的测试结构
- **IMPORTS**: `pytest`, `unittest.mock`, OCR模块类
- **GOTCHA**: PaddleOCR初始化会下载模型，测试必须mock。使用 `@patch` 替换 `PPStructureV3`。
- **VALIDATE**: `pytest tests/test_ocr_extractor.py -v` 全部通过

### Task 12: 集成测试和回归验证
- **ACTION**: 运行完整测试套件，验证无回归
- **IMPLEMENT**:
  1. 运行现有测试：`pytest tests/ -v`
  2. 验证OCR模式关闭时，现有流程不受影响
  3. 验证OCR模式开启时，扫描版PDF可提取内容
- **MIRROR**: 项目现有测试模式
- **IMPORTS**: 无
- **GOTCHA**: OCR功能为可选依赖，测试需处理 `paddleocr` 未安装的情况（`ImportError` 优雅降级）
- **VALIDATE**: 全部235个现有测试通过 + OCR测试通过

---

## Testing Strategy

### Unit Tests

| Test | Input | Expected Output | Edge Case? |
|---|---|---|---|
| create_ocr_extractor('paddleocr') | paddleocr类型 | PaddleOcrExtractor实例 | No |
| create_ocr_extractor('tesseract') | 不支持类型 | ValueError | Yes |
| PaddleOcrExtractor(lang='en') | 英文语言 | 实例创建成功 | No |
| PdfExtractor(ocr_mode=True) | OCR模式 | ocr_mode=True | No |
| PdfExtractor() | 默认 | ocr_mode=False | No |
| OCR提取文本区域 | mock layout+ocr | TextBlock列表 | No |
| OCR提取表格区域 | mock layout+table | PdfTable列表 | No |
| OCR提取图表区域 | mock layout+image | PdfImage列表 | No |
| OCR空页面 | 无文本区域 | 空PdfPage | Yes |
| OCR配置默认值 | 未设置环境变量 | USE_OCR=False | No |
| PaddleOCR未安装 | import失败 | 优雅降级/报错 | Yes |

### Edge Cases Checklist
- [x] 空输入（无文本的扫描页）
- [x] PaddleOCR未安装时的优雅降级
- [x] GPU不可用时回退到CPU
- [x] 大型PDF（数百页）的内存管理
- [x] OCR提取结果与TextBlock管线的兼容性
- [x] OCR模式下mark_non_body_text逻辑调整
- [x] 表格HTML解析的rowspan/colspan处理

---

## Validation Commands

### Static Analysis
```bash
python -m py_compile modules/ocr/base.py
python -m py_compile modules/ocr/paddle_extractor.py
python -m py_compile modules/ocr/factory.py
```
EXPECT: Zero compilation errors

### Unit Tests
```bash
pytest tests/test_ocr_extractor.py -v
```
EXPECT: All tests pass

### Full Test Suite
```bash
pytest tests/ -v
```
EXPECT: No regressions (all existing tests pass)

### Integration Test (requires PaddleOCR installed)
```bash
python cli.py translate tests/data/scanned_test.pdf --ocr --source en --target zh -f markdown
```
EXPECT: Translated markdown output with OCR-extracted content

### Manual Validation
- [ ] OCR模式关闭时，现有PDF翻译流程不受影响
- [ ] OCR模式开启时，扫描版PDF可提取文字并翻译
- [ ] Web界面OCR开关可正常工作
- [ ] CLI --ocr参数可正常工作
- [ ] OCR提取的表格可正常翻译
- [ ] OCR提取的图表在输出文档中正常显示

---

## Acceptance Criteria
- [ ] All tasks completed
- [ ] All validation commands pass
- [ ] Tests written and passing
- [ ] No type errors
- [ ] No lint errors
- [ ] OCR模式下扫描版PDF可成功提取文字、表格和图表
- [ ] 现有235个测试全部通过（无回归）
- [ ] OCR默认关闭，不影响现有流程

## Completion Checklist
- [x] Code follows discovered patterns (ABC+工厂+策略分发)
- [x] Error handling matches codebase style (ValueError/FileNotFoundError/logger.error)
- [x] Logging follows codebase conventions (logging.getLogger(__name__))
- [x] Tests follow test patterns (pytest + mock)
- [x] No hardcoded values (配置从config.py读取)
- [x] No unnecessary scope additions (LLM OCR留给Phase 2)
- [x] Self-contained — no questions needed during implementation

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| PaddleOCR 3.x API变更 | M | H | 锁定paddleocr>=3.0.0版本，测试覆盖API调用 |
| OCR模式下样式信息缺失 | H | M | TextBlock样式字段设默认值，简化mark_non_body_text逻辑 |
| PaddleOCR安装复杂 | M | M | 提供详细安装文档，OCR为可选依赖 |
| 大型PDF内存溢出 | L | H | 逐页处理，及时释放图像内存 |
| PP-StructureV3表格HTML解析失败 | M | M | 添加HTML解析容错，解析失败时跳过表格 |

## Notes

1. **PaddleOCR 3.x vs 2.x**: 必须使用3.x的 `PPStructureV3` 类，2.x的 `PPStructure` 接口不兼容
2. **延迟初始化**: `PaddleOcrExtractor.pipeline` 使用 `@property` 延迟初始化，避免import时下载模型
3. **OCR语言映射**: 源语言代码（en/zh/ja等）需映射到PaddleOCR的lang参数（ch/en/ja等），大部分可直接对应
4. **mark_non_body_text调整**: OCR模式下通过PP-StructureV3的label直接判断是否为正文（header/footer/page_number标记为非正文），无需依赖字体样式分析
5. **Phase 2扩展点**: `create_ocr_extractor()` 工厂函数已预留扩展，添加 `elif ocr_type == 'llm':` 分支即可
6. **PPDocTranslation发现**: PaddleOCR 3.1.0新增了 `PPDocTranslation` 产线（PP-StructureV3 + ERNIE 4.5），未来可考虑集成，但当前保留自建翻译管线以支持多种翻译引擎
