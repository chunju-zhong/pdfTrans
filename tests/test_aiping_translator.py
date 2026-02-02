#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Ping翻译模块测试
"""

import pytest
from unittest.mock import patch, MagicMock
from modules.aiping_translator import AipingTranslator

class TestAipingTranslator:
    """AI Ping翻译模块测试类"""
    
    def test_init(self):
        """测试AI Ping翻译器初始化
    
        验证AipingTranslator能够正确初始化，支持自定义模型参数。
        """
        api_key = "test_api_key"
        api_url = "https://test-api.aiping.cn/v1"
        model = "test-model"
    
        # 测试自定义初始化
        translator = AipingTranslator(api_key, api_url, model)
        assert translator.api_key == api_key
        assert translator.api_url == api_url
        assert translator.model == model
    
    @patch('modules.aiping_translator.OpenAI')
    def test_translate(self, mock_openai, sample_text, source_lang, target_lang, mock_translator_response):
        """测试AI Ping翻译功能
    
        验证AipingTranslator的translate方法能够正确调用API并返回翻译结果。
        """
        # 配置mock
        mock_client = MagicMock()
        mock_chat = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat = mock_chat
    
        # 模拟流式响应
        mock_translation = mock_translator_response["choices"][0]["message"]["content"]
        
        # 创建模拟的流式响应块
        class MockDelta:
            def __init__(self, content=None, reasoning_content=None):
                self.content = content
                self.reasoning_content = reasoning_content
        
        class MockChoice:
            def __init__(self, delta):
                self.delta = delta
        
        class MockChunk:
            def __init__(self, choices):
                self.choices = choices
        
        # 模拟流式响应：先返回思考内容，再返回翻译结果
        mock_chunks = [
            MockChunk([MockChoice(MockDelta(reasoning_content="思考中..."))]),
            MockChunk([MockChoice(MockDelta(content=mock_translation))])
        ]
        
        mock_chat.completions.create.return_value = mock_chunks
    
        # 创建翻译器实例
        translator = AipingTranslator("test_api_key", "https://test-api.aiping.cn/v1", "test-model")
    
        # 调用翻译方法
        result = translator.translate(sample_text, source_lang, target_lang, doc_type="AI技术", glossary=None)

        # 验证OpenAI客户端初始化
        mock_openai.assert_called_once()

        # 验证API调用
        mock_chat.completions.create.assert_called_once()

        # 验证翻译结果
        assert isinstance(result, str)
        assert result == mock_translation
    
    @patch('modules.aiping_translator.OpenAI')
    def test_translate_api_error(self, mock_openai, sample_text, source_lang, target_lang):
        """测试AI Ping翻译API错误处理
        
        验证AipingTranslator的translate方法在API返回错误时能够正确处理。
        """
        # 配置mock引发异常
        mock_client = MagicMock()
        mock_chat = MagicMock()
        mock_chat.completions.create.side_effect = Exception("API Error")
        mock_client.chat = mock_chat
        mock_openai.return_value = mock_client
        
        # 创建翻译器实例
        translator = AipingTranslator("test_api_key", "https://test-api.aiping.cn/v1", "test-model")
        
        # 验证抛出异常
        with pytest.raises(Exception):
            translator.translate(sample_text, source_lang, target_lang, doc_type="AI技术", glossary=None)
    
    def test_validate_language(self):
        """测试语言验证功能
        
        验证AipingTranslator能够正确验证语言代码。
        """
        translator = AipingTranslator("test_api_key", "https://test-api.aiping.cn/v1", "test-model")
        
        # 测试支持的语言
        assert translator._validate_language("en") is True
        assert translator._validate_language("zh") is True
        
        # 测试不支持的语言
        assert translator._validate_language("xx") is False
    
    def test_preprocess_text(self, sample_text):
        """测试文本预处理
        
        验证AipingTranslator的文本预处理功能。
        """
        translator = AipingTranslator("test_api_key", "https://test-api.aiping.cn/v1", "test-model")
        
        # 测试包含多余空格的文本
        raw_text = "   " + sample_text + "   \n  "
        processed_text = translator._preprocess_text(raw_text)
        
        # 验证预处理结果
        assert processed_text == "Hello, world! This is a test text for translation."
    
    @patch('modules.aiping_translator.OpenAI')
    @patch('time.sleep', return_value=None)
    def test_translate_with_retry(self, mock_sleep, mock_openai, sample_text, source_lang, target_lang, mock_translator_response):
        """测试AI Ping翻译重试机制
        
        验证AipingTranslator的translate方法在API调用失败时能够正确重试。
        """
        # 配置mock，前两次调用失败，第三次成功
        mock_client = MagicMock()
        mock_chat = MagicMock()
        
        # 模拟前两次调用引发异常，第三次成功
        def mock_create_side_effect(*args, **kwargs):
            class MockDelta:
                def __init__(self, content=None, reasoning_content=None):
                    self.content = content
                    self.reasoning_content = reasoning_content
            
            class MockChoice:
                def __init__(self, delta):
                    self.delta = delta
            
            class MockChunk:
                def __init__(self, choices):
                    self.choices = choices
            
            # 前两次调用失败
            if mock_create_side_effect.calls < 2:
                mock_create_side_effect.calls += 1
                raise Exception("API Timeout")
            # 第三次调用成功
            else:
                mock_translation = mock_translator_response["choices"][0]["message"]["content"]
                return [
                    MockChunk([MockChoice(MockDelta(reasoning_content="思考中..."))]),
                    MockChunk([MockChoice(MockDelta(content=mock_translation))])
                ]
        
        mock_create_side_effect.calls = 0
        mock_chat.completions.create.side_effect = mock_create_side_effect
        mock_client.chat = mock_chat
        mock_openai.return_value = mock_client
        
        # 创建翻译器实例
        translator = AipingTranslator("test_api_key", "https://test-api.aiping.cn/v1", "test-model")
        
        # 调用翻译方法
        result = translator.translate(sample_text, source_lang, target_lang, doc_type="AI技术", glossary=None)
        
        # 验证OpenAI客户端初始化
        mock_openai.assert_called_once()
        
        # 验证API调用了3次（2次失败+1次成功）
        assert mock_chat.completions.create.call_count == 3
        
        # 验证sleep被调用了2次（重试间隔）
        assert mock_sleep.call_count == 2
        
        # 验证翻译结果
        assert isinstance(result, str)
        assert result == mock_translator_response["choices"][0]["message"]["content"]