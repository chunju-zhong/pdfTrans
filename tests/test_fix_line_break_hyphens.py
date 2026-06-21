# -*- coding: utf-8 -*-
"""fix_line_break_hyphens 函数测试"""

import pytest
from utils.text_processing import fix_line_break_hyphens


class TestFixLineBreakHyphens:
    """换行断词连字符修复测试"""

    def test_basic_fix(self):
        """基本断词连字符修复：his- torical → historical"""
        assert fix_line_break_hyphens("just a his- torical accident") == "just a historical accident"

    def test_multiple_fixes(self):
        """同一段文本中多处断词连字符修复"""
        assert fix_line_break_hyphens("his- torical para- digm dis- crete") == "historical paradigm discrete"

    def test_legitimate_hyphen_preserved(self):
        """合法连字符保持不变：next-token 不受影响"""
        assert fix_line_break_hyphens("next-token prediction") == "next-token prediction"

    def test_mixed_hyphens(self):
        """混合场景：断词连字符修复，合法连字符保留"""
        text = "his- torical next-token para- digm"
        assert fix_line_break_hyphens(text) == "historical next-token paradigm"

    def test_no_hyphens(self):
        """无连字符的文本保持不变"""
        text = "the quick brown fox jumps over the lazy dog"
        assert fix_line_break_hyphens(text) == text

    def test_empty_string(self):
        """空字符串返回空字符串"""
        assert fix_line_break_hyphens("") == ""

    def test_dashes_not_modified(self):
        """普通破折号不受影响"""
        text = "speech, video, etc."
        assert fix_line_break_hyphens(text) == text

    def test_single_word_break(self):
        """单个断词修复"""
        assert fix_line_break_hyphens("para- digm") == "paradigm"

    def test_hyphen_at_line_end_only(self):
        """连字符后无空格的情况不受影响"""
        assert fix_line_break_hyphens("self-attention mechanism") == "self-attention mechanism"

    def test_consecutive_breaks(self):
        """连续断词修复"""
        assert fix_line_break_hyphens("a- ba- ba") == "ababa"
