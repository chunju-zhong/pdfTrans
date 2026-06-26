from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from models.extraction import PdfCell
from utils.logging_config import get_logger

logger = get_logger(__name__)


def _get_cell_span(cell):
    """获取单元格的 row_span 和 col_span，默认值为 1"""
    return getattr(cell, 'row_span', 1), getattr(cell, 'col_span', 1)


class TranslationTableHandler:
    """表格翻译：负责表格内容的翻译处理"""

    def __init__(self, executor: ThreadPoolExecutor):
        self.executor = executor

    def translate_tables(self, task, tables, translator, source_lang, target_lang, doc_type, glossary):
        """翻译表格内容

        Args:
            task: 任务对象
            tables: 提取的表格列表
            translator: 翻译器实例
            source_lang: 源语言
            target_lang: 目标语言
            doc_type: 文档类型
            glossary: 术语表

        Returns:
            list: 翻译后的表格列表
        """

        translated_tables = []

        if not tables:
            return translated_tables

        if not task.update_phase_progress('table_translation', 0, '正在翻译表格内容...'):
            # 任务被取消，直接返回
            logger.info(f"任务 {task.task_id} 被取消")
            return None

        logger.info(f"任务 {task.task_id} 开始翻译表格内容")

        # 提交翻译任务并处理结果
        cell_results, total_cells = self._process_table_translation(task, tables, translator, source_lang, target_lang, doc_type, glossary)

        # 构建翻译后的表格
        translated_tables = self._build_translated_tables(task, tables, cell_results)

        logger.info(f"任务 {task.task_id} 表格翻译完成，共 {len(translated_tables)} 个表格")

        return translated_tables

    def _process_table_translation(self, task, tables, translator, source_lang, target_lang, doc_type, glossary):
        cell_results = {}
        results_lock = threading.Lock()
        translated_rows_count = 0
        total_rows = 0

        table_pages = {table_idx: table.page_num for table_idx, table in enumerate(tables)}

        future_to_row = {}

        for table_idx, table in enumerate(tables):
            logger.info(f"任务 {task.task_id} 处理表格 {table_idx}: 页码={table.page_num}, 行数={len(table.cells)}")

            for row_idx, row in enumerate(table.cells):
                has_content = any(cell and cell.text for cell in row)
                if has_content:
                    total_rows += 1
                    future_to_row[self.executor.submit(
                        self.translate_table_row, task, table_idx, row_idx, row,
                        translator, source_lang, target_lang, doc_type, glossary, table_pages
                    )] = (table_idx, row_idx)

        logger.info(f"任务 {task.task_id} 共提交 {total_rows} 行需要翻译的表格行")

        for future in as_completed(future_to_row):
            table_idx, row_idx = future_to_row[future]
            try:
                t_idx, r_idx, row_result, page_num = future.result()
                logger.info(f"任务 {task.task_id} 存储行翻译结果: 表格={t_idx}, 行={r_idx}, 单元格数={len(row_result)}")

                with results_lock:
                    if t_idx not in cell_results:
                        cell_results[t_idx] = {}
                    cell_results[t_idx][r_idx] = row_result

                    translated_rows_count += 1
                    if total_rows > 0:
                        phase_percent = int((translated_rows_count / total_rows) * 100)
                        task.update_phase_progress('table_translation', phase_percent, f'正在翻译表格: {translated_rows_count}/{total_rows} 行')

            except Exception as e:
                logger.error(f"任务 {task.task_id} 翻译表格行时出错: {str(e)}")
                table = tables[table_idx]
                row = table.cells[row_idx]
                if table_idx not in cell_results:
                    cell_results[table_idx] = {}
                fallback_result = {}
                for col_idx, cell in enumerate(row):
                    if cell and cell.text:
                        rs, cs = _get_cell_span(cell)
                        fallback_result[col_idx] = PdfCell(
                            text=cell.text,
                            bbox=cell.bbox,
                            row_idx=cell.row_idx,
                            col_idx=cell.col_idx,
                            row_span=rs,
                            col_span=cs
                        )
                cell_results[table_idx][row_idx] = fallback_result

        return cell_results, total_rows

    def _build_translated_tables(self, task, tables, cell_results):
        """构建翻译后的表格

        Args:
            task: 任务对象
            tables: 提取的表格列表
            cell_results: 翻译结果

        Returns:
            list: 翻译后的表格列表
        """

        translated_tables = []

        logger.info(f"任务 {task.task_id} 开始构建翻译后的表格，cell_results 包含 {len(cell_results)} 个表格")

        for table_idx, table in enumerate(tables):
            # 创建翻译后的单元格列表
            translated_cells = []
            logger.info(f"任务 {task.task_id} 构建表格 {table_idx}: 行数={len(table.cells)}")

            # 构建每一行
            for row_idx, row in enumerate(table.cells):
                translated_row = self.build_translated_row(task, row_idx, row, table_idx, cell_results)
                translated_cells.append(translated_row)

            # 创建翻译后的PdfTable对象
            # 使用copy方法复制表格对象，排除cells属性
            translated_table = table.copy(exclude_attrs=['cells'])
            # 更新cells为翻译后的内容
            translated_table.cells = translated_cells

            translated_tables.append(translated_table)
            logger.info(f"任务 {task.task_id} 表格 {table_idx} 构建完成")

        return translated_tables

    def translate_table_cell(self, task, table_idx, row_idx, col_idx, cell, translator, source_lang, target_lang, doc_type, glossary, table_pages):
        """翻译单个表格单元格

        Args:
            task: 任务对象
            table_idx: 表格索引
            row_idx: 行索引
            col_idx: 列索引
            cell: 单元格对象
            translator: 翻译器实例
            source_lang: 源语言
            target_lang: 目标语言
            doc_type: 文档类型
            glossary: 术语表
            table_pages: 表格页面信息字典

        Returns:
            tuple: (table_idx, row_idx, col_idx, translated_cell, page_num)
        """
        text_preview = cell.text[:50] + '...' if len(cell.text) > 50 else cell.text
        logger.info(f"任务 {task.task_id} 开始翻译单元格: 表格={table_idx}, 行={row_idx}, 列={col_idx}, 原文='{text_preview}'")

        # 调用翻译API
        translation_result = translator.translate(
            cell.text,
            source_lang,
            target_lang,
            doc_type=doc_type,
            glossary=glossary
        )
        translated_text = translation_result.content
        translated_preview = translated_text[:50] + '...' if len(translated_text) > 50 else translated_text

        logger.info(f"任务 {task.task_id} 单元格翻译完成: 表格={table_idx}, 行={row_idx}, 列={col_idx}, 译文='{translated_preview}'")

        # 检查是否被截断
        if translation_result.truncated:
            logger.warning(f"任务 {task.task_id} 表格单元格翻译被截断: {translation_result.truncation_info}")
            # 添加警告到任务对象
            task.add_warning("表格翻译被截断", {
                "process": "translation",
                "table_index": table_idx,
                "row_index": row_idx,
                "col_index": col_idx,
                "token_usage": translation_result.token_usage,
                "finish_reason": translation_result.finish_reason
            })
        # 创建翻译后的PdfCell对象
        rs, cs = _get_cell_span(cell)
        translated_cell = PdfCell(
            text=translated_text,
            bbox=cell.bbox,
            row_idx=cell.row_idx,
            col_idx=cell.col_idx,
            row_span=rs,
            col_span=cs
        )
        return table_idx, row_idx, col_idx, translated_cell, table_pages.get(table_idx, 0)

    def translate_table_row(self, task, table_idx, row_idx, row_cells, translator, source_lang, target_lang, doc_type, glossary, table_pages):
        non_empty_cells = []
        for col_idx, cell in enumerate(row_cells):
            if cell and cell.text:
                non_empty_cells.append((col_idx, cell.text))

        if not non_empty_cells:
            return table_idx, row_idx, {}, table_pages.get(table_idx, 0)

        SEPARATOR = "\n|||"
        joined_text = SEPARATOR.join(text for _, text in non_empty_cells)

        logger.info(f"任务 {task.task_id} 批量翻译行: 表格={table_idx}, 行={row_idx}, 单元格数={len(non_empty_cells)}")

        try:
            translation_result = translator.translate(
                joined_text,
                source_lang,
                target_lang,
                doc_type=doc_type,
                glossary=glossary
            )
            translated = translation_result.content

            if translation_result.truncated:
                logger.warning(f"任务 {task.task_id} 表格行翻译被截断: {translation_result.truncation_info}")
                task.add_warning("表格行翻译被截断", {
                    "process": "translation",
                    "table_index": table_idx,
                    "row_index": row_idx,
                    "token_usage": translation_result.token_usage,
                    "finish_reason": translation_result.finish_reason
                })

            parts = translated.split(SEPARATOR)

            # 检查分隔符数量是否匹配
            if len(parts) != len(non_empty_cells):
                logger.warning(f"任务 {task.task_id} 表格行翻译分隔符不匹配: 期望{len(non_empty_cells)}段, 实际{len(parts)}段, 回退到逐个翻译")
                # 逐个单元格翻译作为 fallback
                result = {}
                for col_idx, text in non_empty_cells:
                    cell = row_cells[col_idx]
                    rs, cs = _get_cell_span(cell)
                    try:
                        single_result = translator.translate(
                            text, source_lang, target_lang,
                            doc_type=doc_type, glossary=glossary
                        )
                        result[col_idx] = PdfCell(
                            text=single_result.content.strip(),
                            bbox=cell.bbox,
                            row_idx=cell.row_idx,
                            col_idx=cell.col_idx,
                            row_span=rs,
                            col_span=cs
                        )
                    except Exception as e:
                        logger.warning(f"任务 {task.task_id} 单个单元格翻译失败: {e}, 使用原文")
                        result[col_idx] = PdfCell(
                            text=text,
                            bbox=cell.bbox,
                            row_idx=cell.row_idx,
                            col_idx=cell.col_idx,
                            row_span=rs,
                            col_span=cs
                        )
                return table_idx, row_idx, result, table_pages.get(table_idx, 0)

            result = {}
            for i, (col_idx, original) in enumerate(non_empty_cells):
                cell = row_cells[col_idx]
                rs, cs = _get_cell_span(cell)
                if i < len(parts) and parts[i].strip():
                    result[col_idx] = PdfCell(
                        text=parts[i].strip(),
                        bbox=cell.bbox,
                        row_idx=cell.row_idx,
                        col_idx=cell.col_idx,
                        row_span=rs,
                        col_span=cs
                    )
                else:
                    result[col_idx] = PdfCell(
                        text=original,
                        bbox=cell.bbox,
                        row_idx=cell.row_idx,
                        col_idx=cell.col_idx,
                        row_span=rs,
                        col_span=cs
                    )
            return table_idx, row_idx, result, table_pages.get(table_idx, 0)
        except Exception as e:
            logger.warning(f"任务 {task.task_id} 表格行翻译失败: {e}")
            result = {}
            for col_idx, text in non_empty_cells:
                cell = row_cells[col_idx]
                rs, cs = _get_cell_span(cell)
                result[col_idx] = PdfCell(
                    text=text,
                    bbox=cell.bbox,
                    row_idx=cell.row_idx,
                    col_idx=cell.col_idx,
                    row_span=rs,
                    col_span=cs
                )
            return table_idx, row_idx, result, table_pages.get(table_idx, 0)

    def build_translated_row(self, task, row_idx, row, table_idx, cell_results):
        """构建翻译后的表格行

        Args:
            task: 任务对象
            row_idx: 行索引
            row: 原始行
            table_idx: 表格索引
            cell_results: 翻译结果字典

        Returns:
            list: 翻译后的行
        """
        translated_row = []

        for col_idx, cell in enumerate(row):
            if cell and cell.text:
                # 查找翻译结果
                has_translation = (table_idx in cell_results and
                                   row_idx in cell_results[table_idx] and
                                   col_idx in cell_results[table_idx][row_idx])

                if has_translation:
                    translated_cell = cell_results[table_idx][row_idx][col_idx]
                    cell_preview = translated_cell.text[:50] + '...' if len(translated_cell.text) > 50 else translated_cell.text
                    logger.info(f"任务 {task.task_id} 使用翻译结果: 表格={table_idx}, 行={row_idx}, 列={col_idx}, 内容='{cell_preview}'")
                else:
                    # 如果没有翻译结果，使用原文
                    rs, cs = _get_cell_span(cell)
                    text_preview = cell.text[:50] + '...' if len(cell.text) > 50 else cell.text
                    logger.warning(f"任务 {task.task_id} 未找到翻译结果，使用原文: 表格={table_idx}, 行={row_idx}, 列={col_idx}, 原文='{text_preview}'")
                    translated_cell = PdfCell(
                        text=cell.text,
                        bbox=cell.bbox,
                        row_idx=cell.row_idx,
                        col_idx=cell.col_idx,
                        row_span=rs,
                        col_span=cs
                    )
                translated_row.append(translated_cell)
            else:
                # 空单元格或合并覆盖位置
                if cell is None:
                    # 合并覆盖位置，保持 None
                    translated_row.append(None)
                else:
                    rs, cs = _get_cell_span(cell)
                    translated_cell = PdfCell(
                        text='',
                        bbox=cell.bbox if cell.bbox else (0, 0, 0, 0),
                        row_idx=cell.row_idx,
                        col_idx=cell.col_idx,
                        row_span=rs,
                        col_span=cs
                    )
                    translated_row.append(translated_cell)

        return translated_row
