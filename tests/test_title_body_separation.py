import pytest
from models.text_block import TextBlock
from models.merged_block import MergedBlock
from utils.text_processing import merge_semantic_blocks, merge_semantic_blocks_with_llm

class MockSemanticAnalyzer:
    """模拟语义分析器，用于测试LLM语义合并"""
    
    def batch_analyze_semantic_relationship(self, text_pairs, source_lang):
        """批量分析语义关系，始终返回True"""
        return [True] * len(text_pairs)


class TestTitleBodySeparation:
    """测试标题与正文区分功能"""
    
    def test_merge_semantic_blocks_with_single_title(self):
        """测试单个章节标题的情况"""
        # 创建测试文本块
        blocks = [
            # 章节标题
            TextBlock(1, "第一章 介绍", (0, 0, 100, 20), 0, 1),
            # 正文
            TextBlock(2, "这是第一章的正文内容。", (0, 25, 100, 45), 0, 1),
            TextBlock(3, "这是正文的第二部分。", (0, 50, 100, 70), 0, 1)
        ]
        
        # 设置章节信息
        blocks[0].chapter_id = "chapter1"
        blocks[0].chapter_title = "第一章 介绍"
        blocks[0].chapter_level = 1
        blocks[0].is_title_block = True
        
        blocks[1].chapter_id = "chapter1"
        blocks[1].chapter_title = "第一章 介绍"
        blocks[1].is_title_block = False
        
        blocks[2].chapter_id = "chapter1"
        blocks[2].chapter_title = "第一章 介绍"
        blocks[2].is_title_block = False
        
        # 执行语义合并
        merged_blocks, block_mapping = merge_semantic_blocks(blocks)
        
        # 验证结果
        assert len(merged_blocks) == 2
        assert merged_blocks[0].block_text == "第一章 介绍"
        assert len(merged_blocks[0].original_blocks) == 1
        assert merged_blocks[1].block_text == "这是第一章的正文内容。 这是正文的第二部分。"
        assert len(merged_blocks[1].original_blocks) == 2
    
    def test_merge_semantic_blocks_with_multi_block_title(self):
        """测试多个块组成的章节标题的情况"""
        # 创建测试文本块
        blocks = [
            # 章节标题（由两个块组成）
            TextBlock(1, "第二章", (0, 0, 50, 20), 0, 1),
            TextBlock(2, " 方法", (50, 0, 100, 20), 0, 1),
            # 正文
            TextBlock(3, "这是第二章的正文内容。", (0, 25, 100, 45), 0, 1)
        ]
        
        # 设置章节信息
        for i in range(3):
            blocks[i].chapter_id = "chapter2"
            blocks[i].chapter_title = "第二章 方法"
            if i < 2:
                blocks[i].chapter_level = 1
                blocks[i].is_title_block = True
            else:
                blocks[i].is_title_block = False
        
        # 执行语义合并
        merged_blocks, block_mapping = merge_semantic_blocks(blocks)
        
        # 验证结果
        assert len(merged_blocks) == 2
        assert merged_blocks[0].block_text == "第二章 方法"
        assert len(merged_blocks[0].original_blocks) == 2
        assert merged_blocks[1].block_text == "这是第二章的正文内容。"
        assert len(merged_blocks[1].original_blocks) == 1
    
    def test_merge_semantic_blocks_with_llm(self):
        """测试基于LLM的语义合并"""
        # 创建测试文本块
        blocks = [
            # 章节标题
            TextBlock(1, "第三章 结果", (0, 0, 100, 20), 0, 1),
            # 正文
            TextBlock(2, "这是第三章的正文内容。", (0, 25, 100, 45), 0, 1)
        ]
        
        # 设置章节信息
        blocks[0].chapter_id = "chapter3"
        blocks[0].chapter_title = "第三章 结果"
        blocks[0].chapter_level = 1
        blocks[0].is_title_block = True
        
        blocks[1].chapter_id = "chapter3"
        blocks[1].chapter_title = "第三章 结果"
        blocks[1].is_title_block = False
        
        # 创建模拟语义分析器
        semantic_analyzer = MockSemanticAnalyzer()
        
        # 执行LLM语义合并
        merged_blocks, block_mapping = merge_semantic_blocks_with_llm(blocks, semantic_analyzer, "zh")
        
        # 验证结果
        assert len(merged_blocks) == 2
        assert merged_blocks[0].block_text == "第三章 结果"
        assert len(merged_blocks[0].original_blocks) == 1
        assert merged_blocks[1].block_text == "这是第三章的正文内容。"
        assert len(merged_blocks[1].original_blocks) == 1
    
    def test_merge_semantic_blocks_with_llm_multi_block_title(self):
        """测试基于LLM的语义合并处理多个块组成的章节标题"""
        # 创建测试文本块
        blocks = [
            # 章节标题（由两个块组成）
            TextBlock(1, "第四章", (0, 0, 50, 20), 0, 1),
            TextBlock(2, " 讨论", (50, 0, 100, 20), 0, 1),
            # 正文
            TextBlock(3, "这是第四章的正文内容。", (0, 25, 100, 45), 0, 1)
        ]
        
        # 设置章节信息
        for i in range(3):
            blocks[i].chapter_id = "chapter4"
            blocks[i].chapter_title = "第四章 讨论"
            if i < 2:
                blocks[i].chapter_level = 1
                blocks[i].is_title_block = True
            else:
                blocks[i].is_title_block = False
        
        # 创建模拟语义分析器
        semantic_analyzer = MockSemanticAnalyzer()
        
        # 执行LLM语义合并
        merged_blocks, block_mapping = merge_semantic_blocks_with_llm(blocks, semantic_analyzer, "zh")
        
        # 验证结果
        assert len(merged_blocks) == 2
        assert merged_blocks[0].block_text == "第四章 讨论"
        assert len(merged_blocks[0].original_blocks) == 2
        assert merged_blocks[1].block_text == "这是第四章的正文内容。"
        assert len(merged_blocks[1].original_blocks) == 1
    
    def test_merge_semantic_blocks_with_empty_chapter_title(self):
        """测试章节标题为空的情况"""
        # 创建测试文本块
        blocks = [
            # 无章节标题的文本
            TextBlock(1, "这是没有章节标题的文本。", (0, 0, 100, 20), 0, 1),
            TextBlock(2, "这是第二部分文本。", (0, 25, 100, 45), 0, 1)
        ]
        
        # 设置章节信息（chapter_title为空）
        blocks[0].chapter_id = "chapter1"
        blocks[0].chapter_title = ""
        
        blocks[1].chapter_id = "chapter1"
        blocks[1].chapter_title = ""
        
        # 执行语义合并
        merged_blocks, block_mapping = merge_semantic_blocks(blocks)
        
        # 验证结果（应该合并为一个块）
        assert len(merged_blocks) == 1
        assert "这是没有章节标题的文本。" in merged_blocks[0].block_text
        assert "这是第二部分文本。" in merged_blocks[0].block_text
        assert len(merged_blocks[0].original_blocks) == 2
    
    def test_merge_semantic_blocks_with_no_chapter_info(self):
        """测试没有章节信息的情况"""
        # 创建测试文本块
        blocks = [
            # 无章节信息的文本
            TextBlock(1, "这是没有章节信息的文本。", (0, 0, 100, 20), 0, 1),
            TextBlock(2, "这是第二部分文本。", (0, 25, 100, 45), 0, 1)
        ]
        
        # 不设置章节信息
        
        # 执行语义合并
        merged_blocks, block_mapping = merge_semantic_blocks(blocks)
        
        # 验证结果（应该合并为一个块）
        assert len(merged_blocks) == 1
        assert "这是没有章节信息的文本。" in merged_blocks[0].block_text
        assert "这是第二部分文本。" in merged_blocks[0].block_text
        assert len(merged_blocks[0].original_blocks) == 2
    
    def test_merge_semantic_blocks_with_multiple_chapters(self):
        """测试多个章节的情况"""
        # 创建测试文本块
        blocks = [
            # 第一章标题
            TextBlock(1, "第一章 介绍", (0, 0, 100, 20), 0, 1),
            # 第一章正文
            TextBlock(2, "这是第一章的正文内容。", (0, 25, 100, 45), 0, 1),
            # 第二章标题
            TextBlock(3, "第二章 方法", (0, 50, 100, 70), 0, 1),
            # 第二章正文
            TextBlock(4, "这是第二章的正文内容。", (0, 75, 100, 95), 0, 1)
        ]
        
        # 设置章节信息
        blocks[0].chapter_id = "chapter1"
        blocks[0].chapter_title = "第一章 介绍"
        blocks[0].chapter_level = 1
        blocks[0].is_title_block = True
        
        blocks[1].chapter_id = "chapter1"
        blocks[1].chapter_title = "第一章 介绍"
        blocks[1].is_title_block = False
        
        blocks[2].chapter_id = "chapter2"
        blocks[2].chapter_title = "第二章 方法"
        blocks[2].chapter_level = 1
        blocks[2].is_title_block = True
        
        blocks[3].chapter_id = "chapter2"
        blocks[3].chapter_title = "第二章 方法"
        blocks[3].is_title_block = False
        
        # 执行语义合并
        merged_blocks, block_mapping = merge_semantic_blocks(blocks)
        
        # 验证结果（应该有4个合并块：两个标题和两个正文）
        assert len(merged_blocks) == 4
        assert merged_blocks[0].block_text == "第一章 介绍"
        assert merged_blocks[1].block_text == "这是第一章的正文内容。"
        assert merged_blocks[2].block_text == "第二章 方法"
        assert merged_blocks[3].block_text == "这是第二章的正文内容。"
