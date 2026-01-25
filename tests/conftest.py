#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试配置文件，用于定义测试fixture和配置
"""

import pytest
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def test_pdf_path():
    """返回测试PDF文件路径
    
    Returns:
        str: 测试PDF文件的绝对路径
    """
    return os.path.join(os.path.dirname(__file__), 'data', 'test_data_en.pdf')

@pytest.fixture
def invalid_pdf_path():
    """返回无效的PDF文件路径
    
    Returns:
        str: 不存在的PDF文件路径
    """
    return os.path.join(os.path.dirname(__file__), 'data', 'invalid_file.pdf')

@pytest.fixture
def mock_translator_response():
    """返回模拟的翻译API响应
    
    Returns:
        dict: 模拟的翻译API响应
    """
    return {
        "choices": [
            {
                "message": {
                    "content": "这是一个测试翻译结果"
                }
            }
        ]
    }

@pytest.fixture
def sample_text():
    """返回示例文本
    
    Returns:
        str: 用于测试的示例文本
    """
    return "Hello, world! This is a test text for translation."

@pytest.fixture
def source_lang():
    """返回源语言代码
    
    Returns:
        str: 源语言代码
    """
    return "en"

@pytest.fixture
def target_lang():
    """返回目标语言代码
    
    Returns:
        str: 目标语言代码
    """
    return "zh"

@pytest.fixture
def sample_translated_text():
    """返回示例翻译文本
    
    Returns:
        str: 示例翻译文本
    """
    return "你好，世界！这是一段用于翻译测试的文本。"

@pytest.fixture
def mock_baidu_translator_response():
    """返回模拟的百度翻译API响应
    
    Returns:
        dict: 模拟的百度翻译API响应
    """
    return {
        "from": "en",
        "to": "zh",
        "trans_result": [
            {
                "src": "Hello, world!",
                "dst": "你好，世界！"
            }
        ]
    }