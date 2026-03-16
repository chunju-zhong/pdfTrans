import unittest
import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.chapter_identifier import ChapterIdentifier

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MockPage:
    """模拟PyMuPDF页面对象"""
    def __init__(self, blocks):
        self.blocks = blocks
    
    def get_text(self, mode, flags=None):
        if mode == 'blocks':
            return self.blocks
        return []


class MockDoc:
    """模拟PyMuPDF文档对象"""
    def __init__(self, pages):
        self.pages = pages
        self.page_count = len(pages)
    
    def __getitem__(self, index):
        return self.pages[index]


class TestTitlePositionFix(unittest.TestCase):
    """测试 _locate_title_blocks 方法"""
    
    def setUp(self):
        """设置测试环境"""
        self.chapter_identifier = ChapterIdentifier()
    
    def test_exact_single_block_match(self):
        """测试精确匹配单个文本块的场景"""
        logger.info("测试精确匹配单个文本块的场景")
        
        blocks = [
            (10, 20, 300, 50, "Introduction", 0, 0),
            (10, 60, 300, 90, "Some other text", 1, 0)
        ]
        
        page = MockPage(blocks)
        doc = MockDoc([page])
        
        position, block_nos = self.chapter_identifier._locate_title_blocks(doc, 1, "Introduction")
        
        self.assertIsNotNone(position)
        self.assertEqual(position[0], 10)
        self.assertEqual(position[1], 20)
        logger.info("精确匹配单个文本块测试通过")
    
    def test_avoid_substring_match(self):
        """测试避免子字符串误匹配的场景"""
        logger.info("测试避免子字符串误匹配的场景")
        
        blocks = [
            (10, 20, 300, 50, "Introduction to Agents and Agent architectures", 0, 0),
            (10, 60, 300, 90, "Agents and Agent", 1, 0)
        ]
        
        page = MockPage(blocks)
        doc = MockDoc([page])
        
        position, block_nos = self.chapter_identifier._locate_title_blocks(doc, 1, "Agents and Agent")
        
        self.assertIsNotNone(position)
        self.assertEqual(position[0], 10)
        self.assertEqual(position[1], 60)
        logger.info("避免子字符串误匹配测试通过")
    
    def test_cross_block_match(self):
        """测试跨多个连续文本块匹配的场景"""
        logger.info("测试跨多个连续文本块匹配的场景")
        
        blocks = [
            (10, 20, 300, 45, "Chapter", 0, 0),
            (10, 45, 300, 70, "One", 1, 0),
            (10, 70, 300, 95, "Introduction", 2, 0)
        ]
        
        page = MockPage(blocks)
        doc = MockDoc([page])
        
        position, block_nos = self.chapter_identifier._locate_title_blocks(doc, 1, "ChapterOne")
        
        self.assertIsNotNone(position)
        self.assertEqual(position[0], 10)
        self.assertEqual(position[1], 20)
        logger.info("跨块匹配测试通过")
    
    def test_high_similarity_match(self):
        """测试高相似度匹配的场景"""
        logger.info("测试高相似度匹配的场景")
        
        blocks = [
            (10, 20, 300, 50, "Introdution", 0, 0),  # 拼写错误
            (10, 60, 300, 90, "Different title", 1, 0)
        ]
        
        page = MockPage(blocks)
        doc = MockDoc([page])
        
        position, block_nos = self.chapter_identifier._locate_title_blocks(doc, 1, "Introduction")
        
        self.assertIsNotNone(position)
        self.assertEqual(position[0], 10)
        self.assertEqual(position[1], 20)
        logger.info("高相似度匹配测试通过")
    
    def test_no_match_returns_none(self):
        """测试没有匹配时返回None的场景"""
        logger.info("测试没有匹配时返回None的场景")
        
        blocks = [
            (10, 20, 300, 50, "Some title", 0, 0),
            (10, 60, 300, 90, "Another title", 1, 0)
        ]
        
        page = MockPage(blocks)
        doc = MockDoc([page])
        
        position, block_nos = self.chapter_identifier._locate_title_blocks(doc, 1, "Completely Different Title")
        
        self.assertIsNone(position)
        logger.info("没有匹配返回None测试通过")
    
    def test_out_of_range_page(self):
        """测试页码超出范围的场景"""
        logger.info("测试页码超出范围的场景")
        
        page = MockPage([])
        doc = MockDoc([page])
        
        position, block_nos = self.chapter_identifier._locate_title_blocks(doc, 10, "Title")
        
        self.assertIsNone(position)
        logger.info("页码超出范围测试通过")


if __name__ == '__main__':
    unittest.main()
