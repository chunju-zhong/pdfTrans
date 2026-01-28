#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
硅基流动翻译模块测试
"""

import pytest
from unittest.mock import patch, MagicMock
from modules.silicon_flow_translator import SiliconFlowTranslator

class TestSiliconFlowTranslator:
    """硅基流动翻译模块测试类"""
    
    def test_init(self):
        """测试硅基流动翻译器初始化
    
        验证SiliconFlowTranslator能够正确初始化，支持自定义模型参数。
        """
        api_key = "test_api_key"
        api_url = "https://test-api.siliconflow.cn/v1"
        model = "test-model"
        default_api_url = "https://api.siliconflow.cn/v1"
        default_model = "tencent/Hunyuan-MT-7B"
    
        # 测试完整参数初始化
        translator = SiliconFlowTranslator(api_key, api_url, model)
        assert translator.api_key == api_key
        assert translator.api_url == api_url
        assert translator.model == model
    
    @patch('modules.silicon_flow_translator.OpenAI')
    def test_translate(self, mock_openai, sample_text, source_lang, target_lang, mock_translator_response):
        """测试硅基流动翻译功能
        
        验证SiliconFlowTranslator的translate方法能够正确调用API并返回翻译结果。
        """
        # 配置mock
        mock_client = MagicMock()
        mock_chat = MagicMock()
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        
        mock_message.content = mock_translator_response["choices"][0]["message"]["content"]
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        mock_chat.completions.create.return_value = mock_completion
        mock_client.chat = mock_chat
        mock_openai.return_value = mock_client
        
        # 创建翻译器实例
        api_key = "test_api_key"
        api_url = "https://api.siliconflow.cn/v1"
        model = "tencent/Hunyuan-MT-7B"
        translator = SiliconFlowTranslator(api_key, api_url, model)
        
        # 调用翻译方法
        result = translator.translate(sample_text, source_lang, target_lang, doc_type="AI技术", glossary=None)
        
        # 验证OpenAI客户端初始化
        mock_openai.assert_called_once()
        
        # 验证API调用
        mock_chat.completions.create.assert_called_once()
        
        # 验证翻译结果
        assert isinstance(result, str)
        assert result == mock_translator_response["choices"][0]["message"]["content"]
    
    @patch('modules.silicon_flow_translator.OpenAI')
    def test_translate_api_error(self, mock_openai, sample_text, source_lang, target_lang):
        """测试硅基流动翻译API错误处理
        
        验证SiliconFlowTranslator的translate方法在API返回错误时能够正确处理。
        """
        # 配置mock引发异常
        mock_client = MagicMock()
        mock_chat = MagicMock()
        mock_chat.completions.create.side_effect = Exception("API Error")
        mock_client.chat = mock_chat
        mock_openai.return_value = mock_client
        
        # 创建翻译器实例
        api_key = "test_api_key"
        api_url = "https://api.siliconflow.cn/v1"
        model = "tencent/Hunyuan-MT-7B"
        translator = SiliconFlowTranslator(api_key, api_url, model)
        
        # 验证抛出异常
        with pytest.raises(Exception):
            translator.translate(sample_text, source_lang, target_lang, doc_type="AI技术", glossary=None)
    
    def test_validate_language(self):
        """测试语言验证功能
        
        验证SiliconFlowTranslator能够正确验证语言代码。
        """
        api_key = "test_api_key"
        api_url = "https://api.siliconflow.cn/v1"
        model = "tencent/Hunyuan-MT-7B"
        translator = SiliconFlowTranslator(api_key, api_url, model)
        
        # 测试支持的语言
        assert translator._validate_language("en") is True
        assert translator._validate_language("zh") is True
        
        # 测试不支持的语言
        assert translator._validate_language("xx") is False
    
    def test_preprocess_text(self, sample_text):
        """测试文本预处理
        
        验证SiliconFlowTranslator的文本预处理功能。
        """
        api_key = "test_api_key"
        api_url = "https://api.siliconflow.cn/v1"
        model = "tencent/Hunyuan-MT-7B"
        translator = SiliconFlowTranslator(api_key, api_url, model)
        
        # 测试包含多余空格的文本
        raw_text = "   " + sample_text + "   \n  "
        processed_text = translator._preprocess_text(raw_text)
        
        # 验证预处理结果
        assert processed_text == "Hello, world! This is a test text for translation."