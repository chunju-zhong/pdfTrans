import unittest
import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.chapter_identifier import ChapterIdentifier, Chapter
from models.text_block import TextBlock

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestChapterAssociation(unittest.TestCase):
    """测试章节归属逻辑"""
    
    def setUp(self):
        """设置测试环境"""
        self.chapter_identifier = ChapterIdentifier()
        
        # 创建模拟章节
        self.chapter1 = Chapter("Chapter 1", 1, 1, position=(0, 100))
        self.chapter1.id = "chapter_1"
        self.chapter1.number = "1"
        
        self.chapter1_1 = Chapter("Chapter 1.1", 2, 2, position=(0, 100), parent=self.chapter1)
        self.chapter1_1.id = "chapter_1_1"
        self.chapter1_1.number = "1.1"
        
        self.chapter1_2 = Chapter("Chapter 1.2", 2, 3, position=(0, 100), parent=self.chapter1)
        self.chapter1_2.id = "chapter_1_2"
        self.chapter1_2.number = "1.2"
        
        # 跨章节页：第3页同时包含1.2和2.1章节
        self.chapter2 = Chapter("Chapter 2", 1, 3, position=(0, 500))
        self.chapter2.id = "chapter_2"
        self.chapter2.number = "2"
        
        self.chapter2_1 = Chapter("Chapter 2.1", 2, 4, position=(0, 100), parent=self.chapter2)
        self.chapter2_1.id = "chapter_2_1"
        self.chapter2_1.number = "2.1"
        
        # 构建章节树
        self.chapter_identifier.chapters = [self.chapter1, self.chapter2]
        self.chapter1.add_child(self.chapter1_1)
        self.chapter1.add_child(self.chapter1_2)
        self.chapter2.add_child(self.chapter2_1)
    
    def test_cross_chapter_page(self):
        """测试跨章节页的文本块归属"""
        logger.info("测试跨章节页的文本块归属")
        
        # 创建模拟文本块
        # 第3页的文本块，应该归属于chapter1_2
        block1 = TextBlock(
            block_no=1,
            text="Text in Chapter 1.2",
            bbox=(50, 150, 500, 200),
            block_type=0,
            page_num=3
        )
        
        # 第3页的文本块，应该归属于chapter2
        block2 = TextBlock(
            block_no=2,
            text="Text in Chapter 2",
            bbox=(50, 550, 500, 600),
            block_type=0,
            page_num=3
        )
        
        # 第4页的文本块，应该归属于chapter2_1
        block3 = TextBlock(
            block_no=3,
            text="Text in Chapter 2.1",
            bbox=(50, 150, 500, 200),
            block_type=0,
            page_num=4
        )
        
        # 关联文本块到章节
        self.chapter_identifier.associate_text_blocks([block1, block2, block3])
        
        # 验证归属结果
        self.assertEqual(block1.chapter_id, "chapter_1_2")
        self.assertEqual(block1.chapter_number, "1.2")
        
        self.assertEqual(block2.chapter_id, "chapter_2")
        self.assertEqual(block2.chapter_number, "2")
        
        self.assertEqual(block3.chapter_id, "chapter_2_1")
        self.assertEqual(block3.chapter_number, "2.1")
        
        logger.info("跨章节页测试通过")
    
    def test_error_page_assignment(self):
        """测试错误页码归属的修复"""
        logger.info("测试错误页码归属的修复")
        
        # 创建模拟文本块
        # 第5页的文本块，应该归属于chapter2_1
        block1 = TextBlock(
            block_no=1,
            text="Text in Chapter 2.1",
            bbox=(50, 150, 500, 200),
            block_type=0,
            page_num=5
        )
        
        # 关联文本块到章节
        self.chapter_identifier.associate_text_blocks([block1])
        
        # 验证归属结果
        self.assertEqual(block1.chapter_id, "chapter_2_1")
        self.assertEqual(block1.chapter_number, "2.1")
        
        logger.info("错误页码归属测试通过")
    
    def test_backward_compatibility(self):
        """测试向后兼容性"""
        logger.info("测试向后兼容性")
        
        # 创建没有位置信息的章节
        chapter3 = Chapter("Chapter 3", 1, 6)
        chapter3.id = "chapter_3"
        chapter3.number = "3"
        
        self.chapter_identifier.chapters.append(chapter3)
        
        # 创建模拟文本块
        block1 = TextBlock(
            block_no=1,
            text="Text in Chapter 3",
            bbox=(50, 150, 500, 200),
            block_type=0,
            page_num=6
        )
        
        # 关联文本块到章节
        self.chapter_identifier.associate_text_blocks([block1])
        
        # 验证归属结果
        self.assertEqual(block1.chapter_id, "chapter_3")
        self.assertEqual(block1.chapter_number, "3")
        
        logger.info("向后兼容性测试通过")

if __name__ == '__main__':
    unittest.main()