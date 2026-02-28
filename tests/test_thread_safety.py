#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
线程安全性测试
"""

import threading
import time
import pytest
from services.translation_service import translation_service
from models.task import Task
from config import config

class TestThreadSafety:
    """线程安全性测试类"""
    
    def test_thread_safety_in_translation(self):
        """测试翻译过程中的线程安全性
        
        验证多线程环境下翻译结果的一致性和线程安全
        """
        # 创建测试任务
        task = Task("test_thread_safety", "test.pdf")
        
        # 创建模拟的文本块
        from models.text_block import TextBlock
        text_blocks = []
        
        # 创建多个文本块用于测试
        for i in range(15):  # 创建15个文本块
            text_block = TextBlock(
                block_no=i,
                text=f"This is test text {i} for thread safety testing.",
                bbox=(10, 10, 100, 20),
                page_num=1
            )
            text_block.update_style(
                font="Arial",
                font_size=12.0,
                color=0,
                flags=0
            )
            text_blocks.append(text_block)
        
        # 创建翻译器实例（使用模拟翻译器避免实际API调用）
        from models.result_types import TranslationResult
        class MockTranslator:
            """模拟翻译器，用于线程安全测试"""
            def translate(self, text, source_lang, target_lang, **kwargs):
                # 模拟翻译API调用的延迟
                time.sleep(0.05)  # 模拟50ms的翻译延迟
                from models.result_types import TruncationInfo
                return TranslationResult(
                    content=f"[翻译] {text}",
                    token_usage={},
                    finish_reason="",
                    truncation_info=TruncationInfo(truncated=False, token_usage={}, finish_reason="")
                )
        
        translator = MockTranslator()
        
        # 保存原始的MAX_WORKERS配置
        original_max_workers = config.MAX_WORKERS
        
        try:
            # 设置较大的线程池大小以充分测试线程安全性
            config.MAX_WORKERS = 15
            
            # 测试process_original_blocks方法的线程安全性
            page_dict, merged_translations, translated_blocks = translation_service.process_original_blocks(
                task=task,
                text_blocks=text_blocks,
                translator=translator,
                source_lang="en",
                target_lang="zh",
                doc_type="技术文档",
                glossary=""
            )
            
            # 验证翻译结果的完整性
            assert len(merged_translations) == 15, f"期望15个合并结果，实际得到{len(merged_translations)}个"
            assert translated_blocks == 15, f"期望翻译15个块，实际翻译{translated_blocks}个"
            
            # 验证每个页面的结果
            assert 1 in page_dict, "期望包含第1页的结果"
            assert len(page_dict[1].text_blocks) == 15, f"期望第1页有15个文本块，实际有{len(page_dict[1].text_blocks)}个"
            
            # 验证任务状态的线程安全性
            assert task.status == "pending", f"任务状态应该保持为pending，实际为{task.status}"
            assert task.progress <= 100, f"任务进度应该小于等于100，实际为{task.progress}"
            
            print("线程安全性测试通过: 所有翻译结果完整且一致")
            
        finally:
            # 恢复原始配置
            config.MAX_WORKERS = original_max_workers
    
    def test_task_progress_thread_safety(self):
        """测试任务进度更新的线程安全性
        
        验证多线程环境下任务进度更新的一致性
        """
        # 创建测试任务
        task = Task("test_progress_safety", "test.pdf")
        
        # 模拟多个线程同时更新任务进度
        def update_progress(thread_id):
            """更新任务进度的线程函数"""
            for i in range(10):
                progress = (thread_id * 10) + i
                task.update_progress(progress, f"Thread {thread_id}: {progress}%")
                time.sleep(0.01)  # 微小延迟增加线程竞争的可能性
        
        # 创建多个线程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=update_progress, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证任务进度的最终状态
        assert task.progress >= 0, f"任务进度应该大于等于0，实际为{task.progress}"
        assert task.progress <= 100, f"任务进度应该小于等于100，实际为{task.progress}"
        assert task.message is not None, "任务消息不应该为None"
        
        print("任务进度线程安全性测试通过: 进度更新一致且无错误")

if __name__ == "__main__":
    # 直接运行线程安全测试
    tester = TestThreadSafety()
    tester.test_thread_safety_in_translation()
    tester.test_task_progress_thread_safety()
