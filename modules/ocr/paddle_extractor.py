# -*- coding: utf-8 -*-
"""PaddleOCR提取器

基于PaddleOCR PP-StructureV3的OCR提取器实现。
采用分步加载策略：每一步仅加载所需模型，处理完毕后立即释放，
避免同时加载所有模型导致内存溢出（2.5GB+）。

步骤1: 版面分析 + 文本OCR（~1400MB，处理完释放）
步骤2: 表格识别（~1300MB，仅对含表格的页面处理，处理完释放）
步骤3: 公式识别（~200MB，仅对含公式的页面处理，处理完释放）
步骤4: 图表/印章裁剪（无需额外模型）
"""

import gc
import os
import logging
import psutil
import fitz  # PyMuPDF，用于PDF转图像
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


class PaddleOcrExtractor(OcrExtractor):
    """基于PaddleOCR PP-StructureV3的OCR提取器（分步加载）

    使用分步加载策略，每一步仅创建所需功能的PPStructureV3管线，
    处理完毕后立即释放，避免同时加载所有模型导致内存溢出。

    - 步骤1: 版面分析 + 文本OCR → TextBlock
    - 步骤2: 表格识别 → PdfTable（仅含表格的页面）
    - 步骤3: 公式识别 → TextBlock（仅含公式的页面）
    - 步骤4: 图表/印章裁剪 → PdfImage
    """

    # 需要从parsing_res_list中提取文本的版面标签
    TEXT_LABELS = {
        'text', 'title', 'content', 'document_title', 'section_title',
        'abstract', 'references', 'reference', 'footnote',
        'header', 'footer', 'page_number',
        'sidebar_text', 'text_continue',
        'table_caption', 'table_footnote',
    }

    # 标记为非正文的标签
    NON_BODY_LABELS = {'header', 'footer', 'page_number', 'footnote'}

    # 需要保存为图片的版面标签
    IMAGE_LABELS = {'image', 'figure', 'chart', 'figure_caption', 'seal'}

    # 内存阈值系数与上限（字节）：动态 min(可用*0.55, 上限)
    MEMORY_FACTOR = 0.55
    MEMORY_CAP_LAYOUT = 1600 * 1024 * 1024   # 版面分析上限 1600MB
    MEMORY_CAP_TABLE = 1600 * 1024 * 1024     # 表格识别上限 1600MB
    MEMORY_CAP_FORMULA = 1000 * 1024 * 1024   # 公式识别上限 1000MB

    def __init__(self, lang='ch', use_gpu=True):
        """初始化PaddleOcrExtractor

        Args:
            lang (str): OCR识别语言代码，如 'ch', 'en', 'ja'
            use_gpu (bool): 是否使用GPU加速
        """
        self.lang = lang
        self.use_gpu = use_gpu
        self._actual_device = None  # 实际使用的设备

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
            return False

    def _log_memory(self, step_name):
        """记录当前进程内存使用"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            rss_mb = process.memory_info().rss / (1024 * 1024)
            logger.info(f"{step_name}: 内存使用 {rss_mb:.0f} MB")
        except Exception:
            pass

    def _create_pipeline(self, use_table=False, use_formula=False, use_region_detection=False):
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
        # 确定所需内存阈值：动态 min(可用内存*factor, cap)
        available = self._check_available_memory()
        if use_table:
            required = min(int(available * self.MEMORY_FACTOR), self.MEMORY_CAP_TABLE)
            step_name = "表格识别"
        elif use_formula:
            required = min(int(available * self.MEMORY_FACTOR), self.MEMORY_CAP_FORMULA)
            step_name = "公式识别"
        else:
            required = min(int(available * self.MEMORY_FACTOR), self.MEMORY_CAP_LAYOUT)
            step_name = "版面分析+文本OCR"

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
        logger.info(
            f"创建PP-StructureV3管线: lang={self.lang}, device={device}, "
            f"use_table={use_table}, use_formula={use_formula}"
        )

        try:
            from paddleocr import PPStructureV3
            self._log_memory(f"创建管线前(use_table={use_table}, use_formula={use_formula})")

            # 记录当前 root logger 状态，用于构造后恢复
            root_logger = logging.getLogger()
            root_level_before = root_logger.level
            root_handlers_before = list(root_logger.handlers)  # 保存 handler 引用

            pipeline = PPStructureV3(
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                use_table_recognition=use_table,
                use_formula_recognition=use_formula,
                use_region_detection=use_region_detection,
                device=device,
                lang=self.lang,
            )

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
        dpi = config.OCR_RENDER_DPI
        logger.info(f"OCR 渲染 DPI: {dpi} (可通过 OCR_RENDER_DPI 环境变量配置: 120默认|150质量优先)")
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

    def _process_page_layout(self, pipeline, img_path, page_num, page_info):
        """步骤1: 版面分析 + 文本OCR

        使用仅启用文本OCR的管线进行版面分析，提取文本块并记录布局信息。
        result 是 LayoutParsingResultV2（dict 子类），通过 result["key"] 访问数据。
        result["parsing_res_list"] 返回 LayoutBlock 列表，每个 block 有
        .label / .bbox / .content 属性。

        Args:
            pipeline: PPStructureV3管线实例
            img_path (str): 页面图像路径
            page_num (int): 页码（1-based）

        Returns:
            dict: {
                'text_blocks': list[TextBlock],
                'has_table': bool,
                'has_formula': bool,
                'image_regions': list[dict],  # 图表/印章区域信息
                'layout_bboxes': list[dict],  # 所有布局区域bbox信息
            }
        """
        text_blocks = []
        block_no = 0
        has_table = False
        has_formula = False
        image_regions = []
        layout_bboxes = []
        label_counts = {}

        try:
            for result in pipeline.predict(img_path):
                # result is LayoutParsingResultV2 (dict subclass)
                parsing_res_list = result.get("parsing_res_list", [])

                # 提取 textline 级别的 OCR 结果，用于准确估算字体大小
                textline_boxes = []  # [(x1, y1, x2, y2), ...]
                overall_ocr_res = result.get("overall_ocr_res")
                if overall_ocr_res is not None:
                    try:
                        rec_boxes = overall_ocr_res.get("rec_boxes") if hasattr(overall_ocr_res, "get") else getattr(overall_ocr_res, "rec_boxes", None)
                        if rec_boxes is not None and len(rec_boxes) > 0:
                            textline_boxes = rec_boxes
                            logger.info(f"[FONT_DEBUG] page={page_num}: 从 overall_ocr_res 获取到 {len(textline_boxes)} 个 textline bbox")
                    except Exception as e:
                        logger.debug(f"page={page_num}: 提取 overall_ocr_res 失败: {e}")

                for block in parsing_res_list:
                    label = block.label
                    label_counts[label] = label_counts.get(label, 0) + 1
                    bbox = block.bbox  # [x1, y1, x2, y2]
                    content = block.content  # text content

                    if not bbox or len(bbox) < 4:
                        continue

                    x1, y1, x2, y2 = bbox
                    layout_bboxes.append({
                        'bbox': self._pixel_to_pdf_coords((float(x1), float(y1), float(x2), float(y2)), page_info),
                        'label': label,
                    })

                    if label in self.TEXT_LABELS:
                        # Use block.content directly (already contains OCR text)
                        text = content or ''
                        if text.strip():
                            # Convert pixel bbox to PDF point coordinates
                            pixel_bbox = (float(x1), float(y1), float(x2), float(y2))
                            pdf_bbox = self._pixel_to_pdf_coords(pixel_bbox, page_info)

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

                    elif label in self.IMAGE_LABELS:
                        image_regions.append({
                            'bbox': self._pixel_to_pdf_coords((float(x1), float(y1), float(x2), float(y2)), page_info),
                            'pixel_bbox': (float(x1), float(y1), float(x2), float(y2)),
                            'label': label,
                        })
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
        }

    def _process_page_tables(self, pipeline, img_path, page_num, layout_data, page_info):
        """步骤2: 表格识别

        使用启用表格识别的管线，从页面中提取结构化表格。
        通过 result["table_res_list"] 直接获取表格识别结果，
        通过 result["parsing_res_list"] 获取表格区域的 bbox。

        Args:
            pipeline: PPStructureV3管线实例
            img_path (str): 页面图像路径
            page_num (int): 页码（1-based）
            layout_data (dict): 步骤1的布局分析结果

        Returns:
            list[PdfTable]: 提取的表格列表
        """
        tables = []
        table_idx = 0

        try:
            for result in pipeline.predict(img_path):
                table_res_list = result.get("table_res_list", [])
                for table_res in table_res_list:
                    # table_res is a result object, get HTML via .html property
                    html_dict = table_res.html if hasattr(table_res, 'html') else {}
                    html = html_dict.get('html', '') if isinstance(html_dict, dict) else str(html_dict)
                    if not html and hasattr(table_res, 'get'):
                        html = table_res.get('html', '')

                    if not html:
                        continue

                    # Get bbox from parsing_res_list for table blocks
                    bbox = (0, 0, 0, 0)
                    parsing_res_list = result.get("parsing_res_list", [])
                    for block in parsing_res_list:
                        if block.label == 'table':
                            bbox = self._pixel_to_pdf_coords(tuple(float(v) for v in block.bbox), page_info)
                            break

                    try:
                        cells = self._parse_html_table(html)
                        if cells:
                            tables.append(PdfTable(
                                page_num=page_num,
                                table_idx=table_idx,
                                cells=cells,
                                bbox=bbox,
                            ))
                            table_idx += 1
                    except Exception as e:
                        logger.warning(f"第{page_num}页表格HTML解析失败: {e}")
                        continue
        except Exception as e:
            logger.error(f"步骤2处理第{page_num}页表格识别时出错: {e}", exc_info=True)

        return tables

    def _process_page_formulas(self, pipeline, img_path, page_num, layout_data, page_info):
        """步骤3: 公式识别

        使用启用公式识别的管线，从页面中提取LaTeX公式。
        通过 result["formula_res_list"] 直接获取公式识别结果。

        Args:
            pipeline: PPStructureV3管线实例
            img_path (str): 页面图像路径
            page_num (int): 页码（1-based）
            layout_data (dict): 步骤1的布局分析结果

        Returns:
            list[TextBlock]: 公式文本块列表
        """
        formula_blocks = []

        try:
            for result in pipeline.predict(img_path):
                formula_res_list = result.get("formula_res_list", [])
                for formula_res in formula_res_list:
                    # formula_res has .bbox and .latex (or content)
                    bbox = formula_res.get('bbox', []) if hasattr(formula_res, 'get') else getattr(formula_res, 'bbox', [])
                    latex = formula_res.get('latex', '') if hasattr(formula_res, 'get') else getattr(formula_res, 'latex', '') or getattr(formula_res, 'content', '')

                    if not bbox or len(bbox) < 4 or not latex:
                        continue

                    x1, y1, x2, y2 = bbox
                    pdf_bbox = self._pixel_to_pdf_coords((float(x1), float(y1), float(x2), float(y2)), page_info)

                    # Estimate font_size from bbox height
                    bbox_height = pdf_bbox[3] - pdf_bbox[1]
                    estimated_font_size = max(6, min(36, bbox_height * 0.75))

                    tb = TextBlock(
                        block_no=0,  # 后续会重新编号
                        text=latex,
                        bbox=pdf_bbox,
                        block_type=0,
                        page_num=page_num,
                    )
                    tb.font_size = estimated_font_size
                    formula_blocks.append(tb)
        except Exception as e:
            logger.error(f"步骤3处理第{page_num}页公式识别时出错: {e}", exc_info=True)

        return formula_blocks

    def extract_from_pdf(self, pdf_path, pages=None, temp_images_dir=None):
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
            logger.info(f"OCR内存优化配置: OCR_SKIP_TABLE={config.OCR_SKIP_TABLE}, OCR_SKIP_FORMULA={config.OCR_SKIP_FORMULA}, OCR_RENDER_DPI={config.OCR_RENDER_DPI}")
            if config.OCR_SKIP_TABLE or config.OCR_SKIP_FORMULA:
                logger.info("提示: 部分OCR功能已通过环境变量跳过，若需完整功能请 unset OCR_SKIP_TABLE/OCR_SKIP_FORMULA")

            # 渲染页面为图像（供后续OCR使用）
            page_images = self._render_pages(doc, target_pages, temp_images_dir)

            # 步骤1: 版面分析 + 文本OCR
            self._log_memory("步骤1开始")
            layout_pipeline = self._create_pipeline(use_table=False, use_formula=False, use_region_detection=False)
            self._log_memory("步骤1管线创建")
            all_layout_results = {}  # page_num -> layout data
            text_blocks_by_page = {}
            for page_num in target_pages:
                try:
                    page_info = page_images[page_num]
                    img_path = page_info['img_path']
                    result = self._process_page_layout(
                        layout_pipeline, img_path, page_num, page_info
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
                    }

            del layout_pipeline
            gc.collect()
            self._log_memory("步骤1完成")
            logger.info("步骤1完成: 版面分析+文本OCR，管线已释放")

            # 步骤2: 表格识别（仅含表格的页面）
            if config.OCR_SKIP_TABLE:
                logger.info("OCR_SKIP_TABLE=True: 跳过表格识别")
                table_pages = {}
            else:
                table_pages = {
                    p: r for p, r in all_layout_results.items() if r['has_table']
                }
            tables = []
            if table_pages:
                try:
                    self._log_memory("步骤2开始")
                    table_pipeline = self._create_pipeline(
                        use_table=True, use_formula=False, use_region_detection=False
                    )
                    for page_num, layout_data in table_pages.items():
                        try:
                            page_info = page_images[page_num]
                            img_path = page_info['img_path']
                            page_tables = self._process_page_tables(
                                table_pipeline, img_path,
                                page_num, layout_data, page_info
                            )
                            tables.extend(page_tables)
                        except Exception as e:
                            logger.error(
                                f"步骤2处理第{page_num}页表格识别时出错: {e}",
                                exc_info=True,
                            )
                    del table_pipeline
                    gc.collect()
                    self._log_memory("步骤2完成")
                    logger.info("步骤2完成: 表格识别，管线已释放")
                except MemoryError as e:
                    logger.warning(f"步骤2跳过: {str(e)}")

            # 步骤3: 公式识别（仅含公式的页面）
            if config.OCR_SKIP_FORMULA:
                logger.info("OCR_SKIP_FORMULA=True: 跳过公式识别")
                formula_pages = {}
            else:
                formula_pages = {
                    p: r for p, r in all_layout_results.items() if r['has_formula']
                }
            formula_blocks = []
            if formula_pages:
                try:
                    self._log_memory("步骤3开始")
                    formula_pipeline = self._create_pipeline(
                        use_table=False, use_formula=True, use_region_detection=False
                    )
                    for page_num, layout_data in formula_pages.items():
                        try:
                            page_info = page_images[page_num]
                            img_path = page_info['img_path']
                            page_formulas = self._process_page_formulas(
                                formula_pipeline, img_path,
                                page_num, layout_data, page_info
                            )
                            formula_blocks.extend(page_formulas)
                        except Exception as e:
                            logger.error(
                                f"步骤3处理第{page_num}页公式识别时出错: {e}",
                                exc_info=True,
                            )
                    del formula_pipeline
                    gc.collect()
                    self._log_memory("步骤3完成")
                    logger.info("步骤3完成: 公式识别，管线已释放")
                except MemoryError as e:
                    logger.warning(f"步骤3跳过: {str(e)}")

            # 步骤4: 图表/印章图像裁剪
            chart_seal_images = []
            for page_num in target_pages:
                layout_data = all_layout_results.get(page_num, {})
                page_info = page_images[page_num]
                img_path = page_info['img_path']
                for region in layout_data.get('image_regions', []):
                    # 使用像素坐标进行裁剪
                    pixel_bbox = region.get('pixel_bbox', region['bbox'])
                    img = self._extract_image_for_region(
                        img_path, pixel_bbox, page_num,
                        len(chart_seal_images), temp_images_dir, page_info
                    )
                    if img:
                        chart_seal_images.append(img)
            logger.info(f"步骤4完成: 图表/印章裁剪，共{len(chart_seal_images)}张")
            self._log_memory("步骤4完成")

            # 合并结果
            pdf_pages = []
            for page_num in target_pages:
                page_text_blocks = text_blocks_by_page.get(page_num, [])
                page_formula_blocks = [
                    fb for fb in formula_blocks if fb.page_num == page_num
                ]
                all_page_blocks = page_text_blocks + page_formula_blocks
                # 重新编号 block_no
                for i, tb in enumerate(all_page_blocks):
                    tb.block_no = i
                pdf_pages.append(PdfPage(page_num=page_num, text_blocks=all_page_blocks))

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

            # 清理临时图像目录
            try:
                import shutil
                if temp_images_dir and os.path.exists(temp_images_dir):
                    shutil.rmtree(temp_images_dir, ignore_errors=True)
                    logger.info(f"已清理临时图像目录: {temp_images_dir}")
            except Exception as e:
                logger.warning(f"清理临时图像目录失败: {e}")

            return PdfExtraction(
                total_pages=total_pages,
                pages=pdf_pages,
                tables=tables,
                images=all_images,
            )

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
            import cv2

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

