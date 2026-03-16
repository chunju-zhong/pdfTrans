#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试列表开头检测功能
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

def test_list_detection():
    """测试列表开头检测"""
    logger.info("开始测试列表开头检测")
    
    # 从环境变量获取API配置
    api_key = os.getenv('AIPING_API_KEY')
    api_url = os.getenv('AIPING_API_URL')
    model = os.getenv('AIPING_MODEL_TRANSLATION', 'Qwen3-32B')
    
    if not api_key:
        logger.error("缺少AIPING_API_KEY环境变量")
        return
    
    analyzer = SemanticAnalyzer(api_key=api_key, api_url=api_url, model=model)
    
    # 测试案例1：块2是列表开头，不应该合并
    text1 = "The system consists of several components:"
    text2 = "• Component 1: Core functionality"
    logger.info(f"测试案例1: 块1='{text1}', 块2='{text2}'")
    result = analyzer.analyze_semantic_relationship(text1, text2, 'en')
    logger.info(f"测试案例1结果: {result} (期望: False)")
    
    # 测试案例2：块2不是列表开头，应该合并
    text1 = "The system consists"
    text2 = "of multiple components"
    logger.info(f"测试案例2: 块1='{text1}', 块2='{text2}'")
    result = analyzer.analyze_semantic_relationship(text1, text2, 'en')
    logger.info(f"测试案例2结果: {result} (期望: True)")
    
    # 测试案例3：块2是数字列表开头，不应该合并
    text1 = "The steps are:"
    text2 = "1. First step"
    logger.info(f"测试案例3: 块1='{text1}', 块2='{text2}'")
    result = analyzer.analyze_semantic_relationship(text1, text2, 'en')
    logger.info(f"测试案例3结果: {result} (期望: False)")
    
    # 测试案例4：块2是破折号列表开头，不应该合并
    text1 = "The features include:"
    text2 = "- Feature 1"
    logger.info(f"测试案例4: 块1='{text1}', 块2='{text2}'")
    result = analyzer.analyze_semantic_relationship(text1, text2, 'en')
    logger.info(f"测试案例4结果: {result} (期望: False)")

if __name__ == "__main__":
    logger.info("开始测试列表开头检测")
    test_list_detection()
    logger.info("测试完成")
