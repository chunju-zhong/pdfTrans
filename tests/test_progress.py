#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试进度条和任务管理功能
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.task import Task, TASK_STATUS
from services.task_service import task_service
from services.translation_service import translation_service
tasks = task_service.tasks  # 访问任务服务中的tasks字典

def test_task_creation():
    """测试Task类的创建"""
    task_id = "test_task_1"
    filename = "test.pdf"
    
    task = Task(task_id, filename)
    
    assert task.task_id == task_id
    assert task.filename == filename
    assert task.status == TASK_STATUS['PENDING']
    assert task.progress == 0
    assert task.message == '准备开始...'
    assert task.result_file is None
    assert task.error is None
    assert task.canceled is False

def test_task_update_progress():
    """测试任务进度更新"""
    task = Task("test_task_2", "test.pdf")
    
    # 更新进度
    result = task.update_progress(50, "正在处理...")
    
    assert result is True
    assert task.progress == 50
    assert task.message == "正在处理..."
    
    # 测试进度边界值
    task.update_progress(-10, "进度不应为负")
    assert task.progress == 0
    
    task.update_progress(150, "进度不应超过100")
    assert task.progress == 100

def test_task_cancel():
    """测试任务取消功能"""
    task = Task("test_task_3", "test.pdf")
    
    # 取消任务
    task.cancel()
    
    assert task.canceled is True
    assert task.status == TASK_STATUS['ERROR']
    assert task.message == "翻译已取消"
    assert task.error == "用户取消了翻译任务"
    
    # 测试取消后更新进度
    result = task.update_progress(50, "取消后不应更新进度")
    assert result is False
    assert task.progress == 0
    
    # 测试取消后设置结果
    result = task.set_result("result.pdf")
    assert result is False
    assert task.result_file is None

def test_task_status_transition():
    """测试任务状态转换"""
    task = Task("test_task_4", "test.pdf")
    
    # 初始状态
    assert task.status == TASK_STATUS['PENDING']
    
    # 设置为处理中
    task.set_status(TASK_STATUS['PROCESSING'])
    assert task.status == TASK_STATUS['PROCESSING']
    
    # 更新进度
    task.update_progress(50, "正在处理...")
    assert task.progress == 50
    
    # 设置为完成
    task.set_result("result.pdf")
    assert task.status == TASK_STATUS['COMPLETED']
    assert task.progress == 100
    assert task.result_file == "result.pdf"
    
    # 测试新任务
    task2 = Task("test_task_5", "test.pdf")
    task2.set_status(TASK_STATUS['PROCESSING'])
    task2.set_error("处理失败")
    assert task2.status == TASK_STATUS['ERROR']
    assert task2.error == "处理失败"

@pytest.fixture
def client():
    """创建测试客户端"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_translate_api(client):
    """测试翻译API"""
    # 准备测试文件
    test_file_path = os.path.join(os.path.dirname(__file__), 'data', 'test_data_en_text.pdf')
    
    with open(test_file_path, 'rb') as f:
        # 模拟表单提交
        data = {
            'source_lang': 'en',
            'target_lang': 'zh',
            'translator': 'baidu'
        }
        
        # 使用patch模拟文件保存和后续处理
        with patch.object(translation_service, 'process_translation') as mock_process:
            # 合并表单数据和文件数据
            form_data = {
                'source_lang': 'en',
                'target_lang': 'zh',
                'translator': 'baidu',
                'pdf_file': (f, 'test_data_en.pdf')
            }
            response = client.post('/translate', 
                                 data=form_data,
                                 content_type='multipart/form-data',
                                 buffered=True,
                                 follow_redirects=True)
            
            # 检查响应
            assert response.status_code == 200
            
            # 检查响应内容
            response_data = response.get_json()
            assert response_data['success'] is True
            assert 'task_id' in response_data
            assert response_data['message'] == '翻译任务已启动'
            
            # 检查任务是否被添加到任务列表
            task_id = response_data['task_id']
            assert task_id in tasks
            
            # 检查process_translation是否被调用
            mock_process.assert_called_once()

def test_progress_api(client):
    """测试进度查询API"""
    # 创建测试任务
    task_id = "test_task_api_1"
    task = Task(task_id, "test.pdf")
    task.set_status(TASK_STATUS['PROCESSING'])
    task.update_progress(50, "正在处理...")
    tasks[task_id] = task
    
    # 测试获取进度
    response = client.get(f'/progress/{task_id}')
    
    assert response.status_code == 200
    
    response_data = response.get_json()
    assert response_data['success'] is True
    assert response_data['task_id'] == task_id
    assert response_data['status'] == TASK_STATUS['PROCESSING']
    assert response_data['progress'] == 50
    assert response_data['message'] == "正在处理..."
    
    # 测试获取不存在的任务
    response = client.get('/progress/non_existent_task')
    assert response.status_code == 404
    response_data = response.get_json()
    assert response_data['success'] is False
    assert response_data['message'] == '任务不存在'

def test_cancel_api(client):
    """测试取消任务API"""
    # 创建测试任务
    task_id = "test_task_api_2"
    task = Task(task_id, "test.pdf")
    task.set_status(TASK_STATUS['PROCESSING'])
    task.update_progress(50, "正在处理...")
    tasks[task_id] = task
    
    # 测试取消任务
    response = client.post(f'/cancel/{task_id}')
    
    assert response.status_code == 200
    
    response_data = response.get_json()
    assert response_data['success'] is True
    assert response_data['message'] == '翻译任务已取消'
    
    # 检查任务是否被取消
    assert task.canceled is True
    assert task.status == TASK_STATUS['ERROR']
    
    # 测试取消不存在的任务
    response = client.post('/cancel/non_existent_task')
    assert response.status_code == 404
    response_data = response.get_json()
    assert response_data['success'] is False
    assert response_data['message'] == '任务不存在'

def test_task_cleanup():
    """测试任务清理"""
    # 创建多个测试任务
    for i in range(5):
        task_id = f"test_task_cleanup_{i}"
        task = Task(task_id, f"test_{i}.pdf")
        tasks[task_id] = task
    
    # 检查任务数量
    assert len(tasks) >= 5
    
    # 清理测试任务
    for i in range(5):
        task_id = f"test_task_cleanup_{i}"
        if task_id in tasks:
            del tasks[task_id]
    
    # 确认清理完成
    for i in range(5):
        task_id = f"test_task_cleanup_{i}"
        assert task_id not in tasks

if __name__ == "__main__":
    pytest.main([__file__])
