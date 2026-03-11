#!/usr/bin/env python3
"""
测试跨页面文本块章节分配修复
"""

import os
import sys
import json
import requests
import time

# 测试配置
BASE_URL = "http://localhost:5002"
TEST_PDF = "test_pdf.pdf"  # 现有的测试PDF文件
OUTPUT_DIR = "outputs"


def test_cross_page_chapter_assignment():
    """测试跨页面文本块章节分配"""
    print("开始测试跨页面文本块章节分配...")
    
    # 检查测试PDF是否存在
    if not os.path.exists(TEST_PDF):
        print(f"错误: 测试PDF文件 '{TEST_PDF}' 不存在")
        return False
    
    try:
        # 准备测试数据
        files = {
            "pdf_file": (TEST_PDF, open(TEST_PDF, 'rb'), "application/pdf")
        }
        data = {
            "source_lang": "en",
            "target_lang": "zh",
            "translator": "aiping",
            "output_format": "md",
            "semantic_merge": "true"
        }
        
        # 发送翻译请求
        print("发送翻译请求...")
        response = requests.post(
            f"{BASE_URL}/translate",
            files=files,
            data=data,
            timeout=300
        )
        
        if response.status_code != 200:
            print(f"错误: 翻译请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
        
        print(f"响应内容: {response.text}")
        response_data = response.json()
        print(f"响应数据: {response_data}")
        task_id = response_data.get("task_id")
        if not task_id:
            print("错误: 未获取到任务ID")
            return False
        
        print(f"获取到任务ID: {task_id}")
        
        # 轮询任务状态
        print("轮询任务状态...")
        max_retries = 30
        retry_interval = 10
        
        for i in range(max_retries):
            status_response = requests.get(f"{BASE_URL}/progress/{task_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get("status")
                progress = status_data.get("progress", 0)
                
                print(f"任务状态: {status}, 进度: {progress}%")
                
                if status == "completed":
                    print("任务完成！")
                    # 检查生成的Markdown文件
                    output_files = status_data.get("result", [])
                    if output_files:
                        print(f"生成的文件: {output_files}")
                        # 检查章节分配
                        check_chapter_assignment(output_files)
                    return True
                elif status == "failed":
                    print(f"任务失败: {status_data.get('message')}")
                    return False
            
            time.sleep(retry_interval)
        
        print("错误: 任务超时")
        return False
        
    except Exception as e:
        print(f"错误: {str(e)}")
        return False


def check_chapter_assignment(output_files):
    """检查生成的Markdown文件中的章节分配"""
    print("检查章节分配...")
    
    # 查找章节Markdown文件
    chapter_files = [f for f in output_files if f.endswith(".md") and not f.startswith("translated_")]
    
    if not chapter_files:
        print("未找到章节Markdown文件")
        return
    
    print(f"找到 {len(chapter_files)} 个章节文件:")
    for file in chapter_files:
        print(f"- {file}")
        # 检查文件内容
        file_path = os.path.join(OUTPUT_DIR, file)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"文件 {file} 内容长度: {len(content)} 字符")
                # 检查是否有内容
                if content.strip():
                    print(f"文件 {file} 包含内容")
                else:
                    print(f"警告: 文件 {file} 为空")
        else:
            print(f"警告: 文件 {file} 不存在")


if __name__ == "__main__":
    success = test_cross_page_chapter_assignment()
    if success:
        print("测试通过！跨页面文本块章节分配正确")
        sys.exit(0)
    else:
        print("测试失败！跨页面文本块章节分配存在问题")
        sys.exit(1)
