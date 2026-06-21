# -*- coding: utf-8 -*-
from __future__ import annotations

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
from dataclasses import dataclass, field
from openai import OpenAI

from models.text_block import TextBlock
from models.extraction import PdfPage, PdfTable, PdfCell, PdfImage, PdfExtraction
from modules.ocr.base import OcrExtractor
from config import config
from utils.text_processing import fix_line_break_hyphens

# 模块级常量
TABLE_HTML_MARKER = '<table'

logger = logging.getLogger(__name__)


@dataclass
class OcrBlock:
    """OCR解析中间数据类，统一JSON/ref/Markdown三种格式的解析输出"""
    text: str = ''
    bbox: tuple = (0, 0, 0, 0)
    block_type: str = 'text'  # title, sub_title, text, header, footer, footnote, image
    is_image: bool = False
    table_html: str | None = None
    bboxes: list = field(default_factory=list)  # 多bbox场景


# block_type → (is_body_text, block_type_int) 映射
# block_type_int: 0=正文, 1=标题, 2=副标题, 3=页眉, 4=页脚, 5=脚注
BLOCK_TYPE_MAP = {
    'title': (False, 1),
    'sub_title': (False, 1),
    'section_title': (False, 1),
    'header': (False, 3),
    'footer': (False, 4),
    'footnote': (False, 5),
    'page_number': (False, 4),
    'text': (True, 0),
    'image': (True, 0),  # image类型不创建TextBlock，这里只是占位
}


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


def _estimate_text_display_width(text, font_size=9.0):
    """估算文本的显示宽度：CJK字符宽度=font_size×1.0，ASCII字符宽度=font_size×0.6"""
    width = 0.0
    for ch in text:
        if ('\u4e00' <= ch <= '\u9fff' or '\u3000' <= ch <= '\u303f' or '\uff00' <= ch <= '\uffef'
                or '\u3040' <= ch <= '\u309f' or '\u30a0' <= ch <= '\u30ff'  # Japanese Hiragana/Katakana
                or '\uac00' <= ch <= '\ud7af'):  # Korean Hangul
            width += font_size * 1.0
        else:
            width += font_size * 0.6
    return width


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

    def extract_from_pdf(self, pdf_path, pages=None, temp_images_dir=None, progress_callback=None):
        """从PDF中提取内容

        Args:
            pdf_path (str): PDF文件路径
            pages (list[int] | None): 页码列表（从1开始），None表示全部
            temp_images_dir (str | None): 临时图像目录
            progress_callback (callable | None): 进度回调函数，签名 (msg_type, payload)

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
            n_target = len(target_pages)

            # 发送步骤开始回调
            if progress_callback:
                progress_callback('step_start', {
                    'step': 1,
                    'step_name': 'LLM OCR提取',
                    'total_pages': n_target,
                    'pages_done': 0,
                })

            pages_done = 0
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
                result = self._extract_page(img_base64, page_num, page_info, page=page, temp_images_dir=temp_images_dir)

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

                # 更新进度
                pages_done += 1
                if progress_callback:
                    progress_callback('step_progress', {
                        'step': 1,
                        'step_name': 'LLM OCR提取',
                        'total_pages': n_target,
                        'pages_done': pages_done,
                    })

            # 发送步骤完成回调
            if progress_callback:
                progress_callback('step_complete', {
                    'step': 1,
                    'step_name': 'LLM OCR提取',
                    'total_pages': n_target,
                    'pages_done': pages_done,
                })

        return PdfExtraction(
            total_pages=total_pages,
            pages=pdf_pages,
            tables=pdf_tables,
            images=pdf_images
        )

    def _extract_page(self, img_base64, page_num, page_info=None, page=None, temp_images_dir=None):
        """调用LLM视觉模型提取单页内容

        Args:
            img_base64 (str): 页面图像的base64编码
            page_num (int): 页码
            page_info (dict | None): 页面尺寸信息，用于坐标转换
            page (fitz.Page | None): fitz页面对象，用于图像裁剪
            temp_images_dir (str | None): 临时图像保存目录

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
            return self._parse_response(result_text, page_num, page_info, page=page, temp_images_dir=temp_images_dir)

        except Exception as e:
            logger.error(f"LLM OCR提取第{page_num}页失败: {e}", exc_info=True)
            return None

    def _parse_response(self, result_text, page_num, page_info=None, page=None, temp_images_dir=None):
        """解析LLM返回的响应为TextBlock/PdfTable/PdfImage

        三阶段管道：格式检测 → 结构化解析(OcrBlock) → 模型映射

        格式检测优先级（带回退）：
        1. <|ref|>标签格式（DeepSeek-OCR grounding输出）
        2. JSON格式（通用VLM模型，仅严格匹配）
        3. Markdown段落格式（回退）

        当高优先级格式解析返回空结果时，自动回退到下一优先级格式。
        """
        # 阶段1: 格式检测（带回退）
        has_ref_tags = '<|ref|>' in result_text and '<|/ref|>' in result_text
        ocr_blocks = None

        if has_ref_tags:
            logger.info(f"第{page_num}页LLM OCR使用<|ref|>标签格式解析")
            ocr_blocks = self._parse_ref_tags_to_blocks(result_text)

        # <|ref|>标签未命中或返回空结果，尝试JSON
        json_parsed = False
        if not ocr_blocks:
            data = self._extract_json(result_text)
            if data is not None:
                logger.info(f"第{page_num}页LLM OCR使用JSON格式解析")
                ocr_blocks = self._parse_json_to_blocks(data)
                json_parsed = True

        # JSON未命中时才尝试Markdown（JSON成功解析但内容为空不应fallback）
        if not json_parsed and not ocr_blocks:
            logger.info(f"第{page_num}页LLM OCR使用Markdown段落格式解析")
            ocr_blocks = self._parse_markdown_to_blocks(result_text)

        if not ocr_blocks:
            logger.warning(f"第{page_num}页LLM OCR结果解析失败，原始响应(前500字): {result_text[:500]}")
            return None

        # 阶段2: 模型映射
        return self._map_ocr_blocks_to_models(ocr_blocks, page_num, page_info, page=page, temp_images_dir=temp_images_dir)

    def _extract_json(self, text):
        """从LLM响应中提取JSON（两级容错）

        Args:
            text (str): LLM返回的原始文本

        Returns:
            dict | None: 解析后的JSON字典，或None
        """
        # 1. 尝试直接解析（仅当文本以{开头时）
        stripped = text.strip()
        if stripped.startswith('{'):
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

    def _create_text_block(self, ocr_block, page_num, page_info=None):
        """从OcrBlock创建TextBlock，统一处理公式检测、字体估算、坐标转换"""
        is_body, block_type_int = BLOCK_TYPE_MAP.get(
            ocr_block.block_type, (True, 0)
        )

        pdf_bbox = self._pixel_to_pdf_coords(
            ocr_block.bbox, page_info, is_normalized=True
        )

        tb = TextBlock(
            block_no=0,  # 将在映射阶段统一编号
            text=ocr_block.text,
            bbox=pdf_bbox,
            block_type=block_type_int,
            page_num=page_num
        )
        tb.is_body_text = is_body

        # 检测纯LaTeX公式并标记
        is_formula, cleaned_text = self._detect_formula(ocr_block.text)
        if is_formula:
            tb.is_formula = True
            tb.block_text = cleaned_text

        # 估算字体大小
        estimated_font_size = self._estimate_font_size(pdf_bbox, ocr_block.text)
        if estimated_font_size > 0:
            tb.font_size = estimated_font_size

        return tb

    def _parse_ref_tags_to_blocks(self, result_text):
        """将DeepSeek-OCR的<|ref|>标签格式响应解析为OcrBlock列表

        分步解析：
        1. 提取所有<|ref|>...<|/ref|><|det|>...<|/det|>标注对及其位置
        2. 根据位置区间提取标注对之间的文本内容
        3. 组合为OcrBlock列表
        """
        ocr_blocks = []

        # 第一步：提取所有标注对及其位置
        tag_pattern = re.compile(
            r'<\|ref\|>(.*?)<\|/ref\|><\|det\|>(.*?)<\|/det\|>'
        )

        tags = []
        for match in tag_pattern.finditer(result_text):
            tags.append({
                'block_type': match.group(1).strip(),
                'det_content': match.group(2).strip(),
                'start': match.start(),
                'end': match.end(),
            })

        if not tags:
            return []

        # 第二步：提取标注对之间的文本
        for i, tag in enumerate(tags):
            # 文本从当前标注对结束到下一个标注对开始
            text_start = tag['end']
            text_end = tags[i + 1]['start'] if i + 1 < len(tags) else len(result_text)
            actual_text = result_text[text_start:text_end].strip()

            # 清理Markdown标题前缀
            actual_text = re.sub(r'^#{1,6}\s*', '', actual_text).strip()

            # 修复换行断词连字符
            actual_text = fix_line_break_hyphens(actual_text)

            # 从<|det|>提取bbox
            bboxes = self._parse_det_bboxes(tag['det_content'])
            primary_bbox = bboxes[0] if bboxes else (0, 0, 0, 0)

            block_type = tag['block_type']

            # 检测HTML表格
            table_html = None
            if TABLE_HTML_MARKER in actual_text.lower():
                table_match = re.search(r'<table[^>]*>.*?</table>', actual_text, re.DOTALL | re.IGNORECASE)
                if table_match:
                    table_html = table_match.group(0)

            # 多bbox拆分：当1个ref标签包含多个det坐标时，按段落拆分文本
            if len(bboxes) > 1 and block_type != 'image':
                # 优先按双换行拆分，其次按单换行拆分
                if '\n\n' in actual_text:
                    paragraphs = [p.strip() for p in actual_text.split('\n\n') if p.strip()]
                elif '\n' in actual_text:
                    paragraphs = [p.strip() for p in actual_text.split('\n') if p.strip()]
                else:
                    paragraphs = [actual_text]
                if len(paragraphs) == len(bboxes):
                    for j, paragraph in enumerate(paragraphs):
                        ocr_blocks.append(OcrBlock(
                            text=paragraph,
                            bbox=bboxes[j],
                            block_type=block_type,
                            is_image=False,
                            table_html=None,
                            bboxes=[bboxes[j]],
                        ))
                    continue
                elif len(paragraphs) < len(bboxes):
                    # 段落数不足：用空字符串填充至与bbox数量一致
                    paragraphs = paragraphs + [''] * (len(bboxes) - len(paragraphs))
                    for j, paragraph in enumerate(paragraphs):
                        ocr_blocks.append(OcrBlock(
                            text=paragraph,
                            bbox=bboxes[j],
                            block_type=block_type,
                            is_image=False,
                            table_html=None,
                            bboxes=[bboxes[j]],
                        ))
                    continue
                else:
                    # 段落数过多：将多余段落合并到最后一个
                    merged = paragraphs[:len(bboxes) - 1] + ['\n'.join(paragraphs[len(bboxes) - 1:])]
                    for j, paragraph in enumerate(merged):
                        ocr_blocks.append(OcrBlock(
                            text=paragraph,
                            bbox=bboxes[j],
                            block_type=block_type,
                            is_image=False,
                            table_html=None,
                            bboxes=[bboxes[j]],
                        ))
                    continue

            ocr_blocks.append(OcrBlock(
                text=actual_text,
                bbox=primary_bbox,
                block_type=block_type,
                is_image=(block_type == 'image'),
                table_html=table_html,
                bboxes=bboxes,
            ))

        return ocr_blocks

    def _parse_json_to_blocks(self, data):
        """将JSON格式的响应解析为OcrBlock列表"""
        ocr_blocks = []

        for item in data.get('text_blocks', []):
            text_content = item.get('text', '')
            text_content = fix_line_break_hyphens(text_content)

            # 跳过包含HTML表格的文本块
            if TABLE_HTML_MARKER in text_content.lower():
                continue

            bbox_raw = item.get('bbox', [0, 0, 0, 0])
            if len(bbox_raw) < 4:
                bbox_raw = [0, 0, 0, 0]
            try:
                pixel_bbox = tuple(float(v) for v in bbox_raw[:4])
            except (TypeError, ValueError):
                pixel_bbox = (0, 0, 0, 0)

            block_type = item.get('type', 'text')

            ocr_blocks.append(OcrBlock(
                text=text_content,
                bbox=pixel_bbox,
                block_type=block_type,
                is_image=False,
                table_html=None,
                bboxes=[pixel_bbox],
            ))

        # 表格
        for item in data.get('tables', []):
            html = item.get('html', '')
            if html:
                bbox_raw = item.get('bbox', [0, 0, 0, 0])
                try:
                    pixel_bbox = tuple(float(v) for v in bbox_raw[:4])
                except (TypeError, ValueError):
                    pixel_bbox = (0, 0, 0, 0)

                ocr_blocks.append(OcrBlock(
                    text='',
                    bbox=pixel_bbox,
                    block_type='table',
                    is_image=False,
                    table_html=html,
                    bboxes=[pixel_bbox],
                ))

        # 图像
        for item in data.get('images', []):
            bbox_raw = item.get('bbox', [0, 0, 0, 0])
            try:
                pixel_bbox = tuple(float(v) for v in bbox_raw[:4])
            except (TypeError, ValueError):
                pixel_bbox = (0, 0, 0, 0)

            ocr_blocks.append(OcrBlock(
                text='',
                bbox=pixel_bbox,
                block_type='image',
                is_image=True,
                table_html=None,
                bboxes=[pixel_bbox],
            ))

        return ocr_blocks

    def _parse_markdown_to_blocks(self, result_text):
        """将Markdown段落格式的响应解析为OcrBlock列表"""
        ocr_blocks = []
        paragraphs = re.split(r'\n\s*\n', result_text)

        for para in paragraphs:
            para = para.strip()
            para = fix_line_break_hyphens(para)
            if not para:
                continue
            stripped = para.lstrip('#').lstrip('-').lstrip('|').strip()
            if not stripped:
                continue

            # 检测Markdown标题层级
            block_type = 'text'
            heading_match = re.match(r'^(#{1,6})\s+', para)
            if heading_match:
                level = len(heading_match.group(1))
                block_type = 'title' if level <= 2 else 'sub_title'

            # 跳过包含HTML表格的段落
            if TABLE_HTML_MARKER in para.lower():
                table_match = re.search(r'<table[^>]*>.*?</table>', para, re.DOTALL | re.IGNORECASE)
                if table_match:
                    ocr_blocks.append(OcrBlock(
                        text='',
                        bbox=(0, 0, 0, 0),
                        block_type='table',
                        is_image=False,
                        table_html=table_match.group(0),
                        bboxes=[],
                    ))
                continue

            ocr_blocks.append(OcrBlock(
                text=para,
                bbox=(0, 0, 0, 0),
                block_type=block_type,
                is_image=False,
                table_html=None,
                bboxes=[],
            ))

        return ocr_blocks

    def _map_ocr_blocks_to_models(self, ocr_blocks, page_num, page_info=None, page=None, temp_images_dir=None):
        """将OcrBlock列表统一映射为TextBlock/PdfTable/PdfImage

        Args:
            ocr_blocks: OcrBlock列表
            page_num: 页码
            page_info: 页面尺寸信息
            page: fitz.Page对象，用于图像裁剪
            temp_images_dir: 临时图像保存目录

        Returns:
            tuple: (text_blocks, tables, images)
        """
        text_blocks = []
        tables = []
        images = []
        text_block_no = 0
        image_idx = 0

        for block in ocr_blocks:
            # 图像类型
            if block.is_image:
                pdf_bbox = self._pixel_to_pdf_coords(block.bbox, page_info, is_normalized=True)
                image_path = ''
                if page and temp_images_dir:
                    image_path = self._crop_and_save_image(page, pdf_bbox, page_num, image_idx, temp_images_dir)
                images.append(PdfImage(
                    page_num=page_num,
                    image_idx=image_idx,
                    image_path=image_path,
                    bbox=pdf_bbox
                ))
                image_idx += 1
                continue

            # 表格类型
            if block.table_html:
                pdf_bbox = self._pixel_to_pdf_coords(block.bbox, page_info, is_normalized=True)
                cells, row_heights, col_widths = self._parse_html_table(block.table_html, table_bbox=pdf_bbox)
                if cells is not None:
                    # 根据实际行数更新bbox高度
                    if row_heights:
                        actual_height = sum(row_heights)
                        pdf_bbox = (pdf_bbox[0], pdf_bbox[1], pdf_bbox[2], pdf_bbox[1] + actual_height)
                    tables.append(PdfTable(
                        page_num=page_num,
                        table_idx=len(tables),
                        cells=cells,
                        bbox=pdf_bbox,
                        row_heights=row_heights,
                        col_widths=col_widths
                    ))
                    logger.info(f"OcrBlock表格映射: {len(cells)}行, bbox={pdf_bbox}")
                continue

            # 文本类型
            if not block.text:
                continue

            tb = self._create_text_block(block, page_num, page_info)
            tb.block_no = text_block_no
            text_block_no += 1
            text_blocks.append(tb)

        logger.info(f"第{page_num}页OcrBlock映射结果: {len(text_blocks)}个文本块, {len(tables)}个表格, {len(images)}个图像")
        return text_blocks, tables, images

    def _crop_and_save_image(self, page, pdf_bbox, page_num, image_idx, temp_images_dir):
        """从PDF页面裁剪图像区域并保存

        Args:
            page: fitz.Page 对象
            pdf_bbox: (x1, y1, x2, y2) PDF点坐标
            page_num: 页码
            image_idx: 图像索引
            temp_images_dir: 临时图像保存目录

        Returns:
            str: 保存的图像文件路径，失败返回空字符串
        """
        try:
            if not pdf_bbox or pdf_bbox == (0, 0, 0, 0):
                return ''

            rect = fitz.Rect(pdf_bbox)
            # 确保rect在页面范围内
            rect = rect & page.rect
            if rect.is_empty:
                logger.warning(f"图像裁剪区域为空: bbox={pdf_bbox}")
                return ''

            pix = page.get_pixmap(clip=rect, dpi=150)
            save_path = os.path.join(temp_images_dir, f"ocr_img_p{page_num}_{image_idx}.png")
            pix.save(save_path)
            logger.info(f"图像裁剪保存: {save_path}, bbox={pdf_bbox}")
            return save_path
        except Exception as e:
            logger.error(f"图像裁剪保存失败: {e}", exc_info=True)
            return ''

    def _parse_det_bboxes(self, det_content):
        """从<|det|>标签内容提取所有bbox坐标组

        det_content格式: [[x1, y1, x2, y2], [x1, y1, x2, y2], ...]
        返回所有bbox的列表，每个bbox为(x1, y1, x2, y2)元组。
        解析失败时返回 [(0, 0, 0, 0)]。
        """
        try:
            # 支持负数、小数、科学计数法
            pattern = r'\[(-?[\d.]+(?:[eE][+-]?\d+)?)\s*,\s*(-?[\d.]+(?:[eE][+-]?\d+)?)\s*,\s*(-?[\d.]+(?:[eE][+-]?\d+)?)\s*,\s*(-?[\d.]+(?:[eE][+-]?\d+)?)\]'
            matches = re.findall(pattern, det_content)
            if matches:
                return [tuple(float(c) for c in m) for m in matches]
        except (ValueError, TypeError):
            pass
        return [(0, 0, 0, 0)]

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
            # 越界钳位
            x1 = max(0, min(x1, 999))
            y1 = max(0, min(y1, 999))
            x2 = max(0, min(x2, 999))
            y2 = max(0, min(y2, 999))
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

    def _detect_formula(self, text):
        """检测文本是否为纯LaTeX公式，并返回清理后的LaTeX

        检测规则：
        1. 文本整体被公式定界符包裹（$...$、$$...$$、\\(...\\)、\\[...\\]）
        2. 文本整体被LaTeX数学环境包裹（\\begin{env}...\\end{env}）
        混合文本（说明文字+公式）不标记为公式。

        Args:
            text: 待检测的文本

        Returns:
            tuple: (is_formula, cleaned_text)
                is_formula: 是否为纯公式
                cleaned_text: 如果是公式，去除定界符或环境包裹后的纯LaTeX；否则返回原文本
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

        # 检测 LaTeX 数学环境（\begin{env}...\end{env}）
        _MATH_ENVS = frozenset({
            'aligned', 'gathered', 'cases',
            'equation', 'equation*',
            'align', 'align*',
            'gather', 'gather*',
            'matrix', 'pmatrix', 'bmatrix', 'vmatrix',
        })
        for env_name in _MATH_ENVS:
            begin_tag = f'\\begin{{{env_name}}}'
            end_tag = f'\\end{{{env_name}}}'
            if stripped.startswith(begin_tag) and stripped.endswith(end_tag) and len(stripped) > len(begin_tag) + len(end_tag):
                inner = stripped[len(begin_tag):-len(end_tag)].strip()
                return True, inner

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

    @staticmethod
    def _compute_table_layout(matrix, n_rows, n_cols, table_bbox):
        """根据内容权重和行高优先迭代优化计算表格列宽和行高

        算法流程：
        1. 预计算所有单元格的显示宽度
        2. 假设等宽列，初始估算每行行数和行高
        3. 钳位行高到原始bbox
        4. 迭代优化：从行高推导列宽 → 重新估算行高 → 钳位 → 检查收敛

        Args:
            matrix: 单元格二维矩阵
            n_rows: 行数
            n_cols: 列数
            table_bbox: 表格边界框 (x0, y0, x1, y1)

        Returns:
            tuple: (col_widths, row_heights, t_x0, t_y0) 列宽列表、行高列表、表格左上角坐标

        Side Effects:
            Modifies the `estimated_lines` attribute of PdfCell objects in the
            passed `matrix` parameter based on computed layout.
        """
        t_x0, t_y0, t_x1, t_y1 = table_bbox
        table_width = t_x1 - t_x0
        table_height = t_y1 - t_y0

        font_size = 9.0
        single_line_height = font_size * 1.2
        min_col_ratio = 0.1
        max_col_ratio = 0.5
        max_iterations = 3
        convergence_threshold = 0.5

        # 预计算所有单元格的显示宽度
        cell_display_widths = {}  # (r, c) -> display_width
        for r in range(n_rows):
            for c in range(n_cols):
                cell = matrix[r][c]
                if cell is not None and cell.text:
                    cell_display_widths[(r, c)] = _estimate_text_display_width(cell.text, font_size)

        # Step 1: 初始行高估算（假设等宽列）
        equal_col_width = table_width / n_cols
        row_heights = []
        for r in range(n_rows):
            max_lines = 1
            for c in range(n_cols):
                cell = matrix[r][c]
                if cell is not None and cell.text:
                    display_w = cell_display_widths.get((r, c), 0)
                    span_width = equal_col_width * cell.col_span
                    lines = max(1, math.ceil(display_w / span_width)) if span_width > 0 else 1
                    max_lines = max(max_lines, lines)
            row_heights.append(max_lines * single_line_height)

        # Step 2: 钳位行高到原始bbox
        new_total_height = sum(row_heights)
        if new_total_height > 0:
            scale = table_height / new_total_height
            row_heights = [rh * scale for rh in row_heights]

        # 迭代优化：从行高推导列宽，再重新估算行高
        col_widths = [table_width / n_cols] * n_cols
        prev_row_heights = row_heights[:]

        for iteration in range(max_iterations):
            # Step 3: 从钳位后的行高推导列宽
            col_weights = [0.0] * n_cols
            for r in range(n_rows):
                available_lines = max(1, round(row_heights[r] / single_line_height))
                for c in range(n_cols):
                    cell = matrix[r][c]
                    if cell is not None and cell.text:
                        display_w = cell_display_widths.get((r, c), 0)
                        # 在可用行数内适配文本所需的最小列宽
                        min_width = display_w / available_lines if available_lines > 0 else display_w
                        for dc in range(cell.col_span):
                            if c + dc < n_cols:
                                col_weights[c + dc] = max(col_weights[c + dc], min_width / cell.col_span)

            total_weight = sum(col_weights)
            if total_weight > 0:
                col_widths = [table_width * (w / total_weight) for w in col_weights]
            else:
                col_widths = [table_width / n_cols] * n_cols

            # 钳位列宽：最小10%，最大50%
            min_cw = table_width * min_col_ratio
            max_cw = table_width * max_col_ratio
            for _ in range(n_cols):
                clamped = [False] * n_cols
                for c in range(n_cols):
                    if col_widths[c] > max_cw:
                        col_widths[c] = max_cw
                        clamped[c] = True
                    elif col_widths[c] < min_cw:
                        col_widths[c] = min_cw
                        clamped[c] = True
                clamped_total = sum(col_widths[c] for c in range(n_cols) if clamped[c])
                unclamped_total = sum(col_widths[c] for c in range(n_cols) if not clamped[c])
                target_unclamped = table_width - clamped_total
                if unclamped_total > 0 and abs(unclamped_total - target_unclamped) > 0.01:
                    scale = target_unclamped / unclamped_total
                    for c in range(n_cols):
                        if not clamped[c]:
                            col_widths[c] *= scale
                all_ok = all(min_cw - 0.01 <= col_widths[c] <= max_cw + 0.01 for c in range(n_cols))
                if all_ok:
                    break

            # Step 4: 用新列宽重新估算行高
            row_heights = []
            row_line_counts = []
            for r in range(n_rows):
                max_lines = 1
                for c in range(n_cols):
                    cell = matrix[r][c]
                    if cell is not None and cell.text:
                        display_w = cell_display_widths.get((r, c), 0)
                        span_width = sum(col_widths[c + dc] for dc in range(cell.col_span) if c + dc < n_cols)
                        lines = max(1, math.ceil(display_w / span_width)) if span_width > 0 else 1
                        max_lines = max(max_lines, lines)
                row_line_counts.append(max_lines)
                row_heights.append(max_lines * single_line_height)

            # Step 5: 重新钳位行高到原始bbox
            new_total_height = sum(row_heights)
            if new_total_height > 0:
                scale = table_height / new_total_height
                row_heights = [rh * scale for rh in row_heights]

            # Step 6: 检查收敛
            max_change = max(abs(row_heights[r] - prev_row_heights[r]) for r in range(n_rows))
            if max_change < convergence_threshold:
                break
            prev_row_heights = row_heights[:]

        # 保存每个单元格的 estimated_lines
        for r in range(n_rows):
            for c in range(n_cols):
                cell = matrix[r][c]
                if cell is not None:
                    if cell.text:
                        display_w = cell_display_widths.get((r, c), 0)
                        span_width = sum(col_widths[cell.col_idx + dc] for dc in range(cell.col_span) if cell.col_idx + dc < n_cols)
                        lines = max(1, math.ceil(display_w / span_width)) if span_width > 0 else 1
                        cell.estimated_lines = lines
                    else:
                        cell.estimated_lines = 0

        return col_widths, row_heights, t_x0, t_y0

    def _parse_html_table(self, html, table_bbox=None):
        """解析HTML表格为PdfCell二维列表，并计算单元格坐标和行列尺寸

        复用PaddleOcrExtractor中的_TableHtmlParser。
        使用 occupied 矩阵展开合并单元格，生成规整的 n_rows x n_cols 矩阵，
        被合并覆盖的位置放置 None。

        Args:
            html (str): HTML表格字符串
            table_bbox (tuple | None): 表格级 bbox (x0, y0, x1, y2)，用于计算单元格坐标

        Returns:
            tuple: (cells, row_heights, col_widths)
                cells: 二维单元格列表 list[list[PdfCell | None]]，或 None（解析失败时）
                row_heights: 每行高度列表 list[float]
                col_widths: 每列宽度列表 list[float]
        """
        from modules.ocr.paddle_extractor import _TableHtmlParser

        parser = _TableHtmlParser()
        parser.feed(html)

        if not parser.rows:
            return None, [], []

        # 第一遍：确定逻辑列数（考虑 colspan）
        max_logical_cols = 0
        for row in parser.rows:
            logical_cols = sum(colspan for _, _, colspan in row)
            max_logical_cols = max(max_logical_cols, logical_cols)

        n_rows = len(parser.rows)
        n_cols = max_logical_cols if max_logical_cols > 0 else 1

        # occupied 矩阵：标记哪些位置已被合并单元格占据
        occupied = [[False] * n_cols for _ in range(n_rows)]
        # 结果矩阵：合并覆盖位置为 None
        matrix = [[None] * n_cols for _ in range(n_rows)]

        # 第二遍：将解析行展开为完整二维矩阵
        for row_idx, row in enumerate(parser.rows):
            col_idx = 0
            for cell_text, rowspan, colspan in row:
                # 跳过已被上方合并占据的位置
                while col_idx < n_cols and occupied[row_idx][col_idx]:
                    col_idx += 1
                if col_idx >= n_cols:
                    break

                # 钳位 rowspan/colspan，防止越界
                clamped_rowspan = min(rowspan, n_rows - row_idx)
                clamped_colspan = min(colspan, n_cols - col_idx)

                # 在起始位置放置 PdfCell（bbox 稍后计算）
                matrix[row_idx][col_idx] = PdfCell(
                    text=cell_text.replace('\n', ' '),
                    bbox=(0, 0, 0, 0),
                    row_idx=row_idx,
                    col_idx=col_idx,
                    row_span=clamped_rowspan,
                    col_span=clamped_colspan,
                )

                # 标记所有被此合并占据的位置
                for dr in range(clamped_rowspan):
                    for dc in range(clamped_colspan):
                        r = row_idx + dr
                        c = col_idx + dc
                        if r < n_rows and c < n_cols:
                            occupied[r][c] = True

                col_idx += clamped_colspan

        # 计算内容权重分配的行高和列宽（行高优先迭代优化）
        if table_bbox and table_bbox != (0, 0, 0, 0):
            col_widths, row_heights, t_x0, t_y0 = LlmOcrExtractor._compute_table_layout(matrix, n_rows, n_cols, table_bbox)
        else:
            t_x0 = t_y0 = 0
            row_heights = []
            col_widths = []

        # 第三遍：根据矩阵中的位置计算每个单元格的 bbox
        if table_bbox and table_bbox != (0, 0, 0, 0):
            # 预计算每行/每列的起始坐标
            col_starts = [0.0] * n_cols
            for c in range(1, n_cols):
                col_starts[c] = col_starts[c - 1] + col_widths[c - 1]
            row_starts = [0.0] * n_rows
            for r in range(1, n_rows):
                row_starts[r] = row_starts[r - 1] + row_heights[r - 1]

            for r in range(n_rows):
                for c in range(n_cols):
                    cell = matrix[r][c]
                    if cell is not None:
                        cell.bbox = (
                            t_x0 + col_starts[cell.col_idx],
                            t_y0 + row_starts[cell.row_idx],
                            t_x0 + col_starts[cell.col_idx] + sum(col_widths[cell.col_idx + dc] for dc in range(cell.col_span) if cell.col_idx + dc < n_cols),
                            t_y0 + row_starts[cell.row_idx] + sum(row_heights[cell.row_idx + dr] for dr in range(cell.row_span) if cell.row_idx + dr < n_rows),
                        )

        logger.info(f"_parse_html_table: {n_rows}行x{n_cols}列, table_bbox={table_bbox}, row_heights={row_heights}, col_widths={col_widths}")
        logger.info(f"内容权重列宽行高计算: col_widths={col_widths}, row_heights={row_heights}")
        return matrix, row_heights, col_widths
