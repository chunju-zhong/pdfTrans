#!/usr/bin/env python3
"""
测试"翻译所有"选项是否包含Markdown下载
"""

import os
import sys
import requests
import json
import time
import uuid
import threading
import subprocess
from werkzeug.utils import secure_filename

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import config


def test_markdown_download():
    """测试"翻译所有"选项是否包含Markdown下载"""
    import pytest
    # 标记为集成测试
    pytest.mark.integration
    
    # 测试服务器URL和端口
    base_url = 'http://localhost:5001'
    port = 5001
    
    # 启动服务器
    server_process = None
    try:
        # 启动Flask应用作为后台进程
        server_process = subprocess.Popen(
            [sys.executable, 'app.py', '--port', str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        )
        
        # 等待服务器启动
        print("启动服务器...")
        time.sleep(3)  # 等待3秒让服务器启动
        
        # 检查服务器是否启动成功
        try:
            response = requests.get(f'{base_url}/', timeout=5)
            if response.status_code != 200:
                print(f"服务器启动失败，状态码: {response.status_code}")
                pytest.skip("服务器启动失败")
        except requests.RequestException as e:
            print(f"服务器启动失败: {e}")
            pytest.skip("服务器启动失败")
        
        print("服务器启动成功！")
        
        # 准备测试文件
        test_pdf_path = os.path.join(os.path.dirname(__file__), 'test_files', 'test.pdf')
        if not os.path.exists(test_pdf_path):
            # 如果测试文件不存在，创建一个简单的PDF文件
            import fitz  # PyMuPDF
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((100, 100), "这是一个测试PDF文件")
            page.insert_text((100, 150), "包含一些测试文本")
            os.makedirs(os.path.join(os.path.dirname(__file__), 'test_files'), exist_ok=True)
            doc.save(test_pdf_path)
            doc.close()
        
        print(f"使用测试文件: {test_pdf_path}")
        
        # 模拟上传文件
        with open(test_pdf_path, 'rb') as f:
            files = {'pdf_file': f}
            data = {
                'source_lang': 'en',
                'target_lang': 'zh',
                'translator': 'aiping',
                'doc_type': 'general',
                'glossary': '',
                'page_range': '',
                'output_format': 'all',  # 选择"翻译所有"选项
                'semantic_merge': 'on'
            }
            
            print("上传文件并启动翻译任务...")
            response = requests.post(f'{base_url}/translate', files=files, data=data)
            print(f"上传响应状态码: {response.status_code}")
            print(f"上传响应内容: {response.text}")
            
            if response.status_code != 200:
                print(f"上传失败: {response.text}")
                assert False, f"上传失败: {response.text}"
            
            # 解析响应
            response_data = response.json()
            if not response_data.get('success'):
                print(f"上传失败: {response_data.get('message')}")
                assert False, f"上传失败: {response_data.get('message')}"
            
            task_id = response_data.get('task_id')
            print(f"任务ID: {task_id}")
            
            # 轮询任务进度
            max_retries = 60  # 最大重试次数
            retry_interval = 2  # 重试间隔（秒）
            
            for i in range(max_retries):
                print(f"查询任务进度 ({i+1}/{max_retries})...")
                progress_response = requests.get(f'{base_url}/progress/{task_id}')
                
                if progress_response.status_code != 200:
                    print(f"查询进度失败: {progress_response.text}")
                    time.sleep(retry_interval)
                    continue
                
                progress_data = progress_response.json()
                print(f"任务状态: {progress_data.get('status')}")
                print(f"任务进度: {progress_data.get('progress')}%")
                print(f"任务消息: {progress_data.get('message')}")
                
                # 检查任务是否完成
                if progress_data.get('status') == 'completed':
                    print("任务完成！")
                    
                    # 检查返回的文件
                    result_file = progress_data.get('result_file')
                    attachments = progress_data.get('attachments', [])
                    
                    print(f"主要结果文件: {result_file}")
                    print(f"附件文件: {attachments}")
                    
                    # 检查是否包含Markdown文件
                    all_files = [result_file] + attachments
                    has_markdown = any(file.endswith('.zip') for file in all_files)
                    
                    print(f"所有返回的文件: {all_files}")
                    print(f"是否包含Markdown文件: {has_markdown}")
                    
                    assert has_markdown, "'翻译所有'选项不包含Markdown下载"
                    print("✓ 测试通过: '翻译所有'选项包含Markdown下载")
                    return
                
                # 检查任务是否失败
                if progress_data.get('status') == 'error':
                    print(f"任务失败: {progress_data.get('error')}")
                    assert False, f"任务失败: {progress_data.get('error')}"
                
                # 等待一段时间后再次查询
                time.sleep(retry_interval)
            
            print("任务超时，测试失败")
            assert False, "任务超时"
            
    finally:
        # 关闭服务器
        if server_process:
            print("关闭服务器...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
            print("服务器已关闭")


if __name__ == "__main__":
    success = test_markdown_download()
    sys.exit(0 if success else 1)
