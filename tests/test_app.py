#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试前端应用功能
"""

import os
import pytest
from app import app

class TestApp:
    """测试前端应用功能"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        app.config['TESTING'] = True
        app.config['UPLOAD_FOLDER'] = '/tmp'
        app.config['OUTPUT_FOLDER'] = '/tmp'
        
        with app.test_client() as client:
            yield client
    
    def test_index_page(self, client):
        """测试首页加载"""
        response = client.get('/')
        assert response.status_code == 200
        assert 'PDF翻译工具' in response.data.decode('utf-8')
    
    def test_translate_form_elements(self, client):
        """测试翻译表单包含文档类型和术语表输入字段"""
        response = client.get('/')
        assert 'doc_type' in response.data.decode('utf-8')
        assert 'glossary' in response.data.decode('utf-8')
    
    def test_translate_route_with_doc_type_glossary(self, client):
        """测试翻译路由支持文档类型和术语表参数"""
        # 准备测试文件
        test_file_path = os.path.join(app.root_path, 'tests', 'data', 'test_data_en_one_page.pdf')
        
        with open(test_file_path, 'rb') as f:
            data = {
                'source_lang': 'en',
                'target_lang': 'zh',
                'translator': 'silicon_flow',
                'doc_type': '技术文档',
                'glossary': 'AI agents: AI智能体\nLarge Language Model (LLM): 大语言模型（LLM）',
                'pdf_file': (f, 'test.pdf')
            }
            response = client.post('/translate', data=data, content_type='multipart/form-data')
            
        # 验证响应
        assert response.status_code == 200
        assert response.is_json
        result = response.get_json()
        assert result['success'] == True
        assert 'task_id' in result
    
    def test_translate_route_default_values(self, client):
        """测试翻译路由使用默认值"""
        # 准备测试文件
        test_file_path = os.path.join(app.root_path, 'tests', 'data', 'test_data_en_one_page.pdf')
        
        with open(test_file_path, 'rb') as f:
            data = {
                'source_lang': 'en',
                'target_lang': 'zh',
                'translator': 'silicon_flow',
                'pdf_file': (f, 'test.pdf')
            }
            response = client.post('/translate', data=data, content_type='multipart/form-data')
            
        # 验证响应
        assert response.status_code == 200
        assert response.is_json
        result = response.get_json()
        assert result['success'] == True
        assert 'task_id' in result
