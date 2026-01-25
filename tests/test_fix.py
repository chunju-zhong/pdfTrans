#!/usr/bin/env python3

import os
import sys
from services.translation_service import TranslationService
from models.task import Task
from config import config

# 测试脚本：直接调用translation_service来测试修复后的代码

class TestTask:
    def __init__(self, task_id, filename):
        self.task_id = task_id
        self.filename = filename
        self.status = 'pending'
        self.progress = 0
        self.message = ''
        self.result_file = None
        self.error = None
        self.canceled = False
    
    def set_status(self, status):
        self.status = status
        print(f"Task {self.task_id} status: {status}")
    
    def update_progress(self, progress, message):
        self.progress = progress
        self.message = message
        print(f"Task {self.task_id} progress: {progress}%, message: {message}")
        return not self.canceled
    
    def set_result(self, result_file):
        self.result_file = result_file
        print(f"Task {self.task_id} result: {result_file}")
    
    def set_error(self, error):
        self.error = error
        print(f"Task {self.task_id} error: {error}")
    
    def is_canceled(self):
        return self.canceled
    
    def set_canceled(self):
        self.canceled = True

def test_translation():
    # 创建翻译服务实例
    translation_service = TranslationService()
    
    # 测试文件路径
    test_file = '/Users/chunju/work/pdfTrans/tests/data/IntroductionToAgents.pdf'
    
    if not os.path.exists(test_file):
        print(f"测试文件不存在: {test_file}")
        return False
    
    # 创建测试任务
    task = TestTask('test-123', os.path.basename(test_file))
    
    # 先测试PDF提取模块是否能正确提取样式信息
    print("\n=== 测试PDF提取模块 ===")
    try:
        # 调用extract_page_text方法，提取第一页的文本块
        from modules.pdf_extractor import pdf_extractor
        pdf_page = pdf_extractor.extract_page_text(test_file, 1)
        
        # 打印提取的文本块数量
        print(f"提取到 {len(pdf_page.text_blocks)} 个文本块")
        
        # 检查每个文本块的样式信息
        for i, text_block in enumerate(pdf_page.text_blocks):
            print(f"\n文本块 {i+1}:")
            print(f"  文本: '{text_block.block_text[:50]}...'")
            print(f"  字体: '{text_block.font}'")
            print(f"  大小: {text_block.font_size}")
            print(f"  粗体: {text_block.bold}")
            print(f"  斜体: {text_block.italic}")
    except Exception as e:
        print(f"提取测试出错: {e}")
    
    print("\n=== 测试翻译服务模块 ===")
    try:
        # 调用翻译服务
        translation_service.process_translation(
            task=task,
            input_filepath=test_file,
            source_lang='en',
            target_lang='zh',
            translator_type='aiping',
            unique_id='test123',
            filename=os.path.basename(test_file)
        )
        
        print("翻译完成，结果文件:", task.result_file)
        return True
    except Exception as e:
        print(f"翻译出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 设置环境变量
    os.environ['FLASK_ENV'] = 'development'
    
    # 运行测试
    success = test_translation()
    sys.exit(0 if success else 1)
