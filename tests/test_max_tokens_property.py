#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 max_tokens 属性功能
"""

import unittest
from modules.aiping_semantic_analyzer import AipingSemanticAnalyzer
from modules.aiping_translator import AipingTranslator
from modules.markdown_generator import MarkdownGenerator
from modules.semantic_analyzer import SemanticAnalyzer
from modules.silicon_flow_translator import SiliconFlowTranslator

class TestMaxTokensProperty(unittest.TestCase):
    """测试 max_tokens 属性功能"""
    
    def setUp(self):
        """设置测试环境"""
        # 使用占位符 API 密钥和 URL
        self.api_key = "test_api_key"
        self.api_url = "https://api.example.com/v1"
        self.model = "test_model"
    
    def test_aiping_semantic_analyzer_max_tokens(self):
        """测试 AipingSemanticAnalyzer 的 max_tokens 属性"""
        analyzer = AipingSemanticAnalyzer(self.api_key, self.api_url, self.model)
        
        # 验证默认值
        self.assertEqual(analyzer.max_tokens, 1024)
        self.assertEqual(analyzer.batch_max_tokens, 2048)
        
        # 验证可以从外部设置
        analyzer.max_tokens = 4096
        analyzer.batch_max_tokens = 8192
        self.assertEqual(analyzer.max_tokens, 4096)
        self.assertEqual(analyzer.batch_max_tokens, 8192)
    
    def test_aiping_translator_max_tokens(self):
        """测试 AipingTranslator 的 max_tokens 属性"""
        translator = AipingTranslator(self.api_key, self.api_url, self.model)
        
        # 验证默认值
        self.assertEqual(translator.max_tokens, 8192)
        
        # 验证可以从外部设置
        translator.max_tokens = 4096
        self.assertEqual(translator.max_tokens, 4096)
    
    def test_markdown_generator_max_tokens(self):
        """测试 MarkdownGenerator 的 max_tokens 属性"""
        generator = MarkdownGenerator(self.api_key, self.api_url, self.model)
        
        # 验证默认值
        self.assertEqual(generator.max_tokens, 8192)
        
        # 验证可以从外部设置
        generator.max_tokens = 4096
        self.assertEqual(generator.max_tokens, 4096)
    
    def test_semantic_analyzer_max_tokens(self):
        """测试 SemanticAnalyzer 的 max_tokens 属性"""
        analyzer = SemanticAnalyzer(self.api_key, self.api_url, self.model)
        
        # 验证默认值
        self.assertEqual(analyzer.max_tokens, 1024)
        self.assertEqual(analyzer.batch_max_tokens, 2048)
        
        # 验证可以从外部设置
        analyzer.max_tokens = 4096
        analyzer.batch_max_tokens = 8192
        self.assertEqual(analyzer.max_tokens, 4096)
        self.assertEqual(analyzer.batch_max_tokens, 8192)
    
    def test_silicon_flow_translator_max_tokens(self):
        """测试 SiliconFlowTranslator 的 max_tokens 属性"""
        translator = SiliconFlowTranslator(self.api_key, self.api_url, self.model)
        
        # 验证默认值
        self.assertEqual(translator.max_tokens, 8192)
        
        # 验证可以从外部设置
        translator.max_tokens = 4096
        self.assertEqual(translator.max_tokens, 4096)

if __name__ == '__main__':
    unittest.main()