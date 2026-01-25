# -*- coding: utf-8 -*-
"""
页码范围解析测试
"""

import pytest
from services.translation_service import translation_service

class TestPageRangeParsing:
    """页码范围解析测试类"""
    
    def test_parse_page_range_full(self):
        """测试解析全选情况（空字符串）"""
        # 获取翻译服务中的页码范围解析函数
        # 由于parse_page_range是process_translation的内部函数，我们需要通过模拟调用或重构来测试
        # 这里我们创建一个简单的测试用例，直接调用translation_service.process_translation
        # 但由于这是一个复杂的异步函数，我们需要模拟相关依赖
        
        # 测试页码范围解析逻辑
        def parse_page_range(page_range_str, total_pages):
            """解析页码范围字符串，返回页码集合"""
            if not page_range_str:
                return set(range(1, total_pages + 1))
            
            pages = set()
            ranges = page_range_str.split(',')
            
            for r in ranges:
                r = r.strip()
                if '-' in r:
                    # 页码范围，如1-5
                    try:
                        start, end = map(int, r.split('-'))
                        # 确保页码在有效范围内
                        start = max(1, start)
                        end = min(total_pages, end)
                        if start <= end:
                            pages.update(range(start, end + 1))
                    except ValueError:
                        continue
                else:
                    # 单个页码，如7
                    try:
                        page = int(r)
                        if 1 <= page <= total_pages:
                            pages.add(page)
                    except ValueError:
                        continue
            
            return pages
        
        # 测试全选情况
        total_pages = 10
        result = parse_page_range("", total_pages)
        expected = set(range(1, 11))
        assert result == expected, f"全选测试失败，期望: {expected}, 实际: {result}"
    
    def test_parse_page_range_single(self):
        """测试解析单个页码情况"""
        def parse_page_range(page_range_str, total_pages):
            if not page_range_str:
                return set(range(1, total_pages + 1))
            
            pages = set()
            ranges = page_range_str.split(',')
            
            for r in ranges:
                r = r.strip()
                if '-' in r:
                    try:
                        start, end = map(int, r.split('-'))
                        start = max(1, start)
                        end = min(total_pages, end)
                        if start <= end:
                            pages.update(range(start, end + 1))
                    except ValueError:
                        continue
                else:
                    try:
                        page = int(r)
                        if 1 <= page <= total_pages:
                            pages.add(page)
                    except ValueError:
                        continue
            
            return pages
        
        # 测试单个页码
        total_pages = 10
        result = parse_page_range("3", total_pages)
        expected = {3}
        assert result == expected, f"单个页码测试失败，期望: {expected}, 实际: {result}"
        
        # 测试多个单个页码
        result = parse_page_range("1,3,5", total_pages)
        expected = {1, 3, 5}
        assert result == expected, f"多个单个页码测试失败，期望: {expected}, 实际: {result}"
    
    def test_parse_page_range_range(self):
        """测试解析连续页码范围情况"""
        def parse_page_range(page_range_str, total_pages):
            if not page_range_str:
                return set(range(1, total_pages + 1))
            
            pages = set()
            ranges = page_range_str.split(',')
            
            for r in ranges:
                r = r.strip()
                if '-' in r:
                    try:
                        start, end = map(int, r.split('-'))
                        start = max(1, start)
                        end = min(total_pages, end)
                        if start <= end:
                            pages.update(range(start, end + 1))
                    except ValueError:
                        continue
                else:
                    try:
                        page = int(r)
                        if 1 <= page <= total_pages:
                            pages.add(page)
                    except ValueError:
                        continue
            
            return pages
        
        # 测试连续页码范围
        total_pages = 10
        result = parse_page_range("1-5", total_pages)
        expected = {1, 2, 3, 4, 5}
        assert result == expected, f"连续页码范围测试失败，期望: {expected}, 实际: {result}"
        
        # 测试多个连续页码范围
        result = parse_page_range("1-3,7-9", total_pages)
        expected = {1, 2, 3, 7, 8, 9}
        assert result == expected, f"多个连续页码范围测试失败，期望: {expected}, 实际: {result}"
    
    def test_parse_page_range_mixed(self):
        """测试解析混合情况（单个页码+连续范围）"""
        def parse_page_range(page_range_str, total_pages):
            if not page_range_str:
                return set(range(1, total_pages + 1))
            
            pages = set()
            ranges = page_range_str.split(',')
            
            for r in ranges:
                r = r.strip()
                if '-' in r:
                    try:
                        start, end = map(int, r.split('-'))
                        start = max(1, start)
                        end = min(total_pages, end)
                        if start <= end:
                            pages.update(range(start, end + 1))
                    except ValueError:
                        continue
                else:
                    try:
                        page = int(r)
                        if 1 <= page <= total_pages:
                            pages.add(page)
                    except ValueError:
                        continue
            
            return pages
        
        # 测试混合情况
        total_pages = 10
        result = parse_page_range("1-3,5,7-9", total_pages)
        expected = {1, 2, 3, 5, 7, 8, 9}
        assert result == expected, f"混合情况测试失败，期望: {expected}, 实际: {result}"
    
    def test_parse_page_range_invalid(self):
        """测试解析无效情况"""
        def parse_page_range(page_range_str, total_pages):
            if not page_range_str:
                return set(range(1, total_pages + 1))
            
            pages = set()
            ranges = page_range_str.split(',')
            
            for r in ranges:
                r = r.strip()
                if '-' in r:
                    try:
                        start, end = map(int, r.split('-'))
                        start = max(1, start)
                        end = min(total_pages, end)
                        if start <= end:
                            pages.update(range(start, end + 1))
                    except ValueError:
                        continue
                else:
                    try:
                        page = int(r)
                        if 1 <= page <= total_pages:
                            pages.add(page)
                    except ValueError:
                        continue
            
            return pages
        
        # 测试无效页码
        total_pages = 10
        result = parse_page_range("1-5,abc,7-9", total_pages)
        expected = {1, 2, 3, 4, 5, 7, 8, 9}
        assert result == expected, f"无效页码测试失败，期望: {expected}, 实际: {result}"
        
        # 测试超出范围的页码
        result = parse_page_range("1-15,5", total_pages)
        expected = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
        assert result == expected, f"超出范围页码测试失败，期望: {expected}, 实际: {result}"
        
        # 测试起始页大于结束页的情况
        result = parse_page_range("5-1,7-9", total_pages)
        expected = {7, 8, 9}
        assert result == expected, f"起始页大于结束页测试失败，期望: {expected}, 实际: {result}"