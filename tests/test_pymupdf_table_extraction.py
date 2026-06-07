# -*- coding: utf-8 -*-
"""
测试 PyMuPDF 表格提取功能
"""

import os
import pytest
from modules.extractors.table_processor import extract_tables_by_pymupdf, extract_tables_by_camelot


def test_extract_tables_by_pymupdf_nonexistent_file():
    """测试处理不存在的文件"""
    nonexistent_path = "nonexistent_file.pdf"
    
    # 验证函数会抛出FileNotFoundError
    with pytest.raises(FileNotFoundError):
        extract_tables_by_pymupdf(nonexistent_path)


def test_extract_tables_by_pymupdf_interface():
    """测试函数接口一致性"""
    # 验证函数签名与extract_tables_by_camelot相同
    import inspect
    sig_pymupdf = inspect.signature(extract_tables_by_pymupdf)
    sig_camelot = inspect.signature(extract_tables_by_camelot)

    assert sig_pymupdf.parameters == sig_camelot.parameters, "函数参数应该相同"
    # pymupdf返回3个值（含page_table_cells），camelot返回2个值
    # 参数签名应该相同，返回值注解可以不同


def test_extract_tables_by_pymupdf_docstring():
    """测试函数文档字符串"""
    assert extract_tables_by_pymupdf.__doc__ is not None, "函数应该有文档字符串"
    assert "PDF文件路径" in extract_tables_by_pymupdf.__doc__, "文档字符串应该包含参数说明"
    assert "Returns:" in extract_tables_by_pymupdf.__doc__, "文档字符串应该包含返回值说明"

