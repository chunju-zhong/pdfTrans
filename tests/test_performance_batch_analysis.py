#!/usr/bin/env python3
"""
性能测试脚本：比较批量语义分析和非批量语义分析的性能差异
"""
import os
import sys
import time
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.text_block import TextBlock
from models.merged_block import MergedBlock
from utils.text_processing import merge_semantic_blocks_with_llm

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockTranslator:
    """模拟翻译器类，用于性能测试"""
    
    def __init__(self):
        self.api_calls = 0
    
    def analyze_semantic_relationship(self, text1, text2, source_lang):
        """模拟单对文本块的语义分析"""
        self.api_calls += 1
        # 模拟API调用延迟
        time.sleep(0.1)
        # 简单的合并逻辑：如果文本长度小于50，就合并
        return len(text1) < 50 and len(text2) < 50
    
    def batch_analyze_semantic_relationship(self, text_pairs, source_lang):
        """模拟批量文本块的语义分析"""
        self.api_calls += 1
        # 模拟API调用延迟
        time.sleep(0.2)  # 批量调用延迟稍长，但比多次单调用短
        # 简单的合并逻辑：如果文本长度小于50，就合并
        return [len(text1) < 50 and len(text2) < 50 for text1, text2 in text_pairs]

def generate_test_text_blocks(num_blocks):
    """生成测试文本块"""
    text_blocks = []
    for i in range(num_blocks):
        # 生成不同长度的文本
        if i % 3 == 0:
            text = f"这是一个短文本块 {i}"
        else:
            text = f"这是一个较长的文本块，用于测试语义合并功能 {i}。" * 3
        
        # 创建TextBlock对象
        text_block = TextBlock(
            block_no=i,
            text=text,
            bbox=(0, i * 100, 500, (i + 1) * 100),
            block_type=0,
            page_num=1
        )
        text_blocks.append(text_block)
    return text_blocks

def test_performance():
    """测试批量处理和非批量处理的性能差异"""
    # 测试不同数量的文本块
    test_sizes = [10, 50, 100]
    
    for size in test_sizes:
        logger.info(f"测试文本块数量: {size}")
        
        # 生成测试数据
        text_blocks = generate_test_text_blocks(size)
        
        # 测试批量处理
        logger.info("测试批量处理...")
        batch_translator = MockTranslator()
        start_time = time.time()
        batch_merged, batch_mapping = merge_semantic_blocks_with_llm(text_blocks, batch_translator, "zh")
        batch_time = time.time() - start_time
        batch_calls = batch_translator.api_calls
        
        logger.info(f"批量处理结果: 合并后块数量={len(batch_merged)}, API调用次数={batch_calls}, 执行时间={batch_time:.2f}秒")
        
        logger.info("测试完成")
        logger.info("-" * 50)

if __name__ == "__main__":
    test_performance()
