import os
import tempfile
import fitz
import pytest
from unittest.mock import Mock, patch
from modules.chapter_identifier import ChapterIdentifier, Chapter


def create_test_pdf_with_bookmarks():
    """创建一个带有书签的测试PDF"""
    temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    temp_file.close()
    
    doc = fitz.open()
    
    # 添加几个空白页
    for _ in range(4):
        doc.new_page()
    
    # 添加书签
    toc = [
        [1, "第1章 引言", 3],
        [1, "第2章 正文", 4]
    ]
    doc.set_toc(toc)
    
    doc.save(temp_file.name)
    doc.close()
    
    return temp_file.name


def create_test_pdf_without_bookmarks():
    """创建一个不带书签的测试PDF"""
    temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    temp_file.close()
    
    doc = fitz.open()
    
    # 添加几个空白页
    for _ in range(3):
        doc.new_page()
    
    doc.save(temp_file.name)
    doc.close()
    
    return temp_file.name


def create_test_pdf_with_empty_page():
    """创建一个带有空页面的测试PDF"""
    temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False, prefix='test_empty_')
    temp_file.close()
    
    doc = fitz.open()
    
    # 添加几个空白页
    for _ in range(3):
        doc.new_page()
    
    # 添加书签
    toc = [
        [1, "第1章 引言", 3]
    ]
    doc.set_toc(toc)
    
    doc.save(temp_file.name)
    doc.close()
    
    return temp_file.name


def create_test_pdf_with_long_title():
    """创建一个带有长标题的测试PDF"""
    temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False, prefix='test_long_')
    temp_file.close()
    
    doc = fitz.open()
    
    # 添加几个空白页
    for _ in range(2):
        doc.new_page()
    
    # 添加书签
    toc = [
        [1, "第1章 引言", 2]
    ]
    doc.set_toc(toc)
    
    doc.save(temp_file.name)
    doc.close()
    
    return temp_file.name


class TestDefaultChapter:
    """测试默认章节功能"""
    
    def test_init_default_config(self):
        """测试默认配置"""
        ci = ChapterIdentifier()
        assert ci.default_chapter_titles == ["封面", "目录", "前言", "引言"]
        assert ci.default_chapter_level == 1
        assert ci.enable_default_chapters is True
        assert ci.use_smart_naming is True
        assert ci.max_title_length == 20
    
    def test_init_custom_config(self):
        """测试自定义配置"""
        custom_titles = ["首页", "目次", "绪论"]
        ci = ChapterIdentifier(
            default_chapter_titles=custom_titles,
            default_chapter_level=2,
            enable_default_chapters=False,
            use_smart_naming=False,
            max_title_length=30
        )
        assert ci.default_chapter_titles == custom_titles
        assert ci.default_chapter_level == 2
        assert ci.enable_default_chapters is False
        assert ci.use_smart_naming is False
        assert ci.max_title_length == 30
    
    def test_detect_pages_without_chapters(self):
        """测试检测无章节的页面"""
        ci = ChapterIdentifier()
        
        # 测试完全无章节的情况
        pages = ci._detect_pages_without_chapters(5, [])
        assert pages == [1, 2, 3, 4, 5]
        
        # 测试第3页开始有章节的情况
        chapter1 = Chapter("第一章", 1, 3)
        chapter2 = Chapter("第二章", 1, 5)
        pages = ci._detect_pages_without_chapters(10, [chapter1, chapter2])
        assert pages == [1, 2]
        
        # 测试第1页就有章节的情况
        chapter0 = Chapter("封面", 1, 1)
        pages = ci._detect_pages_without_chapters(10, [chapter0, chapter1, chapter2])
        assert pages == []
    
    def test_truncate_title(self):
        """测试文本截断功能"""
        ci = ChapterIdentifier(max_title_length=10)
        
        # 短文本不截断
        assert ci._truncate_title("短标题") == "短标题"
        
        # 恰好10字符
        assert ci._truncate_title("1234567890") == "1234567890"
        
        # 长文本截断
        long_text = "这是一个非常长的标题"
        result = ci._truncate_title(long_text)
        assert len(result) <= 13  # 10字符 + 省略号
        
        # 空文本
        assert ci._truncate_title("") == ""
        assert ci._truncate_title(None) is None
    
    @patch('modules.chapter_identifier.ChapterIdentifier._get_first_text_block')
    def test_create_default_chapters_smart_naming(self, mock_get_text):
        """测试智能命名创建默认章节"""
        mock_get_text.side_effect = ["封面", "目录"]
        
        pdf_path = create_test_pdf_with_bookmarks()
        
        try:
            ci = ChapterIdentifier(use_smart_naming=True)
            doc = fitz.open(pdf_path)
            
            chapters = ci._create_default_chapters([1, 2], doc, pdf_path)
            
            assert len(chapters) == 2
            assert chapters[0].title == "封面"
            assert chapters[0].page_num == 1
            assert chapters[1].title == "目录"
            assert chapters[1].page_num == 2
            
            doc.close()
        finally:
            os.unlink(pdf_path)
    
    def test_create_default_chapters_fixed_naming(self):
        """测试固定命名创建默认章节"""
        pdf_path = create_test_pdf_with_bookmarks()
        
        try:
            ci = ChapterIdentifier(use_smart_naming=False)
            doc = fitz.open(pdf_path)
            
            chapters = ci._create_default_chapters([1, 2, 3, 4, 5, 6], doc, pdf_path)
            
            assert len(chapters) == 6
            assert chapters[0].title == "封面"
            assert chapters[1].title == "目录"
            assert chapters[2].title == "前言"
            assert chapters[3].title == "引言"
            assert chapters[4].title == "引言2"
            assert chapters[5].title == "引言3"
            
            doc.close()
        finally:
            os.unlink(pdf_path)
    
    @patch('modules.chapter_identifier.ChapterIdentifier._get_first_text_block')
    def test_create_default_chapters_empty_page(self, mock_get_text):
        """测试空页面使用文件名和页号"""
        mock_get_text.side_effect = [None, "目录"]
        
        pdf_path = create_test_pdf_with_empty_page()
        
        try:
            ci = ChapterIdentifier(use_smart_naming=True)
            doc = fitz.open(pdf_path)
            
            chapters = ci._create_default_chapters([1, 2], doc, pdf_path)
            
            assert len(chapters) == 2
            # 第1页是空的，应该使用文件名和页号
            assert "test_empty" in chapters[0].title
            assert "第1页" in chapters[0].title
            # 第2页有文本，应该使用智能命名
            assert chapters[1].title == "目录"
            
            doc.close()
        finally:
            os.unlink(pdf_path)
    
    @patch('modules.chapter_identifier.ChapterIdentifier._get_first_text_block')
    def test_create_default_chapters_long_title(self, mock_get_text):
        """测试长标题被截断"""
        long_title = "这是一个非常长的标题，用于测试文本截断功能"
        mock_get_text.return_value = long_title
        
        pdf_path = create_test_pdf_with_long_title()
        
        try:
            ci = ChapterIdentifier(use_smart_naming=True, max_title_length=20)
            doc = fitz.open(pdf_path)
            
            chapters = ci._create_default_chapters([1], doc, pdf_path)
            
            assert len(chapters) == 1
            # 标题应该被截断
            assert len(chapters[0].title) <= 23
            assert chapters[0].title.endswith("...")
            
            doc.close()
        finally:
            os.unlink(pdf_path)
    
    @patch('modules.chapter_identifier.ChapterIdentifier._get_first_text_block')
    def test_extract_bookmarks_with_smart_naming(self, mock_get_text):
        """测试提取书签时使用智能命名"""
        mock_get_text.side_effect = ["封面", "目录"]
        
        pdf_path = create_test_pdf_with_bookmarks()
        
        try:
            ci = ChapterIdentifier(use_smart_naming=True)
            chapters = ci.extract_bookmarks(pdf_path)
            
            # 应该有4个章节：2个智能命名章节 + 2个原有章节
            assert len(chapters) == 4
            assert chapters[0].title == "封面"
            assert chapters[0].page_num == 1
            assert chapters[1].title == "目录"
            assert chapters[1].page_num == 2
            assert chapters[2].title == "第1章 引言"
            assert chapters[2].page_num == 3
            assert chapters[3].title == "第2章 正文"
            assert chapters[3].page_num == 4
        finally:
            os.unlink(pdf_path)
    
    def test_extract_bookmarks_with_fixed_naming(self):
        """测试提取书签时使用固定命名"""
        pdf_path = create_test_pdf_with_bookmarks()
        
        try:
            ci = ChapterIdentifier(use_smart_naming=False)
            chapters = ci.extract_bookmarks(pdf_path)
            
            # 应该有4个章节：2个固定命名章节 + 2个原有章节
            assert len(chapters) == 4
            assert chapters[0].title == "封面"
            assert chapters[0].page_num == 1
            assert chapters[1].title == "目录"
            assert chapters[1].page_num == 2
            assert chapters[2].title == "第1章 引言"
            assert chapters[2].page_num == 3
            assert chapters[3].title == "第2章 正文"
            assert chapters[3].page_num == 4
        finally:
            os.unlink(pdf_path)
    
    def test_extract_bookmarks_disabled_default_chapters(self):
        """测试禁用默认章节功能"""
        pdf_path = create_test_pdf_with_bookmarks()
        
        try:
            ci = ChapterIdentifier(enable_default_chapters=False)
            chapters = ci.extract_bookmarks(pdf_path)
            
            # 应该只有2个原有章节
            assert len(chapters) == 2
            assert chapters[0].title == "第1章 引言"
            assert chapters[1].title == "第2章 正文"
        finally:
            os.unlink(pdf_path)
    
    def test_extract_bookmarks_completely_without_bookmarks(self):
        """测试完全没有书签的PDF"""
        pdf_path = create_test_pdf_without_bookmarks()
        
        try:
            ci = ChapterIdentifier()
            chapters = ci.extract_bookmarks(pdf_path)
            
            # PDF没有书签，但默认章节功能应该仍然创建默认章节吗？
            # 当前实现：没有书签时返回空列表
            assert len(chapters) == 0
        finally:
            os.unlink(pdf_path)
    
    @patch('modules.chapter_identifier.ChapterIdentifier._get_first_text_block')
    def test_associate_to_default_chapters(self, mock_get_text):
        """测试内容关联到默认章节"""
        from models.text_block import TextBlock
        
        mock_get_text.side_effect = ["封面", "目录"]
        
        pdf_path = create_test_pdf_with_bookmarks()
        
        try:
            ci = ChapterIdentifier()
            doc = fitz.open(pdf_path)
            
            # 创建默认章节
            default_chapters = ci._create_default_chapters([1, 2], doc, pdf_path)
            
            # 手动设置章节
            ci.chapters = default_chapters
            ci._assign_chapter_numbers()
            ci._ensure_chapter_cache()
            
            # 创建文本块
            block1 = TextBlock(0, "封面内容", (0, 50, 100, 100), page_num=1)
            block2 = TextBlock(1, "目录内容", (0, 50, 100, 100), page_num=2)
            
            # 关联章节
            ci.associate_text_blocks([block1, block2])
            
            # 验证关联
            assert block1.chapter_id is not None
            assert block1.chapter_title == "封面"
            assert block2.chapter_id is not None
            assert block2.chapter_title == "目录"
            
            doc.close()
        finally:
            os.unlink(pdf_path)
    
    def test_custom_default_titles(self):
        """测试自定义默认章节标题"""
        pdf_path = create_test_pdf_with_bookmarks()
        
        try:
            custom_titles = ["首页", "目次"]
            ci = ChapterIdentifier(default_chapter_titles=custom_titles, use_smart_naming=False)
            chapters = ci.extract_bookmarks(pdf_path)
            
            assert len(chapters) == 4
            assert chapters[0].title == "首页"
            assert chapters[1].title == "目次"
        finally:
            os.unlink(pdf_path)
