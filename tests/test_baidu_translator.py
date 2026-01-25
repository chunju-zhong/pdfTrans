#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度翻译模块测试
"""

import pytest
from unittest.mock import patch, MagicMock
from modules.baidu_translator import BaiduTranslator

class TestBaiduTranslator:
    """百度翻译模块测试类"""
    
    def test_init(self):
        """测试百度翻译器初始化
        
        验证BaiduTranslator能够正确初始化。
        """
        app_id = "test_app_id"
        app_key = "test_app_key"
        
        translator = BaiduTranslator(app_id, app_key)
        
        # 验证初始化参数
        assert translator.app_id == app_id
        assert translator.api_key == app_key
    
    @patch('modules.baidu_translator.requests.get')
    def test_translate(self, mock_get, sample_text, source_lang, target_lang, mock_baidu_translator_response):
        """测试百度翻译功能
        
        验证BaiduTranslator的translate方法能够正确调用API并返回翻译结果。
        """
        # 配置mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_baidu_translator_response
        mock_get.return_value = mock_response
        
        # 创建翻译器实例
        translator = BaiduTranslator("test_app_id", "test_app_key")
        
        # 调用翻译方法
        result = translator.translate(sample_text, source_lang, target_lang)
        
        # 验证API调用
        mock_get.assert_called_once()
        
        # 验证翻译结果
        assert isinstance(result, str)
        assert len(result) > 0
    
    @patch('modules.baidu_translator.requests.get')
    def test_translate_api_error(self, mock_get, sample_text, source_lang, target_lang):
        """测试百度翻译API错误处理
        
        验证BaiduTranslator的translate方法在API返回错误时能够正确处理。
        """
        # 配置mock返回错误响应
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Invalid API key"}
        mock_get.return_value = mock_response
        
        # 创建翻译器实例
        translator = BaiduTranslator("test_app_id", "test_app_key")
        
        # 验证抛出异常
        with pytest.raises(Exception):
            translator.translate(sample_text, source_lang, target_lang)
    
    @patch('modules.baidu_translator.requests.get')
    def test_translate_network_error(self, mock_get, sample_text, source_lang, target_lang):
        """测试网络错误处理
        
        验证BaiduTranslator的translate方法在遇到网络错误时能够正确处理。
        """
        # 配置mock引发网络异常
        mock_get.side_effect = Exception("Network error")
        
        # 创建翻译器实例
        translator = BaiduTranslator("test_app_id", "test_app_key")
        
        # 验证抛出异常
        with pytest.raises(Exception):
            translator.translate(sample_text, source_lang, target_lang)
    
    def test_validate_language(self):
        """测试语言验证功能
        
        验证BaiduTranslator能够正确验证语言代码。
        """
        translator = BaiduTranslator("test_app_id", "test_app_key")
        
        # 测试支持的语言
        assert translator._validate_language("en") is True
        assert translator._validate_language("zh") is True
        
        # 测试不支持的语言
        assert translator._validate_language("xx") is False
    
    def test_preprocess_text(self, sample_text):
        """测试文本预处理
        
        验证BaiduTranslator的文本预处理功能。
        """
        translator = BaiduTranslator("test_app_id", "test_app_key")
        
        # 测试包含多余空格的文本
        raw_text = "   " + sample_text + "   \n  "
        processed_text = translator._preprocess_text(raw_text)
        
        # 验证预处理结果
        assert processed_text == sample_text