#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试被分割句子的合并判断
"""

import os
import sys
import logging
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.semantic_analyzer import SemanticAnalyzer

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_split_sentence_merge():
    """测试被分割句子的合并判断"""
    logger.info("开始测试被分割句子的合并判断")
    
    # 从环境变量获取API配置
    api_key = os.getenv('AIPING_API_KEY')
    api_url = os.getenv('AIPING_API_URL')
    model = os.getenv('AIPING_MODEL_TRANSLATION', 'Qwen3-32B')
    
    if not api_key:
        logger.error("缺少AIPING_API_KEY环境变量")
        return
    
    analyzer = SemanticAnalyzer(api_key=api_key, api_url=api_url, model=model)
    
    # 测试案例1：原始问题中的被分割句子
    text1 = "But how does this system actually work? What does an agent do from the moment it receives"
    text2 = "a request to the moment it delivers a result?"
    logger.info(f"测试案例1: 块1='{text1}', 块2='{text2}'")
    result = analyzer.analyze_semantic_relationship(text1, text2, 'en')
    logger.info(f"测试案例1结果: {result} (期望: True)")
    
    # 测试案例2：另一个被分割的句子
    text1 = "The system consists of several components that work together to"
    text2 = "achieve the desired outcome."
    logger.info(f"测试案例2: 块1='{text1}', 块2='{text2}'")
    result = analyzer.analyze_semantic_relationship(text1, text2, 'en')
    logger.info(f"测试案例2结果: {result} (期望: True)")
    
    # 测试案例3：完整句子，不应该合并
    text1 = "This is a complete sentence."
    text2 = "This is another complete sentence."
    logger.info(f"测试案例3: 块1='{text1}', 块2='{text2}'")
    result = analyzer.analyze_semantic_relationship(text1, text2, 'en')
    logger.info(f"测试案例3结果: {result} (期望: False)")

if __name__ == "__main__":
    logger.info("开始测试被分割句子的合并判断")
    test_split_sentence_merge()
    logger.info("测试完成")
