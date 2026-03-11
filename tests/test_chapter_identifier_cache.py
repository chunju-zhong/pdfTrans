import logging
import time
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.chapter_identifier import ChapterIdentifier

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_cache_optimization():
    """测试章节识别器的缓存优化"""
    print("=== 测试章节识别器缓存优化 ===")
    
    # 创建章节识别器实例
    identifier = ChapterIdentifier()
    
    # 测试 PDF 文件路径
    test_pdf_path = "uploads/c63ff73c_Day4_2_Agent_Quality.pdf"  # 使用上传目录中的文件
    
    try:
        # 第一次提取书签
        print("\n1. 第一次提取书签...")
        start_time = time.time()
        chapters = identifier.extract_bookmarks(test_pdf_path)
        extract_time = time.time() - start_time
        print(f"提取书签耗时: {extract_time:.4f} 秒")
        print(f"提取到 {len(chapters)} 个章节")
        
        # 检查缓存是否已构建
        print("\n2. 检查缓存状态...")
        has_sorted_chapters = hasattr(identifier, '_sorted_chapters') and identifier._sorted_chapters is not None
        has_chapters_by_page = hasattr(identifier, '_chapters_by_page') and identifier._chapters_by_page is not None
        has_chapter_mapping = hasattr(identifier, '_chapter_mapping') and identifier._chapter_mapping is not None
        
        print(f"_sorted_chapters 已构建: {has_sorted_chapters}")
        print(f"_chapters_by_page 已构建: {has_chapters_by_page}")
        print(f"_chapter_mapping 已构建: {has_chapter_mapping}")
        
        # 模拟文本块
        print("\n3. 模拟章节关联操作...")
        class MockTextBlock:
            def __init__(self, block_no, page_num, bbox):
                self.block_no = block_no
                self.page_num = page_num
                self.block_bbox = bbox
                self.chapter_id = None
                self.chapter_title = None
                self.chapter_level = None
                self.chapter_number = None
        
        # 创建模拟文本块
        mock_blocks = [
            MockTextBlock(1, 1, (0, 100, 0, 0)),
            MockTextBlock(2, 2, (0, 200, 0, 0)),
            MockTextBlock(3, 3, (0, 300, 0, 0))
        ]
        
        # 测试关联操作的性能
        start_time = time.time()
        identifier.associate_text_blocks(mock_blocks)
        associate_time = time.time() - start_time
        print(f"关联文本块耗时: {associate_time:.4f} 秒")
        
        # 检查关联结果
        print("\n4. 检查关联结果...")
        for block in mock_blocks:
            print(f"文本块 {block.block_no}: 章节={block.chapter_number} - {block.chapter_title}")
        
        # 第二次提取书签（测试缓存重置）
        print("\n5. 第二次提取书签（测试缓存重置）...")
        start_time = time.time()
        chapters2 = identifier.extract_bookmarks(test_pdf_path)
        extract_time2 = time.time() - start_time
        print(f"第二次提取书签耗时: {extract_time2:.4f} 秒")
        print(f"提取到 {len(chapters2)} 个章节")
        
        # 检查缓存是否已重新构建
        print("\n6. 检查缓存是否已重新构建...")
        has_sorted_chapters2 = hasattr(identifier, '_sorted_chapters') and identifier._sorted_chapters is not None
        has_chapters_by_page2 = hasattr(identifier, '_chapters_by_page') and identifier._chapters_by_page is not None
        has_chapter_mapping2 = hasattr(identifier, '_chapter_mapping') and identifier._chapter_mapping is not None
        
        print(f"_sorted_chapters 已构建: {has_sorted_chapters2}")
        print(f"_chapters_by_page 已构建: {has_chapters_by_page2}")
        print(f"_chapter_mapping 已构建: {has_chapter_mapping2}")
        
        print("\n=== 测试完成 ===")
        return True
        
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")
        return False

if __name__ == "__main__":
    test_cache_optimization()