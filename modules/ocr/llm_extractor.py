# -*- coding: utf-8 -*-
"""LLM视觉模型OCR提取器

通过OpenAI兼容API调用视觉模型（DeepSeek-OCR、Qwen3-VL等），
将PDF页面图像发送给模型，获取文本输出，映射为TextBlock/PdfTable/PdfImage。

支持两种响应格式：
1. JSON格式（通用VLM模型）
2. Markdown/<|ref|>标签格式（DeepSeek-OCR原生格式）
"""

import os
import math
import re
import json
import base64
import logging
import fitz
from openai import OpenAI

from models.text_block import TextBlock
from models.extraction import PdfPage, PdfTable, PdfCell, PdfImage, PdfExtraction
from modules.ocr.base import OcrExtractor
from config import config

logger = logging.getLogger(__name__)

# DeepSeek-OCR 原生 prompt 格式
DEEPSEEK_OCR_PROMPT = "<image>\n<|grounding|>Convert the document to markdown."

# 通用VLM模型的JSON prompt（兼容Qwen3-VL等）
VLM_JSON_SYSTEM_PROMPT = """你是一个专业的文档OCR引擎。分析提供的PDF页面图像，提取所有文字内容、表格和图表信息。

输出严格的JSON格式，结构如下：
{
  "text_blocks": [
    {
      "id": 0,
      "text": "提取的文字内容",
      "bbox": [x1, y1, x2, y2],
      "type": "text|title|section_title|header|footer|footnote",
      "is_body": true
    }
  ],
  "tables": [
    {
      "id": 0,
      "bbox": [x1, y1, x2, y2],
      "html": "<table><tr><td>单元格</td></tr></table>"
    }
  ],
  "images": [
    {
      "id": 0,
      "bbox": [x1, y1, x2, y2],
      "description": "图表简要描述"
    }
  ]
}

规则：
1. bbox坐标为图像像素坐标 [左上x, 左上y, 右下x, 右下y]
2. 按阅读顺序（从上到下、从左到右）排列text_blocks
3. 保持原文内容，不要翻译或修改
4. type为title/section_title时is_body为false
5. type为header/footer/footnote/page_number时is_body为false
6. 如果某类内容为空，对应数组为空列表
7. 仅输出JSON，不要输出其他内容"""


def _is_deepseek_ocr_model(model_name):
    """判断模型是否为DeepSeek-OCR"""
    model_lower = model_name.lower()
    return 'deepseek-ocr' in model_lower


class LlmOcrExtractor(OcrExtractor):
    """基于LLM视觉模型的OCR提取器

    通过OpenAI兼容API调用视觉模型，将PDF页面图像发送给模型，
    获取结构化JSON输出（文本块+坐标+表格+图表），
    映射为现有TextBlock/PdfTable/PdfImage模型。
    """

    def __init__(self, translator_type='aiping', lang='ch', **kwargs):
        """初始化LLM OCR提取器

        Args:
            translator_type (str): 翻译引擎类型，可选 'aiping' 或 'silicon_flow'
            lang (str): OCR识别语言
            **kwargs: 额外参数（预留扩展）
        """
        self.translator_type = translator_type
        self.lang = lang
        self._client = None
        self._model = None

    @property
    def client(self):
        """延迟初始化OpenAI客户端"""
        if self._client is None:
            if self.translator_type == 'aiping':
                self._client = OpenAI(
                    base_url=config.AIPING_API_URL,
                    api_key=config.AIPING_API_KEY,
                    timeout=120.0
                )
                self._model = config.AIPING_OCR_LLM_MODEL
            elif self.translator_type == 'silicon_flow':
                self._client = OpenAI(
                    base_url=config.SILICON_FLOW_API_URL,
                    api_key=config.SILICON_FLOW_API_KEY,
                    timeout=120.0
                )
                self._model = config.SILICON_FLOW_OCR_LLM_MODEL
            else:
                raise ValueError(f"不支持的翻译引擎类型: {self.translator_type}")
        return self._client

    @property
    def model(self):
        """获取模型名称（触发客户端初始化）"""
        if self._model is None:
            _ = self.client  # 触发初始化
        return self._model

    def extract_from_pdf(self, pdf_path, pages=None, temp_images_dir=None):
        """从PDF中提取内容

        Args:
            pdf_path (str): PDF文件路径
            pages (list[int] | None): 页码列表（从1开始），None表示全部
            temp_images_dir (str | None): 临时图像目录

        Returns:
            PdfExtraction: 提取结果
        """
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
            target_pages = pages if pages else list(range(1, total_pages + 1))

            for page_num in target_pages:
                page_idx = page_num - 1
                if page_idx >= total_pages:
                    continue
                page = doc[page_idx]

                # 渲染页面为图像
                pix = page.get_pixmap(dpi=config.OCR_LLM_DPI)
                img_path = os.path.join(temp_images_dir, f"llm_ocr_page_{page_num}.png")
                pix.save(img_path)

                # 获取页面尺寸信息（用于像素坐标转PDF点坐标）
                page_info = {
                    'page_width_pts': page.rect.width,
                    'page_height_pts': page.rect.height,
                    'img_width_px': pix.width,
                    'img_height_px': pix.height,
                }
                logger.info(f"LLM OCR第{page_num}页尺寸: 页面={page_info['page_width_pts']:.1f}x{page_info['page_height_pts']:.1f}pt, 图像={page_info['img_width_px']}x{page_info['img_height_px']}px")

                # 编码为base64
                with open(img_path, 'rb') as f:
                    img_base64 = base64.b64encode(f.read()).decode('utf-8')

                logger.info(f"LLM OCR提取第{page_num}/{total_pages}页")

                # 调用LLM视觉模型
                result = self._extract_page(img_base64, page_num, page_info)

                if result:
                    text_blocks, page_tables, page_images = result
                    pdf_pages.append(PdfPage(
                        page_num=page_num,
                        text_blocks=text_blocks
                    ))
                    pdf_tables.extend(page_tables)
                    pdf_images.extend(page_images)
                else:
                    # 提取失败，添加空页面
                    pdf_pages.append(PdfPage(
                        page_num=page_num,
                        text_blocks=[]
                    ))

        return PdfExtraction(
            total_pages=total_pages,
            pages=pdf_pages,
            tables=pdf_tables,
            images=pdf_images
        )

    def _extract_page(self, img_base64, page_num, page_info=None):
        """调用LLM视觉模型提取单页内容

        Args:
            img_base64 (str): 页面图像的base64编码
            page_num (int): 页码
            page_info (dict | None): 页面尺寸信息，用于坐标转换

        Returns:
            tuple | None: (text_blocks, tables, images) 或 None（失败时）
        """
        try:
            model_name = self.model
            use_deepseek_prompt = _is_deepseek_ocr_model(model_name)

            if use_deepseek_prompt:
                # DeepSeek-OCR 原生格式：prompt放在user消息的文本部分
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": DEEPSEEK_OCR_PROMPT
                            }
                        ]
                    }
                ]
            else:
                # 通用VLM模型：system prompt + user消息
                messages = [
                    {"role": "system", "content": VLM_JSON_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"请提取第{page_num}页PDF中的所有文字、表格和图表信息。"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ]

            response = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=config.OCR_LLM_TEMPERATURE,
                max_tokens=config.OCR_LLM_MAX_TOKENS,
            )

            if not response.choices:
                logger.warning(f"LLM OCR第{page_num}页返回空choices")
                return None
            result_text = response.choices[0].message.content
            logger.info(f"LLM OCR第{page_num}页原始响应(前500字): {result_text[:500]}")
            return self._parse_response(result_text, page_num, page_info)

        except Exception as e:
            logger.error(f"LLM OCR提取第{page_num}页失败: {e}", exc_info=True)
            return None

    def _parse_response(self, result_text, page_num, page_info=None):
        """解析LLM返回的响应为TextBlock/PdfTable/PdfImage

        支持三种响应格式（按优先级）：
        1. JSON格式（通用VLM模型）
        2. <|ref|>...<|/ref|> 标签格式（DeepSeek-OCR grounding输出）
        3. Markdown段落格式（DeepSeek-OCR Markdown输出）

        Args:
            result_text (str): LLM返回的文本
            page_num (int): 页码
            page_info (dict | None): 页面尺寸信息，用于坐标转换

        Returns:
            tuple | None: (text_blocks, tables, images) 或 None（解析失败时）
        """
        # 优先级1: JSON格式
        data = self._extract_json(result_text)
        if data is not None:
            return self._parse_json_response(data, page_num, page_info)

        # 优先级2: <|ref|>...<|/ref|> 标签格式（DeepSeek-OCR grounding输出）
        if '<|ref|>' in result_text and '<|/ref|>' in result_text:
            logger.info(f"第{page_num}页LLM OCR使用<|ref|>标签格式解析")
            return self._parse_ref_tags_response(result_text, page_num, page_info)

        # 优先级3: Markdown段落格式
        text_blocks = self._parse_markdown_response(result_text, page_num)
        if text_blocks:
            logger.info(f"第{page_num}页LLM OCR使用Markdown段落格式解析，共{len(text_blocks)}个文本块")
            return text_blocks, [], []

        logger.warning(f"第{page_num}页LLM OCR结果解析失败，原始响应(前500字): {result_text[:500]}")
        return None

    def _parse_json_response(self, data, page_num, page_info=None):
        """解析JSON格式的响应"""
        text_blocks = []
        tables = []
        images = []

        # 解析文本块
        for item in data.get('text_blocks', []):
            bbox_raw = item.get('bbox', [0, 0, 0, 0])
            # 确保bbox为4个数值
            if len(bbox_raw) < 4:
                bbox_raw = [0, 0, 0, 0]
            try:
                pixel_bbox = tuple(float(v) for v in bbox_raw[:4])
            except (TypeError, ValueError):
                pixel_bbox = (0, 0, 0, 0)

            # 像素坐标转PDF点坐标
            pdf_bbox = self._pixel_to_pdf_coords(pixel_bbox, page_info)

            tb = TextBlock(
                block_no=item.get('id', len(text_blocks)),
                text=item.get('text', ''),
                bbox=pdf_bbox,
                block_type=0,
                page_num=page_num
            )
            # LLM OCR 所有文本块都标记为正文（标题等也需要翻译）
            tb.is_body_text = True

            # 检测纯LaTeX公式并标记
            text_content = item.get('text', '')
            is_formula, cleaned_text = self._detect_formula(text_content)
            if is_formula:
                tb.is_formula = True
                tb.block_text = cleaned_text
                logger.info(f"检测到纯公式文本块: {cleaned_text[:50]}...")

            # 根据bbox估算字体大小（行数法+面积法，取较小值）
            estimated_font_size = self._estimate_font_size(pdf_bbox, text_content)
            if estimated_font_size > 0:
                tb.font_size = estimated_font_size
                logger.info(f"字体大小估算: {tb.font_size:.1f}pt")

            text_blocks.append(tb)

        # 解析表格
        for item in data.get('tables', []):
            html = item.get('html', '')
            if html:
                cells = self._parse_html_table(html)
                if cells:
                    bbox_raw = item.get('bbox', [0, 0, 0, 0])
                    try:
                        pixel_bbox = tuple(float(v) for v in bbox_raw[:4])
                    except (TypeError, ValueError):
                        pixel_bbox = (0, 0, 0, 0)
                    pdf_bbox = self._pixel_to_pdf_coords(pixel_bbox, page_info)
                    tables.append(PdfTable(
                        page_num=page_num,
                        table_idx=len(tables),
                        cells=cells,
                        bbox=pdf_bbox
                    ))

        # 解析图表（LLM OCR无法裁剪图片，仅记录位置）
        for item in data.get('images', []):
            bbox_raw = item.get('bbox', [0, 0, 0, 0])
            try:
                pixel_bbox = tuple(float(v) for v in bbox_raw[:4])
            except (TypeError, ValueError):
                pixel_bbox = (0, 0, 0, 0)
            pdf_bbox = self._pixel_to_pdf_coords(pixel_bbox, page_info)
            images.append(PdfImage(
                page_num=page_num,
                image_idx=len(images),
                image_path='',  # LLM OCR不生成裁剪图片
                bbox=pdf_bbox
            ))

        return text_blocks, tables, images

    def _parse_ref_tags_response(self, result_text, page_num, page_info=None):
        """解析DeepSeek-OCR的<|ref|>标签格式响应

        DeepSeek-OCR的完整格式：
        <|ref|>type<|/ref|><|det|>[[x1, y1, x2, y2]]<|/det|>
        actual text content

        其中type为title/text/image/sub_title等，actual text为实际文本内容。
        坐标为图像像素坐标，需要转换为PDF点坐标。
        """
        text_blocks = []
        images = []

        # 匹配完整块：<|ref|>type<|/ref|><|det|>[[bbox]]<|/det|>\ntext
        # 每个块由 <|ref|>...<|/ref|><|det|>...<|/det|> 和后续文本组成
        block_pattern = re.compile(
            r'<\|ref\|>(.*?)<\|\/ref\|><\|det\|>(.*?)<\|\/det\|>\s*\n?(.*?)(?=<\|ref\||$)',
            re.DOTALL
        )

        for match in block_pattern.finditer(result_text):
            block_type = match.group(1).strip()
            det_content = match.group(2).strip()
            actual_text = match.group(3).strip()

            # 清理Markdown标题前缀（# ## ### 等）
            actual_text = re.sub(r'^#{1,6}\s*', '', actual_text).strip()

            # 从<|det|>提取bbox（归一化坐标 0-999）
            pixel_bbox = self._parse_det_bbox(det_content)

            # 归一化坐标转PDF点坐标（DeepSeek-OCR返回0-999归一化坐标）
            pdf_bbox = self._pixel_to_pdf_coords(pixel_bbox, page_info, is_normalized=True)

            # 跳过空文本（image类型可能没有文本）
            if block_type == 'image':
                images.append(PdfImage(
                    page_num=page_num,
                    image_idx=len(images),
                    image_path='',  # LLM OCR不生成裁剪图片
                    bbox=pdf_bbox
                ))
                continue

            if not actual_text:
                continue

            tb = TextBlock(
                block_no=len(text_blocks),
                text=actual_text,
                bbox=pdf_bbox,
                block_type=0,
                page_num=page_num
            )
            # LLM OCR 所有文本块都标记为正文（标题等也需要翻译）
            tb.is_body_text = True

            # 检测纯LaTeX公式并标记
            is_formula, cleaned_text = self._detect_formula(actual_text)
            if is_formula:
                tb.is_formula = True
                tb.block_text = cleaned_text
                logger.info(f"检测到纯公式文本块: {cleaned_text[:50]}...")

            # 根据bbox和文本行数估算字体大小（行数法+面积法，取较小值）
            estimated_font_size = self._estimate_font_size(pdf_bbox, actual_text)
            if estimated_font_size > 0:
                tb.font_size = estimated_font_size
                logger.info(f"字体大小估算: {tb.font_size:.1f}pt")

            text_blocks.append(tb)

        logger.info(f"第{page_num}页DeepSeek-OCR解析结果: {len(text_blocks)}个文本块, {len(images)}个图像")
        return text_blocks, [], images

    def _parse_det_bbox(self, det_content):
        """从<|det|>标签内容提取bbox坐标

        det_content格式: [[x1, y1, x2, y2]]
        """
        try:
            coords = re.findall(r'[\d.]+', det_content)
            if len(coords) >= 4:
                return tuple(float(c) for c in coords[:4])
        except (ValueError, TypeError):
            pass
        return (0, 0, 0, 0)

    def _detect_formula(self, text):
        """检测文本是否为纯LaTeX公式，并返回清理后的LaTeX

        检测规则：文本整体被公式定界符包裹（$...$、$$...$$、\(...\)、\[...\]）
        混合文本（说明文字+公式）不标记为公式。

        Args:
            text: 待检测的文本

        Returns:
            tuple: (is_formula, cleaned_text)
                is_formula: 是否为纯公式
                cleaned_text: 如果是公式，去除定界符后的纯LaTeX；否则返回原文本
        """
        if not text or not text.strip():
            return False, text

        stripped = text.strip()

        # 检测 $$...$$ （独立行公式，优先匹配避免被 $...$ 误匹配）
        if stripped.startswith('$$') and stripped.endswith('$$') and len(stripped) > 4:
            return True, stripped[2:-2].strip()

        # 检测 $...$ （行内公式）
        if stripped.startswith('$') and stripped.endswith('$') and not stripped.startswith('$$') and len(stripped) > 2:
            return True, stripped[1:-1].strip()

        # 检测 \(...\) （LaTeX行内公式）
        if stripped.startswith('\\(') and stripped.endswith('\\)') and len(stripped) > 4:
            return True, stripped[2:-2].strip()

        # 检测 \[...\] （LaTeX独立行公式）
        if stripped.startswith('\\[') and stripped.endswith('\\]') and len(stripped) > 4:
            return True, stripped[2:-2].strip()

        return False, text

    @staticmethod
    def _estimate_font_size(pdf_bbox, text):
        """根据 bbox 和文本内容估算字体大小

        使用行数法和面积法，取较小值。结果范围 [6, 36] pt。

        Args:
            pdf_bbox: (x1, y1, x2, y2) PDF点坐标
            text: 文本内容

        Returns:
            float: 估算的字体大小（pt），估算失败返回 0
        """
        if not pdf_bbox or pdf_bbox == (0, 0, 0, 0):
            return 0
        bbox_height = pdf_bbox[3] - pdf_bbox[1]
        if bbox_height <= 0:
            return 0
        num_lines = max(1, text.count('\n') + 1)
        font_size_by_lines = bbox_height / num_lines * 0.75
        bbox_width = pdf_bbox[2] - pdf_bbox[0]
        text_length = len(text.replace('\n', ''))
        if text_length > 0 and bbox_width > 0:
            font_size_by_area = math.sqrt(bbox_width * bbox_height / (text_length * 0.66))
        else:
            font_size_by_area = font_size_by_lines
        return max(6, min(font_size_by_lines, font_size_by_area, 36))

    def _pixel_to_pdf_coords(self, bbox, page_info, is_normalized=False):
        """将坐标转换为PDF点坐标

        Args:
            bbox: (x1, y1, x2, y2) 坐标
            page_info: 包含页面尺寸信息的字典，或None
            is_normalized: 是否为归一化坐标(0-999)，DeepSeek-OCR返回的是归一化坐标

        Returns:
            tuple: (x1, y1, x2, y2) PDF点坐标
        """
        if not page_info or bbox == (0, 0, 0, 0):
            return bbox

        page_width = page_info.get('page_width_pts', 0)
        page_height = page_info.get('page_height_pts', 0)

        if page_width <= 0 or page_height <= 0:
            return bbox

        x1, y1, x2, y2 = bbox

        if is_normalized:
            # DeepSeek-OCR 归一化坐标 (0-999) -> PDF 点坐标
            return (x1 / 999 * page_width, y1 / 999 * page_height,
                    x2 / 999 * page_width, y2 / 999 * page_height)
        else:
            # 像素坐标 -> PDF 点坐标
            img_width = page_info.get('img_width_px', 0)
            img_height = page_info.get('img_height_px', 0)
            if img_width <= 0 or img_height <= 0:
                return bbox
            scale_x = page_width / img_width
            scale_y = page_height / img_height
            return (x1 * scale_x, y1 * scale_y, x2 * scale_x, y2 * scale_y)

    def _parse_markdown_response(self, result_text, page_num):
        """解析Markdown段落格式的响应

        按空行分割段落，过滤空段落和纯格式行。
        """
        text_blocks = []
        # 按空行分割段落
        paragraphs = re.split(r'\n\s*\n', result_text)
        for idx, para in enumerate(paragraphs):
            para = para.strip()
            if not para:
                continue
            # 跳过纯格式行（如仅包含#、-、|等）
            stripped = para.lstrip('#').lstrip('-').lstrip('|').strip()
            if not stripped:
                continue
            tb = TextBlock(
                block_no=idx,
                text=para,
                bbox=(0, 0, 0, 0),
                block_type=0,
                page_num=page_num
            )
            # LLM OCR 所有文本块都标记为正文（标题等也需要翻译）
            tb.is_body_text = True
            text_blocks.append(tb)
        return text_blocks

    def _extract_json(self, text):
        """从LLM响应中提取JSON（三级容错）

        Args:
            text (str): LLM返回的原始文本

        Returns:
            dict | None: 解析后的JSON字典，或None
        """
        # 1. 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 2. 尝试从markdown代码块中提取
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # 3. 尝试找到第一个 { 和最后一个 } 之间的内容
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

        return None

    def _parse_html_table(self, html):
        """解析HTML表格为PdfCell二维列表

        复用PaddleOcrExtractor中的_TableHtmlParser。

        Args:
            html (str): HTML表格字符串

        Returns:
            list[list[PdfCell]] | None: 二维单元格列表，或None
        """
        from modules.ocr.paddle_extractor import _TableHtmlParser

        parser = _TableHtmlParser()
        parser.feed(html)

        cells = []
        for row_idx, row in enumerate(parser.rows):
            cell_row = []
            col_idx = 0
            for cell_text, rowspan, colspan in row:
                cell_row.append(PdfCell(
                    text=cell_text,
                    bbox=(0, 0, 0, 0),  # OCR模式无单元格级bbox
                    row_idx=row_idx,
                    col_idx=col_idx,
                    row_span=rowspan,
                    col_span=colspan
                ))
                col_idx += colspan
            cells.append(cell_row)

        return cells if cells else None
