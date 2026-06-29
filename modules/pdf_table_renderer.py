"""PDF表格渲染器

负责在PDF页面上绘制翻译后的表格内容，包括：
- 单元格文本渲染（含字体选择、大小自适应）
- 单元格文本溢出处理（截断）
- 表格网格线绘制（含合并单元格遮挡处理）
"""

import fitz  # PyMuPDF
import logging

logger = logging.getLogger(__name__)


class PdfTableRenderer:
    """PDF表格渲染器，封装表格渲染相关的所有方法"""

    def __init__(self, pdf_generator):
        """初始化PdfTableRenderer对象

        Args:
            pdf_generator: PdfGenerator父实例，用于访问字体和辅助方法
        """
        self._pg = pdf_generator

    def _draw_translated_table(self, page, table, target_lang="zh"):
        """在页面上绘制翻译后的表格

        Args:
            page (fitz.Page): PDF页面对象
            table: PdfTable对象
            target_lang (str): 目标语言代码
        """
        table_cells = table.cells
        logger.info(
            f"[表格绘制] 接收到表格数据: 页码={table.page_num}, "
            f"表格索引={table.table_idx}, "
            f"cells行数={len(table_cells) if table_cells else 0}"
        )

        if not table_cells:
            logger.warning("[表格绘制] 表格数据为空，跳过绘制")
            return

        # 记录表格所有单元格内容
        logger.info("[表格绘制] 表格所有单元格内容预览:")
        for row_idx, row in enumerate(table_cells):
            for col_idx, cell in enumerate(row):
                if cell and hasattr(cell, 'text') and cell.text:
                    text_preview = (
                        cell.text[:30] + '...'
                        if len(cell.text) > 30
                        else cell.text
                    )
                    logger.info(
                        f"[表格绘制] 单元格 ({row_idx},{col_idx}): "
                        f"'{text_preview}'"
                    )

        n_rows = len(table_cells)
        n_cols = (
            max(len(row) for row in table_cells) if table_cells else 0
        )
        logger.info(
            f"[表格绘制] 开始绘制表格，共 {n_rows} 行 {n_cols} 列"
        )

        table_bbox = table.bbox
        logger.info(f"[TABLE_DIAG] 表格边界框: {table_bbox}")

        row_heights = table.row_heights
        col_widths = table.col_widths
        logger.info(f"行高: {row_heights}")
        logger.info(f"列宽: {col_widths}")

        if table_bbox:
            table_x0, table_y0, table_x1, table_y1 = table_bbox
        else:
            table_x0, table_y0 = 50, 50
            table_x1, table_y1 = (
                page.rect.width - 50, page.rect.height - 50
            )
            logger.warning(
                f"[表格绘制] 表格无有效 bbox，使用页面区域 fallback: "
                f"({table_x0},{table_y0},{table_x1},{table_y1})"
            )

        suitable_font = self._pg._get_suitable_font(
            page, 'GoogleSansText-Regular', target_lang
        )
        logger.info(
            f"适合的字体: 目标语言='{target_lang}', 选择='{suitable_font}'"
        )

        # ========== 第一遍：添加 redaction 标注 ==========
        self._apply_table_redactions(
            page, table_cells, n_rows, n_cols,
            table_bbox, row_heights, col_widths,
            table_x0, table_y0, table_x1, table_y1
        )

        # ========== 第二遍：插入翻译文本 ==========
        self._draw_table_cells(
            page, table_cells, n_rows, n_cols,
            suitable_font,
            table_bbox, row_heights, col_widths,
            table_x0, table_y0, table_x1, table_y1
        )

        # 绘制表格网格线
        self._draw_table_gridlines(
            page, table_cells, table_bbox,
            row_heights, col_widths,
            table_x0, table_y0, table_x1, table_y1
        )

        logger.info("表格绘制完成")

    def _apply_table_redactions(
        self, page, table_cells, n_rows, n_cols,
        table_bbox, row_heights, col_widths,
        table_x0, table_y0, table_x1, table_y1
    ):
        """为表格单元格添加redaction标注，准备删除原文"""
        for i, row in enumerate(table_cells):
            for j, cell in enumerate(row):
                if cell is None:
                    continue

                x0, y0, x1, y1 = self._get_cell_bbox(
                    cell, i, j, n_rows, n_cols,
                    table_bbox, row_heights, col_widths,
                    table_x0, table_y0, table_x1, table_y1
                )

                cell_bg_rect = fitz.Rect(
                    max(x0 - 2, 0),
                    y0,
                    min(x1 + 2, page.rect.width),
                    y1
                )
                page.add_redact_annot(cell_bg_rect, fill=(1, 1, 1))

        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
        logger.info(f"[表格绘制] 已执行 redaction 删除单元格原文")

    def _draw_table_cells(
        self, page, table_cells, n_rows, n_cols,
        suitable_font,
        table_bbox, row_heights, col_widths,
        table_x0, table_y0, table_x1, table_y1
    ):
        """绘制所有表格单元格的翻译文本"""
        for i, row in enumerate(table_cells):
            for j, cell in enumerate(row):
                if cell is None:
                    logger.debug(
                        f"[表格绘制] 单元格 ({i},{j}) 为 None"
                        f"（合并覆盖位置），跳过"
                    )
                    continue

                cell_text, cell_bbox = self._extract_cell_data(cell)

                x0, y0, x1, y1 = self._get_cell_bbox(
                    cell, i, j, n_rows, n_cols,
                    table_bbox, row_heights, col_widths,
                    table_x0, table_y0, table_x1, table_y1,
                    use_cell_bbox=cell_bbox
                )

                rect = fitz.Rect(x0, y0, x1, y1)
                cell_height = y1 - y0
                cell_width = x1 - x0

                if cell_text:
                    self._render_cell_text(
                        page, rect, cell_text, cell, i, j,
                        suitable_font, cell_width, cell_height
                    )

    def _render_cell_text(
        self, page, rect, cell_text, cell, row_idx, col_idx,
        suitable_font, cell_width, cell_height
    ):
        """渲染单个单元格的文本内容"""
        base_font_size = min(cell_height * 0.8, 12)
        logger.debug(
            f"单元格 ({row_idx},{col_idx}) 字体大小: {base_font_size:.2f}, "
            f"单元格高度: {cell_height:.2f}"
        )

        cell_estimated_lines = getattr(cell, 'estimated_lines', 0)
        if cell_estimated_lines > 0 and cell_height > 0:
            max_font_for_lines = cell_height / (cell_estimated_lines * 1.2)
            if max_font_for_lines < base_font_size:
                base_font_size = max(
                    max_font_for_lines, base_font_size * 0.5
                )

        max_attempts = 5
        success = False

        for attempt in range(1, max_attempts + 1):
            if attempt == 1:
                current_font_size = base_font_size
            else:
                current_font_size = base_font_size * (
                    1 - (attempt - 1) * 0.1
                )
                current_font_size = max(
                    current_font_size, base_font_size * 0.5
                )

            try:
                result = page.insert_textbox(
                    rect, cell_text,
                    fontname=suitable_font,
                    fontsize=current_font_size,
                    color=(0, 0, 0),
                    align=getattr(cell, 'alignment', 1),
                    lineheight=1.2
                )
                if result >= 0:
                    success = True
                    break
            except Exception as e:
                logger.error(
                    f"单元格 ({row_idx+1},{col_idx+1}) "
                    f"文本绘制异常: {str(e)}"
                )

        if not success:
            self._handle_cell_overflow(
                page, rect, cell_text, suitable_font,
                base_font_size, row_idx, col_idx,
                cell_width, cell_height
            )

    def _handle_cell_overflow(
        self, page, rect, cell_text, suitable_font,
        base_font_size, row_idx, col_idx, cell_width, cell_height
    ):
        """处理单元格文本溢出：截断或强制写入"""
        is_cjk = any(
            '一' <= ch <= '鿿'
            or '　' <= ch <= '〿'
            or '＀' <= ch <= '￯'
            for ch in cell_text
        )
        truncation_success = False
        truncation_font_size = base_font_size * 0.5

        if is_cjk:
            for n in range(len(cell_text) - 1, 0, -1):
                truncated = cell_text[:n] + "…"
                try:
                    result = page.insert_textbox(
                        rect, truncated,
                        fontname=suitable_font,
                        fontsize=truncation_font_size,
                        color=(0, 0, 0),
                        align=1,
                        lineheight=1.2
                    )
                    if result >= 0:
                        truncation_success = True
                        break
                except Exception:
                    continue
        else:
            words = cell_text.split()
            for n in range(len(words) - 1, 0, -1):
                truncated = " ".join(words[:n]) + "…"
                try:
                    result = page.insert_textbox(
                        rect, truncated,
                        fontname=suitable_font,
                        fontsize=truncation_font_size,
                        color=(0, 0, 0),
                        align=1,
                        lineheight=1.2
                    )
                    if result >= 0:
                        truncation_success = True
                        break
                except Exception:
                    continue

        if truncation_success:
            logger.warning(
                f"[表格溢出] 单元格 ({row_idx},{col_idx}): "
                f"文本='{cell_text[:50]}...', "
                f"单元格尺寸={cell_width:.1f}x{cell_height:.1f}, "
                f"处理方式=截断"
            )
        else:
            try:
                page.insert_textbox(
                    rect, cell_text,
                    fontname=suitable_font,
                    fontsize=base_font_size * 0.5,
                    color=(0, 0, 0),
                    align=1,
                    lineheight=1.2
                )
            except Exception as e:
                logger.error(
                    f"单元格 ({row_idx+1},{col_idx+1}) "
                    f"最后尝试绘制异常: {str(e)}"
                )
            logger.warning(
                f"[表格溢出] 单元格 ({row_idx},{col_idx}): "
                f"文本='{cell_text[:50]}...', "
                f"单元格尺寸={cell_width:.1f}x{cell_height:.1f}, "
                f"处理方式=强制写入"
            )

    def _draw_table_gridlines(
        self, page, table_cells, table_bbox,
        row_heights, col_widths,
        table_x0, table_y0, table_x1, table_y1
    ):
        """绘制表格网格线（外框 + 内部线条，跳过合并单元格内部）"""
        try:
            if not table_bbox:
                return

            table_rect = fitz.Rect(
                table_x0, table_y0, table_x1, table_y1
            )
            page.draw_rect(table_rect, color=(0, 0, 0), width=1)

            # 收集合并单元格信息
            h_line_blocked = {}
            v_line_blocked = {}
            merged_cells = []

            for row_idx, row in enumerate(table_cells):
                for col_idx, cell in enumerate(row):
                    if cell is None:
                        continue
                    row_span = getattr(cell, 'row_span', 1)
                    col_span = getattr(cell, 'col_span', 1)
                    if row_span > 1 or col_span > 1:
                        merged_cells.append(
                            (row_idx, col_idx, row_span, col_span)
                        )
                        logger.debug(
                            f"[网格线遮挡] 合并单元格 "
                            f"({row_idx},{col_idx}): "
                            f"row_span={row_span}, col_span={col_span}"
                        )
                    if row_span > 1:
                        for r in range(row_idx, row_idx + row_span - 1):
                            h_line_blocked.setdefault(r, []).append(
                                (col_idx, col_idx + col_span - 1)
                            )
                    if col_span > 1:
                        for c in range(col_idx, col_idx + col_span - 1):
                            v_line_blocked.setdefault(c, []).append(
                                (row_idx, row_idx + row_span - 1)
                            )

            # 收集边界信息
            h_boundaries = {}
            v_boundaries = {}
            for row_idx, col_idx, row_span, col_span in merged_cells:
                if col_span > 1:
                    if row_idx > 0:
                        h_boundaries.setdefault(
                            row_idx - 1, set()
                        ).update(
                            range(col_idx, col_idx + col_span)
                        )
                    bottom_boundary = row_idx + row_span - 1
                    h_boundaries.setdefault(
                        bottom_boundary, set()
                    ).update(range(col_idx, col_idx + col_span))

                if row_span > 1:
                    if col_idx > 0:
                        v_boundaries.setdefault(
                            col_idx - 1, set()
                        ).update(
                            range(row_idx, row_idx + row_span)
                        )
                    right_boundary = col_idx + col_span - 1
                    v_boundaries.setdefault(
                        right_boundary, set()
                    ).update(range(row_idx, row_idx + row_span))

            # 从遮挡信息中排除边界
            for r in list(h_line_blocked.keys()):
                h_line_blocked[r] = self._subtract_boundaries(
                    h_line_blocked[r], h_boundaries.get(r, set())
                )
                if not h_line_blocked[r]:
                    del h_line_blocked[r]

            for c in list(v_line_blocked.keys()):
                v_line_blocked[c] = self._subtract_boundaries(
                    v_line_blocked[c], v_boundaries.get(c, set())
                )
                if not v_line_blocked[c]:
                    del v_line_blocked[c]

            logger.debug(
                f"[网格线遮挡] h_line_blocked={h_line_blocked}"
            )
            logger.debug(
                f"[网格线遮挡] v_line_blocked={v_line_blocked}"
            )

            # 绘制水平线
            for row_i in range(len(row_heights) - 1):
                line_y = table_y0 + sum(row_heights[:row_i + 1])
                blocked_ranges = h_line_blocked.get(row_i, [])
                segments = self._pg._compute_visible_segments(
                    0, len(col_widths) - 1, blocked_ranges
                )
                for seg_start, seg_end in segments:
                    x_start = table_x0 + sum(col_widths[:seg_start])
                    x_end = table_x0 + sum(col_widths[:seg_end + 1])
                    page.draw_line(
                        fitz.Point(x_start, line_y),
                        fitz.Point(x_end, line_y),
                        color=(0, 0, 0), width=0.5
                    )

            # 绘制垂直线
            for col_j in range(len(col_widths) - 1):
                line_x = table_x0 + sum(col_widths[:col_j + 1])
                blocked_ranges = v_line_blocked.get(col_j, [])
                segments = self._pg._compute_visible_segments(
                    0, len(row_heights) - 1, blocked_ranges
                )
                for seg_start, seg_end in segments:
                    y_start = table_y0 + sum(row_heights[:seg_start])
                    y_end = table_y0 + sum(row_heights[:seg_end + 1])
                    page.draw_line(
                        fitz.Point(line_x, y_start),
                        fitz.Point(line_x, y_end),
                        color=(0, 0, 0), width=0.5
                    )

            logger.info(
                "表格网格线绘制完成（已跳过合并单元格内部）"
            )
        except Exception as e:
            logger.error(f"绘制表格网格线异常: {e}")

    @staticmethod
    def _subtract_boundaries(blocked_ranges, boundary_set):
        """从遮挡范围中排除边界位置"""
        if not boundary_set:
            return blocked_ranges
        result = []
        for start, end in blocked_ranges:
            current = start
            for pos in sorted(boundary_set):
                if pos < current:
                    continue
                if pos > end:
                    break
                if pos > current:
                    result.append((current, pos - 1))
                current = pos + 1
            if current <= end:
                result.append((current, end))
        return result

    @staticmethod
    def _extract_cell_data(cell):
        """从单元格对象中提取文本和边界框数据"""
        if isinstance(cell, dict):
            return cell.get('text', ''), cell.get('bbox')
        elif hasattr(cell, 'text') and hasattr(cell, 'bbox'):
            return cell.text, cell.bbox
        else:
            return str(cell), None

    def _get_cell_bbox(
        self, cell, row_idx, col_idx, n_rows, n_cols,
        table_bbox, row_heights, col_widths,
        table_x0, table_y0, table_x1, table_y1,
        use_cell_bbox=None
    ):
        """获取单元格的边界框坐标

        Args:
            use_cell_bbox: 可选的已知单元格bbox，优先使用

        Returns:
            tuple: (x0, y0, x1, y1)
        """
        if use_cell_bbox and not (
            use_cell_bbox[0] == 0
            and use_cell_bbox[1] == 0
            and use_cell_bbox[2] == 0
            and use_cell_bbox[3] == 0
        ):
            cx0, cy0, cx1, cy1 = use_cell_bbox
            cell_width = cx1 - cx0
            cell_height = cy1 - cy0
            if cell_width > 0 and cell_height > 0:
                return use_cell_bbox

        if table_bbox and row_heights and col_widths:
            x0 = table_x0 + sum(col_widths[:col_idx])
            y0 = table_y0 + sum(row_heights[:row_idx])
            row_span = (
                getattr(cell, 'row_span', 1)
                if hasattr(cell, 'row_span')
                else 1
            )
            col_span = (
                getattr(cell, 'col_span', 1)
                if hasattr(cell, 'col_span')
                else 1
            )
            if col_idx + col_span <= len(col_widths):
                cell_width = sum(
                    col_widths[col_idx:col_idx + col_span]
                )
            else:
                cell_width = (
                    col_widths[col_idx]
                    if col_idx < len(col_widths)
                    else 100
                )
            if row_idx + row_span <= len(row_heights):
                cell_height = sum(
                    row_heights[row_idx:row_idx + row_span]
                )
            else:
                cell_height = (
                    row_heights[row_idx]
                    if row_idx < len(row_heights)
                    else 30
                )
            x1 = x0 + cell_width
            y1 = y0 + cell_height
        else:
            cell_width = (
                (table_x1 - table_x0) / n_cols if n_cols > 0 else 100
            )
            cell_height = (
                (table_y1 - table_y0) / n_rows if n_rows > 0 else 30
            )
            x0 = table_x0 + col_idx * cell_width
            y0 = table_y0 + row_idx * cell_height
            x1 = x0 + cell_width
            y1 = y0 + cell_height

        return x0, y0, x1, y1
