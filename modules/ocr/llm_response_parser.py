# -*- coding: utf-8 -*-
from __future__ import annotations

"""LLM OCR响应解析器

负责将LLM视觉模型的原始响应解析为结构化OcrBlock列表，
再映射为TextBlock/PdfTable/PdfImage模型。

支持三种响应格式：
1. <|ref|>标签格式（DeepSeek-OCR原生格式）
2. JSON格式（通用VLM模型）
3. Markdown段落格式（回退）
"""

import json
import math
import re
import logging
from dataclasses import dataclass, field

from models.text_block import TextBlock
from models.extraction import PdfImage, PdfTable
from utils.text_processing import fix_line_break_hyphens

logger = logging.getLogger(__name__)

# 模块级常量
TABLE_HTML_MARKER = '<table'


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
    'title': (True, 1),
    'sub_title': (True, 1),
    'section_title': (True, 1),
    'header': (False, 3),
    'footer': (False, 4),
    'footnote': (False, 5),
    'page_number': (False, 4),
    'text': (True, 0),
    'image': (True, 0),  # image类型不创建TextBlock，这里只是占位
}


class LlmOcrResponseParser:
    """LLM OCR响应解析器

    将LLM视觉模型的原始响应文本解析为OcrBlock中间数据结构，
    再映射为TextBlock/PdfTable/PdfImage模型对象。
    """

    def __init__(self, translator_type='aiping', lang='ch', source_lang=None):
        """初始化解析器

        Args:
            translator_type (str): 翻译引擎类型
            lang (str): OCR识别语言
            source_lang (str | None): 源语言
        """
        self.translator_type = translator_type
        self.lang = lang
        self.source_lang = source_lang

    def _parse_response(self, result_text, page_num, page_info=None, page=None,
                        temp_images_dir=None, crop_callback=None, table_parse_callback=None):
        """解析LLM返回的响应为TextBlock/PdfTable/PdfImage

        三阶段管道：格式检测 → 结构化解析(OcrBlock) → 模型映射

        格式检测优先级（带回退）：
        1. <|ref|>标签格式（DeepSeek-OCR grounding输出）
        2. JSON格式（通用VLM模型，仅严格匹配）
        3. Markdown段落格式（回退）

        当高优先级格式解析返回空结果时，自动回退到下一优先级格式。

        Args:
            result_text (str): LLM返回的原始文本
            page_num (int): 页码
            page_info (dict | None): 页面尺寸信息
            page: fitz.Page对象，用于图像裁剪
            temp_images_dir (str | None): 临时图像保存目录
            crop_callback (callable | None): 图像裁剪回调，签名 (page, pdf_bbox, page_num, image_idx, temp_images_dir) -> str
            table_parse_callback (callable | None): 表格解析回调，签名 (html, table_bbox) -> (cells, row_heights, col_widths)

        Returns:
            tuple | None: (text_blocks, tables, images) 或 None（失败时）
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
        return self._map_ocr_blocks_to_models(
            ocr_blocks, page_num, page_info, page=page,
            temp_images_dir=temp_images_dir,
            crop_callback=crop_callback,
            table_parse_callback=table_parse_callback
        )

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

    def _map_ocr_blocks_to_models(self, ocr_blocks, page_num, page_info=None,
                                  page=None, temp_images_dir=None,
                                  crop_callback=None, table_parse_callback=None):
        """将OcrBlock列表统一映射为TextBlock/PdfTable/PdfImage

        Args:
            ocr_blocks: OcrBlock列表
            page_num: 页码
            page_info: 页面尺寸信息
            page: fitz.Page对象，用于图像裁剪
            temp_images_dir: 临时图像保存目录
            crop_callback: 图像裁剪回调，签名 (page, pdf_bbox, page_num, image_idx, temp_images_dir) -> str
            table_parse_callback: 表格解析回调，签名 (html, table_bbox) -> (cells, row_heights, col_widths)

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
                if page and temp_images_dir and crop_callback:
                    image_path = crop_callback(page, pdf_bbox, page_num, image_idx, temp_images_dir)
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
                if table_parse_callback:
                    cells, row_heights, col_widths = table_parse_callback(block.table_html, table_bbox=pdf_bbox)
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
                else:
                    logger.warning("表格解析回调未设置，跳过表格解析")
                continue

            # 文本类型
            if not block.text:
                continue

            # 质量过滤：跳过明显幻觉文本（如空白页产生的数字枚举）
            if self._is_noise_text(block):
                logger.warning(
                    f"第{page_num}页跳过噪声文本块(bbox={block.bbox}): "
                    f"内容前50字='{block.text[:50]}'"
                )
                continue

            tb = self._create_text_block(block, page_num, page_info)
            tb.block_no = text_block_no
            text_block_no += 1
            text_blocks.append(tb)

        logger.info(f"第{page_num}页OcrBlock映射结果: {len(text_blocks)}个文本块, {len(tables)}个表格, {len(images)}个图像")
        return text_blocks, tables, images

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
    def _is_noise_text(ocr_block) -> bool:
        """检测 OcrBlock 是否为幻觉/噪声文本

        对空白页 OCR 产生的数字枚举、重复模式等幻觉文本进行过滤。
        满足任意一条规则即判定为噪声：

        R1: 全页覆盖 bbox + 数字枚举模式（如 "1. 2. 3. ... 111"）
        R2: 重复数字序列（如 "1.1.1.1.1..."）
        R3: 纯符号/数字/标点占比 > 85%

        Args:
            ocr_block: OcrBlock 对象

        Returns:
            bool: 是否为噪声文本
        """
        text = ocr_block.text
        if not text or not text.strip():
            return False

        # R1: 全页覆盖 + 数字枚举
        bbox = ocr_block.bbox
        if bbox and len(bbox) == 4:
            x1, y1, x2, y2 = bbox
            # 归一化坐标 (0-999) 下，接近全页覆盖
            if x1 <= 1 and y1 <= 1 and x2 >= 990 and y2 >= 990:
                # 内容以数字开头且以数字结尾，或大量 "n. n+1." 模式
                stripped = text.strip()
                if re.match(r'^[\d#.\s]+$', stripped):
                    return True
                # 匹配 "1. 2. 3. 4." 或 "# 1. 2. 3." 模式
                number_seq = re.findall(r'\b\d+\.\s*', stripped)
                if len(number_seq) >= 5:
                    ratio = len(''.join(number_seq)) / len(stripped) if stripped else 0
                    if ratio > 0.4:
                        return True

        # R2: 重复数字序列（如 "1.1.1.1.1...", "1.1.1.1..."）
        if re.match(r'^[\d.]+$', text.strip()):
            # 检查是否有重复片段（如 "1.1." 重复）
            core = text.strip().replace('.', '').replace(' ', '')
            if len(core) >= 10 and len(set(core)) <= 2:
                return True

        # R3: 纯符号/数字/标点占比
        stripped_text = text.strip()
        if len(stripped_text) >= 20:
            digit_punct_count = sum(
                1 for c in stripped_text
                if c.isdigit() or c.isspace() or c in '.,:;!?-#()[]{}<>@/\\\'\"|_~`^%$&+=*'
            )
            ratio = digit_punct_count / len(stripped_text)
            if ratio > 0.85:
                return True

        return False
