# -*- coding: utf-8 -*-
from __future__ import annotations

"""LLM OCR表格解析器

负责解析HTML表格字符串，计算行列布局和单元格坐标。
复用modules.ocr.paddle_extractor中的_TableHtmlParser进行HTML解析，
通过内容权重迭代优化算法计算表格列宽和行高。
"""

import logging
import math

from models.extraction import PdfCell
from modules.extractors.coordinate_utils import estimate_text_display_width

logger = logging.getLogger(__name__)


class LlmTableParser:
    """LLM OCR表格解析器

    提供静态方法用于HTML表格解析和表格布局计算。
    """

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
                    cell_display_widths[(r, c)] = estimate_text_display_width(cell.text, font_size)

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

    @staticmethod
    def _parse_html_table(html, table_bbox=None):
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
            col_widths, row_heights, t_x0, t_y0 = LlmTableParser._compute_table_layout(matrix, n_rows, n_cols, table_bbox)
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
