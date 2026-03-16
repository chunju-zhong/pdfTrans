#!/usr/bin/env python3
"""
测试两阶段并行合并功能
验证parallel_batch_analyze和merge_semantic_blocks_with_llm_two_phase的正确性
"""
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.text_processing import parallel_batch_analyze, merge_semantic_blocks_with_llm_two_phase
from models.text_block import TextBlock

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MockSemanticAnalyzer:
    """模拟语义分析器"""

    def __init__(self, merge_all=False):
        self.merge_all = merge_all

    def batch_analyze_semantic_relationship(self, text_pairs, source_lang):
        """模拟批量语义分析，返回合并判断结果"""
        import time
        time.sleep(0.1)
        results = []
        for i, (text1, text2) in enumerate(text_pairs):
            if self.merge_all:
                results.append(True)
            else:
                results.append(i % 2 == 0)
        return results


class MockTextBlock:
    """模拟TextBlock对象"""

    def __init__(self, text, page_num=1, chapter_id=None, chapter_title=None):
        self.block_text = text
        self.page_num = page_num
        self.chapter_id = chapter_id
        self.chapter_title = chapter_title
        self.block_bbox = (0, 0, 100, 20)
        self.font = "Arial"
        self.font_size = 12.0
        self.color = 0
        self.flags = 0
        self.bold = False
        self.italic = False


def test_parallel_batch_analyze():
    """测试并行批量分析方法"""
    logger.info("=" * 50)
    logger.info("测试1: parallel_batch_analyze 方法")
    logger.info("=" * 50)

    analyzer = MockSemanticAnalyzer(merge_all=False)

    text_pairs = [
        ("Hello world", "This is a test"),
        ("Second pair", "Third text"),
        ("Fourth text", "Fifth text"),
        ("Sixth text", "Seventh text"),
        ("Eighth text", "Ninth text"),
        ("Tenth text", "Eleventh text"),
        ("Twelfth text", "Thirteenth text"),
        ("Fourteenth text", "Fifteenth text"),
        ("Sixteenth text", "Seventeenth text"),
        ("Eighteenth text", "Nineteenth text"),
        ("Twentieth text", "Twenty-first text"),
        ("Twenty-second text", "Twenty-third text"),
    ]

    results = parallel_batch_analyze(
        analyzer, text_pairs, "en",
        max_workers=3, batch_size=5
    )

    logger.info(f"输入文本对数量: {len(text_pairs)}")
    logger.info(f"输出结果数量: {len(results)}")
    logger.info(f"结果内容: {results}")

    assert len(results) == len(text_pairs), f"结果数量不匹配: {len(results)} vs {len(text_pairs)}"

    assert sum(results) > 0, "应该有一些True结果"
    assert len(results) - sum(results) > 0, "应该有一些False结果"

    logger.info("✅ parallel_batch_analyze 测试通过")
    return True


def test_parallel_batch_analyze_empty():
    """测试空输入"""
    logger.info("=" * 50)
    logger.info("测试2: parallel_batch_analyze 空输入")
    logger.info("=" * 50)

    analyzer = MockSemanticAnalyzer()

    results = parallel_batch_analyze(analyzer, [], "en")

    assert results == [], f"空输入应返回空列表，实际: {results}"

    logger.info("✅ 空输入测试通过")
    return True


def test_parallel_batch_analyze_single_batch():
    """测试单批次情况"""
    logger.info("=" * 50)
    logger.info("测试3: parallel_batch_analyze 单批次")
    logger.info("=" * 50)

    analyzer = MockSemanticAnalyzer(merge_all=True)

    text_pairs = [
        ("Text 1", "Text 2"),
        ("Text 3", "Text 4"),
    ]

    results = parallel_batch_analyze(
        analyzer, text_pairs, "en",
        max_workers=3, batch_size=10
    )

    assert len(results) == 2, f"结果数量应为2，实际: {len(results)}"
    assert all(results), f"所有结果应为True，实际: {results}"

    logger.info("✅ 单批次测试通过")
    return True


def test_merge_semantic_blocks_two_phase():
    """测试两阶段合并方法"""
    logger.info("=" * 50)
    logger.info("测试4: merge_semantic_blocks_with_llm_two_phase 方法")
    logger.info("=" * 50)

    analyzer = MockSemanticAnalyzer(merge_all=False)

    text_blocks = [
        MockTextBlock("First block", chapter_id=1),
        MockTextBlock("Second block", chapter_id=1),
        MockTextBlock("Third block", chapter_id=1),
        MockTextBlock("Fourth block", chapter_id=1),
        MockTextBlock("Fifth block", chapter_id=2),
    ]

    merged_blocks, block_mapping = merge_semantic_blocks_with_llm_two_phase(
        text_blocks, analyzer, "en",
        max_workers=2, batch_size=3
    )

    logger.info(f"原始块数量: {len(text_blocks)}")
    logger.info(f"合并后块数量: {len(merged_blocks)}")
    logger.info(f"块映射数量: {len(block_mapping)}")

    for i, mb in enumerate(merged_blocks):
        logger.info(f"合并块 {i+1}: {mb.block_text[:50]}... (包含 {len(mb.original_blocks)} 个原始块)")

    assert len(merged_blocks) > 0, "合并块数量应大于0"
    assert len(merged_blocks) <= len(text_blocks), "合并块数量不应超过原始块数量"

    logger.info("✅ 两阶段合并测试通过")
    return True


def test_merge_semantic_blocks_two_phase_empty():
    """测试空输入两阶段合并"""
    logger.info("=" * 50)
    logger.info("测试5: merge_semantic_blocks_with_llm_two_phase 空输入")
    logger.info("=" * 50)

    analyzer = MockSemanticAnalyzer()

    merged_blocks, block_mapping = merge_semantic_blocks_with_llm_two_phase(
        [], analyzer, "en"
    )

    assert merged_blocks == [], "空输入应返回空列表"
    assert block_mapping == [], "空输入应返回空映射"

    logger.info("✅ 空输入两阶段合并测试通过")
    return True


def test_merge_semantic_blocks_two_phase_single_block():
    """测试单块两阶段合并"""
    logger.info("=" * 50)
    logger.info("测试6: merge_semantic_blocks_with_llm_two_phase 单块")
    logger.info("=" * 50)

    analyzer = MockSemanticAnalyzer()

    text_blocks = [
        MockTextBlock("Only one block", chapter_id=1),
    ]

    merged_blocks, block_mapping = merge_semantic_blocks_with_llm_two_phase(
        text_blocks, analyzer, "en"
    )

    assert len(merged_blocks) == 1, f"单块应返回一个合并块，实际: {len(merged_blocks)}"
    assert merged_blocks[0].block_text == "Only one block", "文本内容应一致"

    logger.info("✅ 单块两阶段合并测试通过")
    return True


def run_all_tests():
    """运行所有测试"""
    logger.info("\n" + "=" * 60)
    logger.info("开始运行两阶段并行合并测试")
    logger.info("=" * 60 + "\n")

    tests = [
        test_parallel_batch_analyze,
        test_parallel_batch_analyze_empty,
        test_parallel_batch_analyze_single_batch,
        test_merge_semantic_blocks_two_phase,
        test_merge_semantic_blocks_two_phase_empty,
        test_merge_semantic_blocks_two_phase_single_block,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
                logger.error(f"❌ 测试失败: {test.__name__}")
        except Exception as e:
            failed += 1
            logger.error(f"❌ 测试异常: {test.__name__}, 错误: {str(e)}")

    logger.info("\n" + "=" * 60)
    logger.info(f"测试完成: 通过 {passed} 个，失败 {failed} 个")
    logger.info("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
