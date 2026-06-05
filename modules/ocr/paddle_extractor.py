# -*- coding: utf-8 -*-
"""PaddleOCR提取器

基于PaddleOCR PP-StructureV3的OCR提取器实现。
采用分步加载策略：每一步仅加载所需模型，处理完毕后立即释放，
避免同时加载所有模型导致内存溢出（2.5GB+）。

步骤1:   版面分析 + 文本OCR + 公式识别 + 表格识别（~2900MB，处理完释放）
步骤2:   图表/印章裁剪（无需额外模型）
"""

import gc
import os
import sys
import re
import logging
import time

import cv2
import psutil
import fitz
from html.parser import HTMLParser

from models.text_block import TextBlock
from models.extraction import PdfPage, PdfTable, PdfCell, PdfImage, PdfExtraction
from modules.ocr.base import OcrExtractor
from config import config

logger = logging.getLogger(__name__)


class _TableHtmlParser(HTMLParser):
    """HTML表格解析器

    解析PP-StructureV3返回的HTML表格为PdfCell二维列表。
    """

    def __init__(self):
        super().__init__()
        self.rows = []
        self.current_row = []
        self.current_cell = ''
        self.in_cell = False

    def handle_starttag(self, tag, attrs):
        if tag in ('td', 'th'):
            self.in_cell = True
            self.current_cell = ''

    def handle_endtag(self, tag):
        if tag in ('td', 'th'):
            self.in_cell = False
            self.current_row.append(self.current_cell.strip())
        elif tag == 'tr':
            if self.current_row:
                self.rows.append(self.current_row)
            self.current_row = []

    def handle_data(self, data):
        if self.in_cell:
            self.current_cell += data


from typing import Optional, Dict, Any

class PaddleOcrExtractor(OcrExtractor):
    """基于PaddleOCR PP-StructureV3的OCR提取器（分步加载）

    使用分步加载策略，每一步仅创建所需功能的PPStructureV3管线，
    处理完毕后立即释放，避免同时加载所有模型导致内存溢出。

    - 步骤1:   版面分析 + 文本OCR + 公式识别 + 表格识别 → TextBlock + PdfTable
    - 步骤2:   图表/印章裁剪 → PdfImage
    """

    # 步骤定义常量
    STEP_LAYOUT_OCR = 1
    STEP_LAYOUT_OCR_NAME = '版面分析+文本+公式+表格'
    STEP_IMAGE_CROP = 2
    STEP_IMAGE_CROP_NAME = '图像裁剪'

    # 需要从parsing_res_list中提取文本的版面标签
    TEXT_LABELS = {
        'text', 'title', 'paragraph_title', 'content', 'document_title', 'doc_title', 'section_title',
        'abstract', 'references', 'reference', 'footnote',
        'header', 'footer', 'page_number',
        'sidebar_text', 'text_continue',
        'table_caption', 'table_footnote',
        'list', 'list_item', 'item',
    }

    # 标记为非正文的标签
    NON_BODY_LABELS = {'footer', 'page_number', 'footnote', 'header'}

    # 需要保存为图片的版面标签
    IMAGE_LABELS = {'image', 'figure', 'chart', 'figure_caption', 'seal'}

    MEMORY_FACTOR = 0.55
    MEMORY_CAP_LAYOUT = 1800 * 1024 * 1024
    MEMORY_CAP_TABLE = 1600 * 1024 * 1024
    MEMORY_CAP_FORMULA = 1000 * 1024 * 1024

    def __init__(self, lang: str = 'ch', use_gpu: bool = True,
                 memory_params: Optional[Dict[str, Any]] = None,
                 skip_table: Optional[bool] = None,
                 skip_formula: Optional[bool] = None,
                 ocr_params: Optional[Dict[str, Any]] = None):
        self.lang = lang
        self.use_gpu = use_gpu
        self._actual_device = None
        self._memory_factor = (memory_params or {}).get('memory_factor', self.MEMORY_FACTOR)
        self._memory_cap_layout = (memory_params or {}).get('memory_cap_layout', self.MEMORY_CAP_LAYOUT)
        self._memory_cap_table = (memory_params or {}).get('memory_cap_table', self.MEMORY_CAP_TABLE)
        self._memory_cap_formula = (memory_params or {}).get('memory_cap_formula', self.MEMORY_CAP_FORMULA)
        self._skip_table = skip_table if skip_table is not None else config.OCR_SKIP_TABLE
        self._skip_formula = skip_formula if skip_formula is not None else config.OCR_SKIP_FORMULA
        safe_params = ocr_params or {}
        self.cpu_threads = safe_params.get('cpu_threads', None)
        self.model_names = safe_params.get('model_names', {})
        self.inference_params = safe_params.get('inference_params', {})
        self.render_dpi = safe_params.get('render_dpi', None)

    def _check_available_memory(self):
        """检查系统可用内存

        Returns:
            int: 可用内存字节数
        """
        return psutil.virtual_memory().available

    def _check_gpu_available(self):
        """检查 GPU 是否可用

        Returns:
            bool: GPU 是否可用
        """
        try:
            import paddle
            return paddle.is_compiled_with_cuda() and paddle.device.cuda.device_count() > 0
        except Exception:
            logger.debug("GPU availability check failed", exc_info=True)
            return False

    def _log_memory(self, step_name):
        """记录当前进程内存使用"""
        try:
            process = psutil.Process(os.getpid())
            rss_mb = process.memory_info().rss / (1024 * 1024)
            logger.info(f"{step_name}: 内存使用 {rss_mb:.0f} MB")
        except Exception:
            logger.debug("Memory log failed", exc_info=True)

    @staticmethod
    def _force_release_memory():
        try:
            import ctypes
            process = psutil.Process(os.getpid())
            rss_before = process.memory_info().rss / (1024 * 1024)

            if sys.platform == 'darwin':
                try:
                    libc = ctypes.CDLL("libc.dylib")
                    libc.malloc_zone_pressure_relief(0, 0)
                except Exception:
                    pass
            else:
                try:
                    ctypes.CDLL("libc.so.6").malloc_trim(0)
                except Exception:
                    pass

            gc.collect()
            rss_after = process.memory_info().rss / (1024 * 1024)
            logger.info(f"强制释放内存: RSS {rss_before:.0f}MB -> {rss_after:.0f}MB (释放 {rss_before - rss_after:.0f}MB)")
        except Exception as e:
            logger.debug(f"强制释放内存失败: {e}")

    @staticmethod
    def _clean_latex(latex):
        if not latex or not latex.strip():
            return latex
        result = latex.strip()

        def fix_text_mode(match):
            prefix = match.group(1)
            content = match.group(2)
            fixed = re.sub(r'(?<=[a-zA-Z])\s+(?=[a-zA-Z])', '', content)
            return prefix + '{' + fixed + '}'
        result = re.sub(r'(\\mathrm|\\text|\\mathbf|\\mathit|\\mathsf|\\mathtt)\{([^}]*)\}', fix_text_mode, result)

        result = re.sub(r'(?<=\b[A-Z])\s+(?=[A-Z]\b)', '', result)

        result = re.sub(r'\s*\{\s*', '{', result)
        result = re.sub(r'\s*\}\s*', '}', result)

        result = re.sub(r' {2,}', ' ', result)

        result = re.sub(r'\s*(\\cdot|\\times|\\pm|\\div|\\leq|\\geq|\\neq|\\approx|\\equiv)\s*', r' \1 ', result)
        result = re.sub(r'\s*(=|\+|<|>)\s*', r' \1 ', result)

        result = result.strip()

        incomplete_endings = [
            '\\frac', '\\sqrt', '\\sum', '\\int', '\\prod',
            '\\cdot', '\\times', '\\pm', '\\div',
            '\\left', '\\right', '\\bigl', '\\bigr',
            '\\begin', '\\hat', '\\bar', '\\vec', '\\dot', '\\tilde',
            '\\overline', '\\underline', '\\overrightarrow',
        ]
        for ending in incomplete_endings:
            if result.rstrip().endswith(ending):
                logger.warning(f'公式可能被截断: ...{ending[-20:]}')
                break

        return result

    def _create_pipeline(self, use_table=False, use_formula=False, use_region_detection=False, cpu_threads=None):
        """创建PP-StructureV3管线实例

        根据参数仅启用所需功能，减少内存占用。
        创建前会检查系统可用内存，不足时抛出 MemoryError。

        Args:
            use_table (bool): 是否启用表格识别
            use_formula (bool): 是否启用公式识别

        Returns:
            PPStructureV3: 管线实例

        Raises:
            MemoryError: 可用内存不足
            RuntimeError: PaddleOCR 初始化失败
        """
        available = self._check_available_memory()
        if use_table:
            required = min(int(available * self._memory_factor), self._memory_cap_table)
            step_name = "表格识别"
        elif use_formula:
            required = min(int(available * self._memory_factor), self._memory_cap_formula)
            step_name = "公式识别"
        else:
            required = min(int(available * self._memory_factor), self._memory_cap_layout)
            step_name = self.STEP_LAYOUT_OCR_NAME

        if available < required:
            required_mb = required / (1024 * 1024)
            available_mb = available / (1024 * 1024)
            raise MemoryError(
                f"可用内存不足（当前 {available_mb:.0f} MB，"
                f"需要 {required_mb:.0f} MB），"
                f"无法执行{step_name}步骤"
            )

        # 确定实际使用的设备
        if self.use_gpu:
            if self._check_gpu_available():
                device = "gpu:0"
            else:
                logger.warning("GPU 不可用，自动回退到 CPU 模式")
                device = "cpu"
        else:
            device = "cpu"

        self._actual_device = device
        formula_model = self.model_names.get('formula', 'PP-FormulaNet_plus-S')
        model_info = f", formula_model={formula_model}" if use_formula else ""
        _det_side_len = self.inference_params.get('text_det_limit_side_len', 960)
        _rec_batch = self.inference_params.get('text_recognition_batch_size', 10)
        logger.info(
            f"创建PP-StructureV3管线: lang={self.lang}, device={device}, "
            f"use_table={use_table}, use_formula={use_formula}{model_info}, "
            f"det_side_len={_det_side_len}, rec_batch={_rec_batch}"
        )

        try:
            from paddleocr import PPStructureV3
            self._log_memory(f"创建管线前(use_table={use_table}, use_formula={use_formula})")

            # 记录当前 root logger 状态，用于构造后恢复
            root_logger = logging.getLogger()
            root_level_before = root_logger.level
            root_handlers_before = list(root_logger.handlers)  # 保存 handler 引用

            kwargs = dict(
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                use_table_recognition=use_table,
                use_formula_recognition=use_formula,
                use_region_detection=use_region_detection,
                device=device,
                lang=self.lang,
            )
            if self.model_names:
                layout_model = self.model_names.get('layout')
                if layout_model:
                    kwargs['layout_detection_model_name'] = layout_model
                text_det = self.model_names.get('text_det')
                if text_det:
                    kwargs['text_detection_model_name'] = text_det
                text_rec = self.model_names.get('text_rec')
                if text_rec:
                    kwargs['text_recognition_model_name'] = text_rec
                if use_formula:
                    kwargs['formula_recognition_model_name'] = self.model_names.get('formula', 'PP-FormulaNet_plus-S')
                if use_table:
                    table_model = self.model_names.get('table')
                    if table_model:
                        kwargs['wired_table_structure_recognition_model_name'] = table_model
            elif use_formula:
                kwargs['formula_recognition_model_name'] = 'PP-FormulaNet_plus-S'
            kwargs['text_det_limit_side_len'] = self.inference_params.get('text_det_limit_side_len', 960)
            kwargs['text_det_thresh'] = 0.3
            kwargs['text_det_box_thresh'] = 0.5
            kwargs['text_recognition_batch_size'] = self.inference_params.get('text_recognition_batch_size', 10)
            kwargs['text_rec_score_thresh'] = 0.5
            if cpu_threads is not None:
                kwargs['cpu_threads'] = cpu_threads
            pipeline = PPStructureV3(**kwargs)

            # PPStructureV3 构造可能破坏 root logger 和子 logger 配置
            # 恢复 root logger level（被改为 WARNING 等会过滤 INFO 日志）
            if root_logger.level > root_level_before:
                logger.warning(
                    f"PPStructureV3 构造修改了 root logger level "
                    f"({logging.getLevelName(root_level_before)} -> {logging.getLevelName(root_logger.level)})，正在恢复"
                )
                root_logger.setLevel(root_level_before)

            # 恢复 root logger handlers：直接恢复保存的 handler 引用
            root_logger.handlers.clear()
            for h in root_handlers_before:
                if h not in root_logger.handlers:
                    root_logger.addHandler(h)

            # 恢复子 logger propagate（被设为 False 会阻止日志传播到 root）
            child_logger = logging.getLogger(__name__)
            if not child_logger.propagate:
                if child_logger.handlers:
                    logger.debug(
                        "PPStructureV3 构造将子 logger propagate 设为 False，"
                        "子 logger 有自有 handler，保持 propagate=False 避免重复输出"
                    )
                else:
                    logger.warning(
                        "PPStructureV3 构造将子 logger propagate 设为 False，正在恢复为 True"
                    )
                    child_logger.propagate = True

            # 移除子 logger 上被添加的 NullHandler（会吞掉所有日志）
            null_handlers = [
                h for h in child_logger.handlers
                if isinstance(h, logging.NullHandler)
            ]
            for h in null_handlers:
                logger.warning("PPStructureV3 构造向子 logger 添加了 NullHandler，正在移除")
                child_logger.removeHandler(h)

            # 确保子 logger level 为 INFO 或更低
            if child_logger.level > logging.INFO:
                logger.warning(
                    f"PPStructureV3 构造修改了子 logger level 为 {logging.getLevelName(child_logger.level)}，正在恢复为 INFO"
                )
                child_logger.setLevel(logging.INFO)

            # 验证日志状态已恢复
            logger.info("PPStructureV3 构造后 logger 状态已检查并恢复")

            return pipeline
        except Exception as e:
            logger.error(f"PP-StructureV3 初始化失败: {str(e)}", exc_info=True)
            raise RuntimeError(
                f"OCR 引擎初始化失败: {str(e)}。"
                "请确保已正确安装 PaddleOCR: pip install \"paddleocr[all]\""
            ) from e

    def _render_pages(self, doc, target_pages, temp_images_dir):
        """渲染PDF页面为图像

        Args:
            doc (fitz.Document): 已打开的PDF文档
            target_pages (list[int]): 目标页码列表（1-based）
            temp_images_dir (str): 临时图像目录

        Returns:
            dict[int, dict]: 页码 -> 页面信息映射，包含:
                - img_path: 图像路径
                - page_width_pts: PDF页面宽度（点）
                - page_height_pts: PDF页面高度（点）
                - img_width_px: 渲染图像宽度（像素）
                - img_height_px: 渲染图像高度（像素）
        """
        page_images = {}
        dpi = self.render_dpi if self.render_dpi is not None else config.OCR_RENDER_DPI
        logger.info(f"OCR 渲染 DPI: {dpi} (profiler={self.render_dpi}, config={config.OCR_RENDER_DPI})")
        for page_num in target_pages:
            page_idx = page_num - 1
            page = doc[page_idx]
            pix = page.get_pixmap(dpi=dpi)
            page_width_pts = page.rect.width
            page_height_pts = page.rect.height
            img_width_px = pix.width
            img_height_px = pix.height

            img_path = os.path.join(temp_images_dir, f"ocr_page_{page_num}.png")
            pix.save(img_path)
            page_images[page_num] = {
                'img_path': img_path,
                'page_width_pts': page_width_pts,
                'page_height_pts': page_height_pts,
                'img_width_px': img_width_px,
                'img_height_px': img_height_px,
            }
        return page_images

    def _pixel_to_pdf_coords(self, bbox, page_info):
        """将图像像素坐标转换为PDF点坐标

        Args:
            bbox: (x1, y1, x2, y2) 像素坐标
            page_info: 包含页面尺寸信息的字典

        Returns:
            tuple: (x1, y1, x2, y2) PDF点坐标
        """
        scale_x = page_info['page_width_pts'] / page_info['img_width_px']
        scale_y = page_info['page_height_pts'] / page_info['img_height_px']
        x1, y1, x2, y2 = bbox
        return (x1 * scale_x, y1 * scale_y, x2 * scale_x, y2 * scale_y)

    def _load_image_as_array(self, img_path, page_num):
        if not os.path.exists(img_path):
            logger.error(f"图片文件不存在: {img_path}, page={page_num}")
            return None
        img_array = cv2.imread(img_path)
        if img_array is None:
            logger.error(f"cv2.imread 失败: {img_path}, page={page_num}")
            return None
        return img_array

    @staticmethod
    def _create_text_block(block_no, text, pdf_bbox, page_num, font_size=None, is_formula=False, is_body_text=None):
        tb = TextBlock(
            block_no=block_no,
            text=text,
            bbox=pdf_bbox,
            block_type=0,
            page_num=page_num,
        )
        if font_size is not None:
            tb.font_size = max(6, min(36, font_size))
        if is_formula:
            tb.is_formula = True
        if is_body_text is not None:
            tb.is_body_text = is_body_text
        return tb

    @staticmethod
    def _compute_tight_bbox(layout_bbox, textline_boxes, textline_texts):
        """从 textline bbox 计算精确的文字边界框

        Args:
            layout_bbox: PP-StructureV3 布局区域 bbox (x1,y1,x2,y2)
            textline_boxes: textline bbox 列表
            textline_texts: textline 文本列表

        Returns:
            tuple | None: (x1,y1,x2,y2) 精确边界框，或 None（无法计算时）
        """
        if textline_boxes is None or textline_texts is None or len(textline_boxes) == 0 or len(textline_texts) == 0:
            return None

        lx1, ly1, lx2, ly2 = layout_bbox
        matched = []
        for i, tl_box in enumerate(textline_boxes):
            if len(tl_box) < 4:
                continue
            bx, by, bx2, by2 = float(tl_box[0]), float(tl_box[1]), float(tl_box[2]), float(tl_box[3])
            cx, cy = (bx+bx2)/2, (by+by2)/2
            # 检查 textline 中心是否在布局区域内（与 _build_text_from_textlines 一致）
            if lx1 <= cx <= lx2 and ly1 <= cy <= ly2:
                matched.append((bx, by, bx2, by2))

        if not matched:
            return None

        tight_x1 = min(m[0] for m in matched)
        tight_y1 = min(m[1] for m in matched)
        tight_x2 = max(m[2] for m in matched)
        tight_y2 = max(m[3] for m in matched)

        # 防止超出原始布局 bbox 过多（超过 30% 则截断右边界）
        lwidth = lx2 - lx1
        if lwidth > 0:
            twidth = tight_x2 - tight_x1
            if twidth / lwidth > 1.3:
                tight_x2 = lx2

        return (tight_x1, tight_y1, tight_x2, tight_y2)

    @staticmethod
    def _build_text_from_textlines(block_bbox, textline_boxes, textline_texts):
        if textline_boxes is None or textline_texts is None or len(textline_boxes) == 0 or len(textline_texts) == 0 or len(textline_boxes) != len(textline_texts):
            return None
        bx1, by1, bx2, by2 = block_bbox
        matching = []
        for i, tl_box in enumerate(textline_boxes):
            if len(tl_box) >= 4:
                tl_x1, tl_y1, tl_x2, tl_y2 = float(tl_box[0]), float(tl_box[1]), float(tl_box[2]), float(tl_box[3])
                tl_cx = (tl_x1 + tl_x2) / 2
                tl_cy = (tl_y1 + tl_y2) / 2
                if bx1 <= tl_cx <= bx2 and by1 <= tl_cy <= by2:
                    matching.append((tl_cy, textline_texts[i].strip()))
        if not matching:
            return None
        matching.sort(key=lambda x: x[0])
        lines = []
        current_line_y = None
        current_parts = []
        for cy, txt in matching:
            if current_line_y is None or abs(cy - current_line_y) > 5:
                if current_parts:
                    lines.append(' '.join(current_parts))
                current_parts = [txt]
                current_line_y = cy
            else:
                current_parts.append(txt)
        if current_parts:
            lines.append(' '.join(current_parts))
        result = '\n'.join(lines)
        return result if result.strip() else None

    def _process_page_layout(self, pipeline, img_path, page_num, page_info, use_formula=False):
        """步骤1: 版面分析 + 文本OCR + 公式识别 + 表格识别

        使用PP-StructureV3管线进行版面分析，提取文本块并记录布局信息。
        当 use_formula=True 时，同时从 formula_res_list 提取 LaTeX 公式。
        当管线启用 use_table=True 时，同时从 table_res_list 提取表格。
        result 是 LayoutParsingResultV2（dict 子类），通过 result["key"] 访问数据。
        result["parsing_res_list"] 返回 LayoutBlock 列表，每个 block 有
        .label / .bbox / .content 属性。

        Args:
            pipeline: PPStructureV3管线实例
            img_path (str): 页面图像路径
            page_num (int): 页码（1-based）
            page_info (dict): 页面尺寸信息
            use_formula (bool): 管线是否启用了公式识别

        Returns:
            dict: {
                'text_blocks': list[TextBlock],
                'has_table': bool,
                'has_formula': bool,
                'image_regions': list[dict],
                'layout_bboxes': list[dict],
                'tables': list[PdfTable],
            }
        """
        text_blocks = []
        block_no = 0
        has_table = False
        has_formula = False
        image_regions = []
        layout_bboxes = []
        tables = []
        label_counts = {}

        try:
            img_array = self._load_image_as_array(img_path, page_num)
            if img_array is None:
                logger.error(f"步骤1处理第{page_num}页版面分析时出错: 无法加载图片")
                return {
                    'text_blocks': [],
                    'has_table': False,
                    'has_formula': False,
                    'image_regions': [],
                    'layout_bboxes': [],
                    'tables': [],
                }
            for result in pipeline.predict(img_array):
                # result is LayoutParsingResultV2 (dict subclass)
                parsing_res_list = result.get("parsing_res_list", [])

                # 提取表格识别结果（当 use_table=True 时可用）
                table_res_list = result.get("table_res_list", [])
                if table_res_list:
                    logger.info(f"[TABLE_DEBUG] page={page_num}: table_res_list长度={len(table_res_list)}")

                # 提取 textline 级别的 OCR 结果，用于准确估算字体大小
                textline_boxes = []
                textline_texts = []
                overall_ocr_res = result.get("overall_ocr_res")
                if overall_ocr_res is not None:
                    try:
                        rec_boxes = overall_ocr_res.get("rec_boxes") if hasattr(overall_ocr_res, "get") else getattr(overall_ocr_res, "rec_boxes", None)
                        rec_texts = overall_ocr_res.get("rec_text") if hasattr(overall_ocr_res, "get") else getattr(overall_ocr_res, "rec_text", None)
                        if rec_boxes is not None and len(rec_boxes) > 0:
                            textline_boxes = rec_boxes
                            if rec_texts is not None and len(rec_texts) == len(rec_boxes):
                                textline_texts = rec_texts
                            logger.info(f"[FONT_DEBUG] page={page_num}: 从 overall_ocr_res 获取到 {len(textline_boxes)} 个 textline bbox, {len(textline_texts)} 个 textline text")
                    except Exception as e:
                        logger.debug(f"page={page_num}: 提取 overall_ocr_res 失败: {e}")

                # 处理表格识别结果
                if table_res_list and not self._skip_table:
                    # 从 parsing_res_list 中提取 table 标签的 bbox
                    table_bboxes = []
                    for block in parsing_res_list:
                        if block.label == 'table':
                            bbox = block.bbox if hasattr(block, 'bbox') else block.get('bbox', [0, 0, 0, 0])
                            table_bboxes.append(bbox)
                    
                    logger.info(f"[TABLE_DEBUG] page={page_num}: table_bboxes长度={len(table_bboxes)}")
                    
                    for idx, table_res in enumerate(table_res_list):
                        # 提取 HTML - 使用正确的键名 'pred'（PaddleX SingleTableRecognitionResult.html 返回 {"pred": ...}）
                        html_dict = table_res.html if hasattr(table_res, 'html') else {}
                        html = html_dict.get('pred', '') if isinstance(html_dict, dict) else str(html_dict)
                        
                        if not html:
                            logger.warning(f"[TABLE_DEBUG] page={page_num}: 表格{idx} HTML提取为空, html_dict keys={list(html_dict.keys()) if isinstance(html_dict, dict) else 'N/A'}")
                            continue
                        
                        # 获取表格 bbox
                        if idx >= len(table_bboxes):
                            logger.warning(f"[TABLE_DEBUG] page={page_num}: 表格{idx} 无对应bbox（table_bboxes长度={len(table_bboxes)}），跳过")
                            continue
                        bbox = table_bboxes[idx]
                        
                        # 检查 bbox 是否有效
                        if not bbox or len(bbox) < 4 or (bbox[2] - bbox[0]) <= 0 or (bbox[3] - bbox[1]) <= 0:
                            logger.warning(f"[TABLE_DEBUG] page={page_num}: 表格{idx} bbox无效: {bbox}，跳过")
                            continue
                        
                        # 转换 bbox 到 PDF 坐标（与文本块使用相同的转换方法）
                        pdf_bbox = self._pixel_to_pdf_coords(bbox, page_info)
                        logger.info(f"[TABLE_DIAG] page={page_num}: 像素坐标={bbox}, PDF坐标={pdf_bbox}")
                        
                        # 解析 HTML 表格
                        cells = self._parse_html_table(html)

                        # 为表格计算统一网格布局
                        row_heights_px = []
                        col_widths_px = []
                        if cells and textline_boxes is not None and len(textline_boxes) > 0:
                            cells, row_heights_px, col_widths_px = self._compute_table_grid(
                                bbox, cells, textline_boxes, textline_texts
                            )

                        # 将单元格 bbox 从像素坐标转换为 PDF 坐标
                        for row in cells:
                            for cell in row:
                                if cell.bbox and cell.bbox != (0, 0, 0, 0):
                                    cell.bbox = self._pixel_to_pdf_coords(cell.bbox, page_info)
                                    cell.width = cell.bbox[2] - cell.bbox[0]
                                    cell.height = cell.bbox[3] - cell.bbox[1]

                        # 转换行列尺寸并设置到 PdfTable
                        if row_heights_px and col_widths_px:
                            scale_x = page_info['page_width_pts'] / page_info['img_width_px']
                            scale_y = page_info['page_height_pts'] / page_info['img_height_px']
                            row_heights = [h * scale_y for h in row_heights_px]
                            col_widths = [w * scale_x for w in col_widths_px]
                        else:
                            row_heights = []
                            col_widths = []

                        table = PdfTable(
                            page_num=page_num,
                            table_idx=len(tables),
                            bbox=pdf_bbox,
                            cells=cells,
                            row_heights=row_heights,
                            col_widths=col_widths,
                        )
                        tables.append(table)
                        logger.info(f"[TABLE_DEBUG] page={page_num}: 表格{idx}提取成功, cells={len(cells) if cells else 0}, html长度={len(html)}")

                for block in parsing_res_list:
                    label = block.label
                    label_counts[label] = label_counts.get(label, 0) + 1
                    bbox = block.bbox  # [x1, y1, x2, y2]
                    content = block.content  # text content

                    _known_labels = self.TEXT_LABELS | self.IMAGE_LABELS | {'table', 'formula', 'formula_number'}
                    if label not in _known_labels:
                        _preview = (content or '')[:80]
                        logger.warning(f"[LABEL_DEBUG] page={page_num}: unknown label={label!r}, content_preview={_preview!r}")
                    else:
                        logger.debug(f"[LABEL_DEBUG] page={page_num}: known label={label!r}")

                    if not bbox or len(bbox) < 4:
                        continue

                    x1, y1, x2, y2 = bbox
                    layout_bboxes.append({
                        'bbox': self._pixel_to_pdf_coords((float(x1), float(y1), float(x2), float(y2)), page_info),
                        'label': label,
                    })

                    if label in self.TEXT_LABELS:
                        textline_text = PaddleOcrExtractor._build_text_from_textlines(
                            (float(x1), float(y1), float(x2), float(y2)),
                            textline_boxes, textline_texts
                        )
                        text = textline_text if textline_text else (content or '')
                        if text.strip():
                            # 使用 textline 计算精确 bbox，解决残影问题
                            tight_bbox = PaddleOcrExtractor._compute_tight_bbox(
                                (float(x1), float(y1), float(x2), float(y2)),
                                textline_boxes, textline_texts
                            )
                            if tight_bbox:
                                pixel_bbox = tight_bbox
                                logger.debug(f"[TIGHT_BBOX] page={page_num}, label={label}, "
                                             f"layout=({float(x1):.0f},{float(y1):.0f},{float(x2):.0f},{float(y2):.0f}), "
                                             f"tight=({tight_bbox[0]:.0f},{tight_bbox[1]:.0f},{tight_bbox[2]:.0f},{tight_bbox[3]:.0f})")
                            else:
                                pixel_bbox = (float(x1), float(y1), float(x2), float(y2))
                            pdf_bbox = self._pixel_to_pdf_coords(pixel_bbox, page_info)

                            page_area = page_info['page_width_pts'] * page_info['page_height_pts']
                            min_block_area = page_area * 0.0001
                            block_area = (pdf_bbox[2] - pdf_bbox[0]) * (pdf_bbox[3] - pdf_bbox[1])
                            if block_area < min_block_area:
                                continue

                            # Estimate font_size using textline-level bbox heights
                            bbox_height = pdf_bbox[3] - pdf_bbox[1]
                            estimated_font_size = 10.0  # default
                            font_estimation_method = "fallback"

                            # 方法1: 使用 overall_ocr_res 中的 textline bbox
                            if textline_boxes is not None and len(textline_boxes) > 0:
                                # 找到落在当前 block bbox 范围内的 textline
                                block_x1, block_y1 = float(x1), float(y1)
                                block_x2, block_y2 = float(x2), float(y2)
                                matching_heights = []
                                for tl_box in textline_boxes:
                                    if len(tl_box) >= 4:
                                        tl_x1, tl_y1, tl_x2, tl_y2 = float(tl_box[0]), float(tl_box[1]), float(tl_box[2]), float(tl_box[3])
                                        # textline 中心点在 block 范围内
                                        tl_cx = (tl_x1 + tl_x2) / 2
                                        tl_cy = (tl_y1 + tl_y2) / 2
                                        if block_x1 <= tl_cx <= block_x2 and block_y1 <= tl_cy <= block_y2:
                                            matching_heights.append(tl_y2 - tl_y1)
                                
                                if matching_heights:
                                    avg_textline_height_px = sum(matching_heights) / len(matching_heights)
                                    # 转换为 PDF 点坐标高度
                                    scale_y = bbox_height / (block_y2 - block_y1) if (block_y2 - block_y1) > 0 else 1.0
                                    avg_textline_height_pdf = avg_textline_height_px * scale_y
                                    estimated_font_size = avg_textline_height_pdf * 0.75
                                    font_estimation_method = f"textline({len(matching_heights)}lines,avg_h={avg_textline_height_pdf:.1f}pt)"
                            
                            # 方法2: 使用 LayoutBlock 的 num_of_lines 和 text_line_height
                            if font_estimation_method == "fallback":
                                num_of_lines = getattr(block, 'num_of_lines', None)
                                text_line_height = getattr(block, 'text_line_height', None)
                                if text_line_height and text_line_height > 0:
                                    # text_line_height 是像素坐标，转换为 PDF 点
                                    scale_y = bbox_height / (float(y2) - float(y1)) if (float(y2) - float(y1)) > 0 else 1.0
                                    estimated_font_size = text_line_height * scale_y * 0.75
                                    font_estimation_method = f"block_tlh({text_line_height:.1f}px)"
                                elif num_of_lines and num_of_lines > 1:
                                    estimated_font_size = (bbox_height / num_of_lines) * 0.75
                                    font_estimation_method = f"block_nol({num_of_lines})"
                            
                            # 方法3: 最终回退 - 基于典型行高估算行数
                            if font_estimation_method == "fallback":
                                assumed_line_height = 12.0  # 典型文档行高（pt）
                                estimated_lines = max(1, round(bbox_height / assumed_line_height))
                                estimated_font_size = (bbox_height / estimated_lines) * 0.75
                                font_estimation_method = f"block_bbox_fallback({estimated_lines}lines)"

                            estimated_font_size = max(6, min(36, estimated_font_size))
                            
                            logger.info(f"[FONT_DEBUG] page={page_num}, label={label}, is_body={label not in self.NON_BODY_LABELS}, "
                                        f"text={repr(text[:30])}, font_size={estimated_font_size:.2f}, method={font_estimation_method}")

                            tb = TextBlock(
                                block_no=block_no,
                                text=text.strip(),
                                bbox=pdf_bbox,
                                block_type=0,
                                page_num=page_num,
                            )
                            tb.font_size = estimated_font_size
                            if label in self.NON_BODY_LABELS:
                                tb.is_body_text = False
                            text_blocks.append(tb)
                            block_no += 1

                    elif label == 'table':
                        has_table = True

                    elif label in ('formula', 'formula_number'):
                        has_formula = True
                        if use_formula:
                            text = content or ''
                            text = PaddleOcrExtractor._clean_latex(text) if text else text
                            if text.strip():
                                pixel_bbox = (float(x1), float(y1), float(x2), float(y2))
                                pdf_bbox = self._pixel_to_pdf_coords(pixel_bbox, page_info)
                                bbox_height = pdf_bbox[3] - pdf_bbox[1]
                                estimated_font_size = max(6, min(36, bbox_height * 0.75))
                                tb = TextBlock(
                                    block_no=block_no,
                                    text=text.strip(),
                                    bbox=pdf_bbox,
                                    block_type=0,
                                    page_num=page_num,
                                )
                                tb.font_size = estimated_font_size
                                tb.is_formula = True
                                text_blocks.append(tb)
                                block_no += 1

                    elif label in self.IMAGE_LABELS:
                        image_regions.append({
                            'bbox': self._pixel_to_pdf_coords((float(x1), float(y1), float(x2), float(y2)), page_info),
                            'pixel_bbox': (float(x1), float(y1), float(x2), float(y2)),
                            'label': label,
                        })
                        # figure_caption 包含需要翻译的文本，额外提取 textline 级文本
                        if label == 'figure_caption':
                            caption_text = PaddleOcrExtractor._build_text_from_textlines(
                                (float(x1), float(y1), float(x2), float(y2)),
                                textline_boxes, textline_texts
                            )
                            caption_text = caption_text or (content or '')
                            if caption_text.strip():
                                tight_bbox = PaddleOcrExtractor._compute_tight_bbox(
                                    (float(x1), float(y1), float(x2), float(y2)),
                                    textline_boxes, textline_texts
                                )
                                if tight_bbox:
                                    pixel_bbox = tight_bbox
                                else:
                                    pixel_bbox = (float(x1), float(y1), float(x2), float(y2))
                                pdf_bbox = self._pixel_to_pdf_coords(pixel_bbox, page_info)
                                bbox_height = pdf_bbox[3] - pdf_bbox[1]
                                estimated_font_size = max(6, min(36, bbox_height * 0.75))
                                tb = TextBlock(
                                    block_no=block_no,
                                    text=caption_text.strip(),
                                    bbox=pdf_bbox,
                                    block_type=0,
                                    page_num=page_num,
                                )
                                tb.font_size = estimated_font_size
                                tb.is_body_text = True
                                text_blocks.append(tb)
                                block_no += 1
                                logger.info(f"[SUPPLEMENT] page={page_num}: 从 figure_caption 提取文本, text='{caption_text.strip()[:60]}'")

                    else:
                        textline_text = PaddleOcrExtractor._build_text_from_textlines(
                            (float(x1), float(y1), float(x2), float(y2)),
                            textline_boxes, textline_texts
                        )
                        text = textline_text if textline_text else (content or '')
                        if text.strip():
                            tight_bbox = PaddleOcrExtractor._compute_tight_bbox(
                                (float(x1), float(y1), float(x2), float(y2)),
                                textline_boxes, textline_texts
                            )
                            if tight_bbox:
                                pixel_bbox = tight_bbox
                            else:
                                pixel_bbox = (float(x1), float(y1), float(x2), float(y2))
                            pdf_bbox = self._pixel_to_pdf_coords(pixel_bbox, page_info)

                            page_area = page_info['page_width_pts'] * page_info['page_height_pts']
                            min_block_area = page_area * 0.0001
                            block_area = (pdf_bbox[2] - pdf_bbox[0]) * (pdf_bbox[3] - pdf_bbox[1])
                            if block_area < min_block_area:
                                continue

                            bbox_height = pdf_bbox[3] - pdf_bbox[1]
                            estimated_font_size = max(6, min(36, bbox_height * 0.75))
                            tb = TextBlock(
                                block_no=block_no,
                                text=text.strip(),
                                bbox=pdf_bbox,
                                block_type=0,
                                page_num=page_num,
                            )
                            tb.font_size = estimated_font_size
                            tb.is_body_text = True
                            text_blocks.append(tb)
                            block_no += 1

                # === 补充捕获：检测未被 parsing_res_list 覆盖的 textline 文本 ===
                # PP-StructureV3 可能漏检某些文本（如表格周边的标题/脚注），
                # 通过 overall_ocr_res 的 textline 数据捕获这些漏检文本。
                if textline_boxes is not None and len(textline_boxes) > 0 and textline_texts is not None and len(textline_texts) > 0:
                    # 收集所有已处理 LayoutBlock 的 bbox（像素坐标）
                    processed_bboxes = []
                    for block in parsing_res_list:
                        if not hasattr(block, 'bbox') or not block.bbox or len(block.bbox) < 4:
                            continue
                        b_label = block.label
                        # 覆盖所有已知标签，包括 text、table、figure_caption、formula 等
                        if b_label in self.TEXT_LABELS or b_label in self.IMAGE_LABELS or b_label in ('table', 'formula', 'formula_number'):
                            b = block.bbox
                            processed_bboxes.append((float(b[0]), float(b[1]), float(b[2]), float(b[3])))

                    # 对 textline，检查是否被任何 processed bbox 覆盖
                    uncovered_textlines = []  # list of (cy, text)
                    for i, tl_box in enumerate(textline_boxes):
                        if len(tl_box) < 4:
                            continue
                        tl_x1, tl_y1, tl_x2, tl_y2 = float(tl_box[0]), float(tl_box[1]), float(tl_box[2]), float(tl_box[3])
                        tl_cx = (tl_x1 + tl_x2) / 2
                        tl_cy = (tl_y1 + tl_y2) / 2

                        covered = False
                        for pb in processed_bboxes:
                            pb_x1, pb_y1, pb_x2, pb_y2 = pb
                            # 给 bbox 一个 5px 的扩展容差
                            if (pb_x1 - 5) <= tl_cx <= (pb_x2 + 5) and (pb_y1 - 5) <= tl_cy <= (pb_y2 + 5):
                                covered = True
                                break

                        if not covered:
                            txt = textline_texts[i].strip() if i < len(textline_texts) else ''
                            if txt:
                                uncovered_textlines.append((tl_cy, txt, (tl_x1, tl_y1, tl_x2, tl_y2)))

                    if uncovered_textlines:
                        logger.info(f"[SUPPLEMENT] page={page_num}: 发现 {len(uncovered_textlines)} 个未被 LayoutBlock 覆盖的 textline")
                        # 按垂直位置排序
                        uncovered_textlines.sort(key=lambda x: x[0])

                        # 按垂直邻近关系聚合成文本块
                        groups = []
                        current_group = [uncovered_textlines[0]]
                        for i in range(1, len(uncovered_textlines)):
                            prev_cy = uncovered_textlines[i-1][0]
                            curr_cy = uncovered_textlines[i][0]
                            if curr_cy - prev_cy < 15:  # 垂直距离小于15px视为同一段落
                                current_group.append(uncovered_textlines[i])
                            else:
                                groups.append(current_group)
                                current_group = [uncovered_textlines[i]]
                        if current_group:
                            groups.append(current_group)

                        for group in groups:
                            # 计算聚合文本和 bbox
                            group_texts = []
                            min_x1 = min(t[2][0] for t in group)
                            min_y1 = min(t[2][1] for t in group)
                            max_x2 = max(t[2][2] for t in group)
                            max_y2 = max(t[2][3] for t in group)
                            for t in group:
                                group_texts.append(t[1])
                            combined_text = ' '.join(group_texts)
                            group_pixel_bbox = (min_x1, min_y1, max_x2, max_y2)
                            group_pdf_bbox = self._pixel_to_pdf_coords(group_pixel_bbox, page_info)

                            # 估算字体大小
                            group_height_pdf = group_pdf_bbox[3] - group_pdf_bbox[1]
                            est_font_size = max(6, min(36, group_height_pdf * 0.75))

                            tb = TextBlock(
                                block_no=block_no,
                                text=combined_text,
                                bbox=group_pdf_bbox,
                                block_type=0,
                                page_num=page_num,
                            )
                            tb.font_size = est_font_size
                            tb.is_body_text = True
                            text_blocks.append(tb)
                            block_no += 1
                            logger.info(f"[SUPPLEMENT] page={page_num}: 创建补充 TextBlock, text='{combined_text[:60]}', pdf_bbox={group_pdf_bbox}")

                        logger.info(f"[SUPPLEMENT] page={page_num}: 共创建 {len(groups)} 个补充 TextBlock")
                    else:
                        logger.debug(f"[SUPPLEMENT] page={page_num}: 所有 textline 均被已处理 LayoutBlock 覆盖")
                else:
                    logger.debug(f"[SUPPLEMENT] page={page_num}: overall_ocr_res 不可用或无 textline 数据")

                if use_formula:
                    formula_res_list = result.get("formula_res_list", [])
                    for formula_res in formula_res_list:
                        bbox = formula_res.get('bbox', []) if hasattr(formula_res, 'get') else getattr(formula_res, 'bbox', [])
                        latex = formula_res.get('latex', '') if hasattr(formula_res, 'get') else getattr(formula_res, 'latex', '') or getattr(formula_res, 'content', '')
                        latex = PaddleOcrExtractor._clean_latex(latex) if latex else latex
                        if not bbox or len(bbox) < 4 or not latex:
                            continue
                        x1, y1, x2, y2 = bbox
                        pdf_bbox = self._pixel_to_pdf_coords((float(x1), float(y1), float(x2), float(y2)), page_info)
                        bbox_height = pdf_bbox[3] - pdf_bbox[1]
                        estimated_font_size = max(6, min(36, bbox_height * 0.75))
                        tb = TextBlock(
                            block_no=block_no,
                            text=latex,
                            bbox=pdf_bbox,
                            block_type=0,
                            page_num=page_num,
                        )
                        tb.font_size = estimated_font_size
                        tb.is_formula = True
                        text_blocks.append(tb)
                        block_no += 1
                        has_formula = True
        except Exception as e:
            logger.error(f"步骤1处理第{page_num}页版面分析时出错: {e}", exc_info=True)

        logger.info(f"[LAYOUT_DEBUG] page={page_num}: {dict(sorted(label_counts.items()))}, "
                     f"text_blocks={len(text_blocks)}, image_regions={len(image_regions)}")

        return {
            'text_blocks': text_blocks,
            'has_table': has_table,
            'has_formula': has_formula,
            'image_regions': image_regions,
            'layout_bboxes': layout_bboxes,
            'tables': tables,
        }

    def extract_from_pdf(self, pdf_path, pages=None, temp_images_dir=None, status_callback=None):
        """从PDF中提取内容（分步加载策略）

        按步骤依次加载模型，每步完成后释放管线，降低峰值内存占用。

        Args:
            pdf_path (str): PDF文件路径
            pages (list[int] | None): 指定页码列表（1-based），None表示全部
            temp_images_dir (str | None): 临时图像目录

        Returns:
            PdfExtraction: 提取结果

        Raises:
            FileNotFoundError: PDF文件不存在
            ValueError: 参数无效
        """
        if not pdf_path:
            raise ValueError("PDF文件路径不能为空")

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        if temp_images_dir is None:
            temp_images_dir = os.path.join(os.getcwd(), 'temp_images')
        os.makedirs(temp_images_dir, exist_ok=True)

        with fitz.open(pdf_path) as doc:
            total_pages = len(doc)

            # 确定目标页码
            if pages:
                target_pages = [p for p in pages if 1 <= p <= total_pages]
            else:
                target_pages = list(range(1, total_pages + 1))

            logger.info(f"开始OCR提取PDF: {pdf_path}, 共{len(target_pages)}页")
            logger.info(f"OCR内存优化配置: OCR_SKIP_TABLE={self._skip_table}, OCR_SKIP_FORMULA={self._skip_formula}, OCR_RENDER_DPI={config.OCR_RENDER_DPI}")
            if self._skip_table or self._skip_formula:
                logger.info("提示: 部分OCR功能已跳过，若需完整功能请调整参数")

            # 渲染页面为图像（供后续OCR使用）
            page_images = self._render_pages(doc, target_pages, temp_images_dir)

            # 步骤1: 版面分析 + 文本OCR
            step1_start = time.time()
            self._log_memory("步骤1开始")
            if status_callback:
                status_callback('step_start', {'step': self.STEP_LAYOUT_OCR, 'step_name': self.STEP_LAYOUT_OCR_NAME, 'total_pages': len(target_pages)})
            layout_pipeline = None
            _step1_use_formula = not self._skip_formula
            if _step1_use_formula:
                try:
                    layout_pipeline = self._create_pipeline(use_table=not self._skip_table, use_formula=True, use_region_detection=False, cpu_threads=self.cpu_threads)
                except MemoryError as e:
                    logger.warning(f"步骤1启用公式识别时内存不足，回退到 use_formula=False: {e}")
                    _step1_use_formula = False
            if layout_pipeline is None:
                layout_pipeline = self._create_pipeline(use_table=not self._skip_table, use_formula=False, use_region_detection=False, cpu_threads=self.cpu_threads)
            self._log_memory("步骤1管线创建")
            all_layout_results = {}
            text_blocks_by_page = {}
            pages_done = 0
            for page_num in target_pages:
                try:
                    page_info = page_images[page_num]
                    img_path = page_info['img_path']
                    result = self._process_page_layout(
                        layout_pipeline, img_path, page_num, page_info,
                        use_formula=_step1_use_formula
                    )
                    text_blocks_by_page[page_num] = result['text_blocks']
                    all_layout_results[page_num] = result
                except Exception as e:
                    logger.error(
                        f"步骤1处理第{page_num}页时出错: {e}", exc_info=True
                    )
                    text_blocks_by_page[page_num] = []
                    all_layout_results[page_num] = {
                        'text_blocks': [],
                        'has_table': False,
                        'has_formula': False,
                        'image_regions': [],
                        'layout_bboxes': [],
                        'tables': [],
                    }
                pages_done += 1
                if status_callback:
                    status_callback('step_progress', {
                        'step': self.STEP_LAYOUT_OCR, 'step_name': self.STEP_LAYOUT_OCR_NAME,
                        'page_num': page_num,
                        'pages_done': pages_done, 'total_pages': len(target_pages),
                    })

            del layout_pipeline
            gc.collect()
            self._force_release_memory()

            slim_layout = {}
            for p, r in all_layout_results.items():
                slim_layout[p] = {
                    k: v for k, v in r.items()
                    if k in ('has_table', 'has_formula', 'image_regions', 'layout_bboxes', 'pixel_bbox', 'tables')
                }
            all_layout_results = slim_layout
            gc.collect()
            self._force_release_memory()

            step1_duration = time.time() - step1_start
            self._log_memory("步骤1完成")
            logger.info(f"步骤{self.STEP_LAYOUT_OCR}完成: {self.STEP_LAYOUT_OCR_NAME}，管线已释放，布局数据已精简")
            formula_detected_pages = [p for p, r in all_layout_results.items() if r.get('has_formula', False)]
            if formula_detected_pages:
                logger.info("步骤1检测到公式的页面: %s", formula_detected_pages)
            else:
                logger.info("步骤1未检测到公式页面")
            if status_callback:
                status_callback('step_complete', {'step': self.STEP_LAYOUT_OCR, 'step_name': self.STEP_LAYOUT_OCR_NAME, 'duration_sec': round(step1_duration, 1)})

            # 表格已在步骤1中提取
            tables = []
            for p, r in all_layout_results.items():
                tables.extend(r.get('tables', []))
            if tables:
                logger.info(f"步骤1提取到 {len(tables)} 个表格")
            else:
                logger.info("步骤1未检测到表格")

            # 步骤2: 图表/印章图像裁剪
            if status_callback:
                status_callback('step_start', {'step': self.STEP_IMAGE_CROP, 'step_name': self.STEP_IMAGE_CROP_NAME})
            chart_seal_images = []
            for page_num in target_pages:
                layout_data = all_layout_results.get(page_num, {})
                page_info = page_images[page_num]
                img_path = page_info['img_path']
                for region in layout_data.get('image_regions', []):
                    pixel_bbox = region.get('pixel_bbox', region['bbox'])
                    img = self._extract_image_for_region(
                        img_path, pixel_bbox, page_num,
                        len(chart_seal_images), temp_images_dir, page_info
                    )
                    if img:
                        chart_seal_images.append(img)
            logger.info(f"步骤2完成: 图表/印章裁剪，共{len(chart_seal_images)}张")
            self._log_memory("步骤2完成")
            if status_callback:
                status_callback('step_complete', {'step': self.STEP_IMAGE_CROP, 'step_name': self.STEP_IMAGE_CROP_NAME})

            # 合并结果
            pdf_pages = []
            for page_num in target_pages:
                page_text_blocks = text_blocks_by_page.get(page_num, [])
                for i, tb in enumerate(page_text_blocks):
                    tb.block_no = i
                pdf_pages.append(PdfPage(page_num=page_num, text_blocks=page_text_blocks))

            all_images = chart_seal_images
            # 重新编号 image_idx
            for i, img in enumerate(all_images):
                img.image_idx = i

            # 重新编号 table_idx
            for i, table in enumerate(tables):
                table.table_idx = i

            logger.info(
                f"OCR提取完成: 共{len(pdf_pages)}页, "
                f"{len(tables)}个表格, "
                f"{len(all_images)}个图像"
            )

            return PdfExtraction(
                total_pages=total_pages,
                pages=pdf_pages,
                tables=tables,
                images=all_images,
            )

    @staticmethod
    def _compute_table_grid(table_pixel_bbox, cells, textline_boxes, textline_texts):
        """为表格计算统一网格布局，更新单元格 bbox 和行列尺寸

        每个单元格的 bbox 基于累积行高/列宽计算，确保同行等高、同列等宽，
        网格线完美对齐，避免独立 tight bbox 导致的字体不一致和线条混乱问题。

        Args:
            table_pixel_bbox: 表格的像素坐标 bbox (x1,y1,x2,y2)
            cells: list[list[PdfCell]] 二维单元格列表
            textline_boxes: textline bbox 列表
            textline_texts: textline 文本列表

        Returns:
            tuple: (cells, row_heights, col_widths)
                - cells: 更新了 bbox 的单元格列表
                - row_heights: 每行的统一高度列表（像素）
                - col_widths: 每列的统一宽度列表（像素）
        """
        if not cells or textline_boxes is None or len(textline_boxes) == 0:
            return cells, [], []

        tx1, ty1, tx2, ty2 = table_pixel_bbox
        n_rows = len(cells)
        n_cols = max(len(row) for row in cells) if cells else 0
        if n_rows == 0 or n_cols == 0:
            return cells, [], []

        # 计算均匀行列区域（用于将 textline 分配到对应的行/列）
        row_height_avg = (ty2 - ty1) / n_rows
        col_width_avg = (tx2 - tx1) / n_cols

        # 收集每行/列的 textline bbox
        row_tight = [None] * n_rows  # (min_y1, max_y2)
        col_tight = [None] * n_cols  # (min_x1, max_x2)

        for row_idx in range(n_rows):
            cell_y1 = ty1 + row_idx * row_height_avg
            cell_y2 = ty1 + (row_idx + 1) * row_height_avg

            for col_idx in range(n_cols):
                cell_x1 = tx1 + col_idx * col_width_avg
                cell_x2 = tx1 + (col_idx + 1) * col_width_avg

                for tl_box in textline_boxes:
                    if len(tl_box) < 4:
                        continue
                    bx, by, bx2, by2 = float(tl_box[0]), float(tl_box[1]), float(tl_box[2]), float(tl_box[3])
                    cx, cy = (bx + bx2) / 2, (by + by2) / 2
                    if cell_x1 <= cx <= cell_x2 and cell_y1 <= cy <= cell_y2:
                        # 更新行 tight（同一行所有 textline 的 y 范围）
                        if row_tight[row_idx] is None:
                            row_tight[row_idx] = (by, by2)
                        else:
                            row_tight[row_idx] = (
                                min(row_tight[row_idx][0], by),
                                max(row_tight[row_idx][1], by2)
                            )
                        # 更新列 tight（同一列所有 textline 的 x 范围）
                        if col_tight[col_idx] is None:
                            col_tight[col_idx] = (bx, bx2)
                        else:
                            col_tight[col_idx] = (
                                min(col_tight[col_idx][0], bx),
                                max(col_tight[col_idx][1], bx2)
                            )

        # 计算最终行高和列宽（textline tight 优先，否则用平均值作为 fallback）
        row_heights = []
        for i in range(n_rows):
            if row_tight[i] is not None:
                h = row_tight[i][1] - row_tight[i][0]
                # 确保最小高度不低于平均行高的一半，避免过小的行
                h = max(h, row_height_avg * 0.5)
            else:
                h = row_height_avg
            row_heights.append(h)

        col_widths = []
        for j in range(n_cols):
            if col_tight[j] is not None:
                w = col_tight[j][1] - col_tight[j][0]
                w = max(w, col_width_avg * 0.5)
            else:
                w = col_width_avg
            col_widths.append(w)

        # 确保累积行高/列宽等于表格 bbox 的总高度/总宽度
        total_row_height = sum(row_heights)
        total_col_width = sum(col_widths)
        table_height = ty2 - ty1
        table_width = tx2 - tx1

        if total_row_height > 0 and abs(total_row_height - table_height) > 1:
            scale_y = table_height / total_row_height
            row_heights = [h * scale_y for h in row_heights]

        if total_col_width > 0 and abs(total_col_width - table_width) > 1:
            scale_x = table_width / total_col_width
            col_widths = [w * scale_x for w in col_widths]

        # 为每个单元格计算网格 bbox（累积行列尺寸）
        for row_idx, row in enumerate(cells):
            grid_y1 = ty1 + sum(row_heights[:row_idx])
            grid_y2 = grid_y1 + row_heights[row_idx]

            for col_idx, cell in enumerate(row):
                grid_x1 = tx1 + sum(col_widths[:col_idx])
                grid_x2 = grid_x1 + col_widths[col_idx]

                cell.bbox = (grid_x1, grid_y1, grid_x2, grid_y2)
                cell.width = grid_x2 - grid_x1
                cell.height = grid_y2 - grid_y1

        return cells, row_heights, col_widths

    def _parse_html_table(self, html):
        """解析HTML表格为PdfCell二维列表

        Args:
            html (str): HTML表格字符串

        Returns:
            list[list[PdfCell]] | None: 二维单元格列表
        """
        parser = _TableHtmlParser()
        parser.feed(html)

        if not parser.rows:
            return None

        cells = []
        for row_idx, row in enumerate(parser.rows):
            cell_row = [
                PdfCell(
                    text=cell_text,
                    bbox=(0, 0, 0, 0),  # OCR模式无单元格级精确bbox
                    row_idx=row_idx,
                    col_idx=col_idx
                )
                for col_idx, cell_text in enumerate(row)
            ]
            cells.append(cell_row)

        return cells

    def _extract_image_for_region(self, src_img_path, bbox, page_num,
                                  image_idx, temp_images_dir, page_info=None):
        """裁剪并保存图像区域

        Args:
            src_img_path (str): 源图像路径
            bbox (tuple): 区域边界框 (x1, y1, x2, y2)，像素坐标
            page_num (int): 页码
            image_idx (int): 图像索引
            temp_images_dir (str): 临时图像目录
            page_info (dict | None): 页面尺寸信息，用于坐标转换

        Returns:
            PdfImage | None: 提取的图像，失败返回None
        """
        try:

            # 保存原始像素坐标用于图像裁剪
            pixel_bbox = bbox

            # 转换为PDF点坐标用于PdfImage.bbox
            if page_info:
                pdf_bbox = self._pixel_to_pdf_coords(bbox, page_info)
            else:
                pdf_bbox = bbox

            x1, y1, x2, y2 = [int(v) for v in pixel_bbox]

            img = cv2.imread(src_img_path)
            if img is None:
                return None

            # 确保坐标不超出图像范围
            h, w = img.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            if x1 >= x2 or y1 >= y2:
                return None

            cropped = img[y1:y2, x1:x2]
            save_path = os.path.join(
                temp_images_dir, f"ocr_img_p{page_num}_{image_idx}.png"
            )
            cv2.imwrite(save_path, cropped)

            return PdfImage(
                page_num=page_num,
                image_idx=image_idx,
                image_path=save_path,
                bbox=pdf_bbox
            )
        except Exception as e:
            logger.warning(f"保存第{page_num}页图像区域失败: {e}")
            return None

