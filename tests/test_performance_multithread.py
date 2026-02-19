#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多线程翻译性能测试
"""

import time
import pytest
from services.translation_service import translation_service
from models.task import Task
from modules.aiping_translator import AipingTranslator
from config import config

class TestPerformanceMultithread:
    """多线程翻译性能测试类"""
    
    def test_multithread_vs_serial_performance(self):
        """测试多线程翻译与串行翻译的性能对比
        
        由于需要实际调用翻译API，这里主要测试线程池的基本性能
        """
        # 创建测试任务
        task = Task("test_perf", "test.pdf")
        
        # 创建模拟的文本块
        from models.text_block import TextBlock
        text_blocks = []
        
        # 创建多个文本块用于测试
        for i in range(20):  # 创建20个文本块
            text_block = TextBlock(
                block_no=i,
                text=f"This is test text {i}. It contains some sample content for translation performance testing.",
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
        class MockTranslator:
            """模拟翻译器，用于性能测试"""
            def translate(self, text, source_lang, target_lang, **kwargs):
                # 模拟翻译API调用的延迟
                time.sleep(0.1)  # 模拟100ms的翻译延迟
                return f"[翻译] {text}"
        
        translator = MockTranslator()
        
        # 测试多线程翻译性能
        start_time = time.time()
        
        # 保存原始的MAX_WORKERS配置
        original_max_workers = config.MAX_WORKERS
        
        # 设置较大的线程池大小以充分测试并行性能
        config.MAX_WORKERS = 10
        
        try:
            # 测试process_original_blocks方法（多线程）
            page_dict, merged_translations, translated_blocks = translation_service.process_original_blocks(
                task=task,
                text_blocks=text_blocks,
                translator=translator,
                source_lang="en",
                target_lang="zh",
                doc_type="技术文档",
                glossary=""
            )
            
            multithread_time = time.time() - start_time
            print(f"多线程翻译时间: {multithread_time:.2f}秒")
            
            # 验证翻译结果
            assert len(merged_translations) == 20
            assert translated_blocks == 20
            
        finally:
            # 恢复原始配置
            config.MAX_WORKERS = original_max_workers
        
        # 验证多线程翻译确实比串行翻译快
        # 理论上，20个文本块，每个延迟0.1秒，串行应该需要约2秒
        # 多线程（10线程）应该需要约0.2秒
        assert multithread_time < 1.0, f"多线程翻译时间过长: {multithread_time:.2f}秒"
        
        print(f"性能测试通过: 多线程翻译时间 {multithread_time:.2f}秒")

if __name__ == "__main__":
    # 直接运行性能测试
    tester = TestPerformanceMultithread()
    tester.test_multithread_vs_serial_performance()
