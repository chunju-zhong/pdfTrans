import os
import sys
import logging
import tempfile

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.chapter_identifier import Chapter
from modules.markdown_generator import MarkdownGenerator
from models.extraction import PdfPage, TextBlock

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_chapter_markdown_generation():
    """测试章节Markdown生成功能"""
    try:
        # 创建测试章节结构
        # 章节1: The Journey to Production
        chapter1 = Chapter("The Journey to Production", 1, 11)
        chapter1.id = "chapter_0"
        chapter1.number = "4"
        
        # 章节1.1: Evaluation as a Quality Gate
        chapter1_1 = Chapter("Evaluation as a Quality Gate", 2, 12)
        chapter1_1.id = "chapter_1"
        chapter1_1.number = "4.1"
        chapter1.add_child(chapter1_1)
        
        # 章节1.2: The Automated CI/CD Pipeline
        chapter1_2 = Chapter("The Automated CI/CD Pipeline", 2, 14)
        chapter1_2.id = "chapter_2"
        chapter1_2.number = "4.2"
        chapter1.add_child(chapter1_2)
        
        # 章节1.3: Safe Rollout Strategies
        chapter1_3 = Chapter("Safe Rollout Strategies", 2, 16)
        chapter1_3.id = "chapter_3"
        chapter1_3.number = "4.3"
        chapter1.add_child(chapter1_3)
        
        # 章节1.4: Building Security from the Start
        chapter1_4 = Chapter("Building Security from the Start", 2, 18)
        chapter1_4.id = "chapter_4"
        chapter1_4.number = "4.4"
        chapter1.add_child(chapter1_4)
        
        # 章节2: Operations in-Production
        chapter2 = Chapter("Operations in-Production", 1, 20)
        chapter2.id = "chapter_5"
        chapter2.number = "5"
        
        # 章节2.1: Observe: Your Agent's Sensory System
        chapter2_1 = Chapter("Observe: Your Agent's Sensory System", 2, 21)
        chapter2_1.id = "chapter_6"
        chapter2_1.number = "5.1"
        chapter2.add_child(chapter2_1)
        
        # 章节2.2: Act: The Levers of Operational Control
        chapter2_2 = Chapter("Act: The Levers of Operational Control", 2, 22)
        chapter2_2.id = "chapter_7"
        chapter2_2.number = "5.2"
        chapter2.add_child(chapter2_2)
        
        # 章节2.2.1: Managing System Health: Performance, Cost, and Scale
        chapter2_2_1 = Chapter("Managing System Health: Performance, Cost, and Scale", 3, 23)
        chapter2_2_1.id = "chapter_8"
        chapter2_2_1.number = "5.2.1"
        chapter2_2.add_child(chapter2_2_1)
        
        # 章节2.2.2: Managing Risk: The Security Response Playbook
        chapter2_2_2 = Chapter("Managing Risk: The Security Response Playbook", 3, 24)
        chapter2_2_2.id = "chapter_9"
        chapter2_2_2.number = "5.2.2"
        chapter2_2.add_child(chapter2_2_2)
        
        # 章节2.3: Evolve: Learning from Production
        chapter2_3 = Chapter("Evolve: Learning from Production", 2, 25)
        chapter2_3.id = "chapter_10"
        chapter2_3.number = "5.3"
        chapter2.add_child(chapter2_3)
        
        # 章节2.3.1: The Engine of Evolution: An Automated Path to Production
        chapter2_3_1 = Chapter("The Engine of Evolution: An Automated Path to Production", 3, 25)
        chapter2_3_1.id = "chapter_11"
        chapter2_3_1.number = "5.3.1"
        chapter2_3.add_child(chapter2_3_1)
        
        # 章节2.3.2: The Evolution Workflow: From Insight to Deployed Improvement
        chapter2_3_2 = Chapter("The Evolution Workflow: From Insight to Deployed Improvement", 3, 26)
        chapter2_3_2.id = "chapter_12"
        chapter2_3_2.number = "5.3.2"
        chapter2_3.add_child(chapter2_3_2)
        
        # 章节2.4: Evolving Security: The Production Feedback Loop
        chapter2_4 = Chapter("Evolving Security: The Production Feedback Loop", 2, 27)
        chapter2_4.id = "chapter_13"
        chapter2_4.number = "5.4"
        chapter2.add_child(chapter2_4)
        
        # 章节2.5: Beyond Single-Agent Operations
        chapter2_5 = Chapter("Beyond Single-Agent Operations", 2, 28)
        chapter2_5.id = "chapter_14"
        chapter2_5.number = "5.5"
        chapter2.add_child(chapter2_5)
        
        # 构建章节列表
        chapters = [chapter1, chapter2]
        
        # 创建测试文本块
        text_blocks = []
        
        # 为每个章节创建文本块
        chapter_info = [
            (chapter1, 11, "Chapter 4 content"),
            (chapter1_1, 12, "Chapter 4.1 content"),
            (chapter1_2, 14, "Chapter 4.2 content"),
            (chapter1_3, 16, "Chapter 4.3 content"),
            (chapter1_4, 18, "Chapter 4.4 content"),
            (chapter2, 20, "Chapter 5 content"),
            (chapter2_1, 21, "Chapter 5.1 content"),
            (chapter2_2, 22, "Chapter 5.2 content"),
            (chapter2_2_1, 23, "Chapter 5.2.1 content"),
            (chapter2_2_2, 24, "Chapter 5.2.2 content"),
            (chapter2_3, 25, "Chapter 5.3 content"),
            (chapter2_3_1, 25, "Chapter 5.3.1 content"),
            (chapter2_3_2, 26, "Chapter 5.3.2 content"),
            (chapter2_4, 27, "Chapter 5.4 content"),
            (chapter2_5, 28, "Chapter 5.5 content"),
        ]
        
        for chapter, page_num, content in chapter_info:
            text_block = TextBlock(
                block_no=len(text_blocks),
                text=content,
                bbox=(100, 100, 200, 120),
                block_type=0,
                page_num=page_num
            )
            text_block.chapter_id = chapter.id
            text_block.chapter_title = chapter.title
            text_block.chapter_level = chapter.level
            text_block.chapter_number = chapter.number
            text_blocks.append(text_block)
        
        # 创建测试页面
        pages = {}
        for text_block in text_blocks:
            if text_block.page_num not in pages:
                pages[text_block.page_num] = []
            pages[text_block.page_num].append(text_block)
        
        pdf_pages = []
        for page_num, blocks in pages.items():
            pdf_page = PdfPage(
                page_num=page_num,
                text_blocks=blocks
            )
            pdf_pages.append(pdf_page)
        
        # 准备测试数据
        translated_content = {
            'blocks': pdf_pages,
            'tables': []
        }
        
        # 创建测试图像
        class MockImage:
            def __init__(self, page_num, image_path, chapter_id, chapter_title, chapter_level, chapter_number):
                self.page_num = page_num
                self.image_path = image_path
                self.bbox = (150, 150, 250, 250)
                self.chapter_id = chapter_id
                self.chapter_title = chapter_title
                self.chapter_level = chapter_level
                self.chapter_number = chapter_number
        
        images = [
            MockImage(11, "test_image1.png", chapter1.id, chapter1.title, chapter1.level, chapter1.number),
            MockImage(20, "test_image2.png", chapter2.id, chapter2.title, chapter2.level, chapter2.number),
        ]
        
        # 创建临时输出目录
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"创建临时输出目录: {temp_dir}")
            
            # 创建Markdown生成器（使用模拟实现）
            class MockMarkdownGenerator:
                def __init__(self):
                    self.chapter_counter = 0
                
                def _sanitize_filename(self, filename):
                    import re
                    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
                    if len(filename) > 255:
                        filename = filename[:255]
                    return filename
                
                def _process_chapter_pages(self, chapter_pages):
                    """处理章节中的所有页面内容"""
                    full_text = []
                    sorted_pages = sorted(chapter_pages.keys())
                    logger.info(f"处理章节页面，页码数量: {len(sorted_pages)}")
                    for page_num in sorted_pages:
                        page_content = chapter_pages[page_num]
                        logger.info(f"  处理页码: {page_num}, 文本块数量: {len(page_content['text_blocks'])}, 图像数量: {len(page_content['images'])}, 表格数量: {len(page_content['tables'])}")
                        for text_block in page_content['text_blocks']:
                            logger.info(f"    处理文本块: block_no={text_block.block_no}, 文本长度: {len(text_block.block_text)}")
                            if text_block.block_text.strip():
                                full_text.append(text_block.block_text)
                                full_text.append("")
                                logger.info(f"    文本块添加成功")
                            else:
                                logger.warning(f"    文本块为空: block_no={text_block.block_no}")
                        for image in page_content['images']:
                            image_path = image.image_path
                            image_md = f"![]({image_path})"
                            full_text.append("")
                            full_text.append(image_md)
                            full_text.append("")
                            logger.info(f"    图像添加成功: {image_path}")
                        for table in page_content['tables']:
                            table_md = "| 测试表格 |\n|---------|\n| 测试内容 |"
                            if table_md:
                                full_text.append("")
                                full_text.append(table_md)
                                full_text.append("")
                                logger.info(f"    表格添加成功")
                            else:
                                logger.warning(f"    表格为空")
                    result = "\n".join(full_text)
                    logger.info(f"章节内容处理完成，总长度: {len(result)}")
                    return result
                
                def _format_with_layout_model(self, text):
                    # 模拟布局模型处理
                    class MockResult:
                        def __init__(self, content):
                            self.content = content
                            self.token_usage = {}
                            self.finish_reason = ""
                            self.truncation_info = type('obj', (object,), {'truncated': False, 'token_usage': {}, 'finish_reason': ''})
                    return MockResult(text)
                
                def _generate_chapter_index(self, chapters, chapter_files, index_path):
                    # 生成章节索引
                    index_content = []
                    index_content.append("# 章节索引")
                    index_content.append("")
                    
                    def add_chapters_to_index(chapters, level=0):
                        for chapter in chapters:
                            indent = "  " * level
                            filename = f"{chapter.number} {chapter.title}.md"
                            filename = self._sanitize_filename(filename)
                            link = f"[{chapter.title}]({filename})"
                            index_content.append(f"{indent}- {link}")
                            if chapter.children:
                                add_chapters_to_index(chapter.children, level + 1)
                    
                    add_chapters_to_index(chapters)
                    
                    with open(index_path, 'w', encoding='utf-8') as f:
                        f.write("\n".join(index_content))
                
                def _generate_chapter_markdowns(self, translated_content, images, output_dir, target_lang, doc_id, chapters):
                    """按章节生成Markdown文件"""
                    # 按章节组织内容
                    chapter_content = {}
                    
                    # 递归收集所有章节，包括子章节
                    all_chapters = []
                    def collect_chapters(chapters):
                        for chapter in chapters:
                            all_chapters.append(chapter)
                            if chapter.children:
                                collect_chapters(chapter.children)
                    
                    collect_chapters(chapters)
                    logger.info(f"开始按章节组织内容，章节列表长度: {len(all_chapters)}")
                    
                    # 首先为所有章节创建条目
                    for chapter in all_chapters:
                        chapter_content[chapter.id] = {
                            'title': chapter.title,
                            'level': chapter.level,
                            'number': chapter.number,
                            'pages': {}  # 按页码组织内容
                        }
                    
                    # 组织文本块
                    if 'blocks' in translated_content:
                        logger.info(f"处理文本块，页面数量: {len(translated_content['blocks'])}")
                        for page in translated_content['blocks']:
                            logger.info(f"处理页码: {page.page_num}, 文本块数量: {len(page.text_blocks)}")
                            for text_block in page.text_blocks:
                                logger.info(f"  文本块: block_no={text_block.block_no}, chapter_id={text_block.chapter_id}, chapter_number={text_block.chapter_number}, chapter_title={text_block.chapter_title}")
                                if text_block.chapter_id and text_block.chapter_id in chapter_content:
                                    if page.page_num not in chapter_content[text_block.chapter_id]['pages']:
                                        chapter_content[text_block.chapter_id]['pages'][page.page_num] = {
                                            'text_blocks': [],
                                            'images': [],
                                            'tables': []
                                        }
                                    chapter_content[text_block.chapter_id]['pages'][page.page_num]['text_blocks'].append(text_block)
                                    logger.info(f"  文本块添加到章节: {text_block.chapter_number} - {text_block.chapter_title}, 页码: {page.page_num}")
                                    
                                    # 同时将内容添加到父章节
                                    chapter = None
                                    for c in all_chapters:
                                        if c.id == text_block.chapter_id:
                                            chapter = c
                                            break
                                    if chapter and chapter.parent and chapter.parent.id in chapter_content:
                                        parent_id = chapter.parent.id
                                        if page.page_num not in chapter_content[parent_id]['pages']:
                                            chapter_content[parent_id]['pages'][page.page_num] = {
                                                'text_blocks': [],
                                                'images': [],
                                                'tables': []
                                            }
                                        chapter_content[parent_id]['pages'][page.page_num]['text_blocks'].append(text_block)
                                        logger.info(f"  文本块添加到父章节: {chapter.parent.number} - {chapter.parent.title}, 页码: {page.page_num}")
                                else:
                                    logger.warning(f"  文本块未找到对应章节: chapter_id={text_block.chapter_id}, chapter_content中存在: {text_block.chapter_id in chapter_content}")
                    
                    # 组织图像
                    for image in images:
                        if image.chapter_id and image.chapter_id in chapter_content:
                            if image.page_num not in chapter_content[image.chapter_id]['pages']:
                                chapter_content[image.chapter_id]['pages'][image.page_num] = {
                                    'text_blocks': [],
                                    'images': [],
                                    'tables': []
                                }
                            chapter_content[image.chapter_id]['pages'][image.page_num]['images'].append(image)
                            logger.debug(f"图像添加到章节: {image.chapter_number} - {image.chapter_title}, 页码: {image.page_num}")
                            
                            # 同时将图像添加到父章节
                            chapter = None
                            for c in all_chapters:
                                if c.id == image.chapter_id:
                                    chapter = c
                                    break
                            if chapter and chapter.parent and chapter.parent.id in chapter_content:
                                parent_id = chapter.parent.id
                                if image.page_num not in chapter_content[parent_id]['pages']:
                                    chapter_content[parent_id]['pages'][image.page_num] = {
                                        'text_blocks': [],
                                        'images': [],
                                        'tables': []
                                    }
                                chapter_content[parent_id]['pages'][image.page_num]['images'].append(image)
                                logger.info(f"图像添加到父章节: {chapter.parent.number} - {chapter.parent.title}, 页码: {image.page_num}")
                    
                    # 清理没有内容的章节
                    chapter_content = {k: v for k, v in chapter_content.items() if v['pages']}
                    logger.info(f"章节内容组织完成，章节数量: {len(chapter_content)}")
                    if chapter_content:
                        logger.info(f"章节ID列表: {list(chapter_content.keys())}")
                        for chapter_id, content in chapter_content.items():
                            page_count = len(content['pages'])
                            total_blocks = sum(len(page['text_blocks']) for page in content['pages'].values())
                            total_images = sum(len(page['images']) for page in content['pages'].values())
                            total_tables = sum(len(page['tables']) for page in content['pages'].values())
                            logger.info(f"章节 {content['number']} - {content['title']}: {page_count}页, {total_blocks}文本块, {total_images}图像, {total_tables}表格")
                    
                    # 生成章节Markdown文件
                    chapter_files = []
                    
                    for chapter_id, content in chapter_content.items():
                        # 生成文件名
                        filename = f"{content['number']} {content['title']}.md"
                        # 清理文件名中的非法字符
                        filename = self._sanitize_filename(filename)
                        file_path = os.path.join(output_dir, filename)
                        logger.info(f"生成章节文件: {file_path}")
                        
                        # 构建章节内容
                        full_text = []
                        
                        # 添加章节标题
                        full_text.append(f"# {content['title']}")
                        full_text.append("")
                        
                        # 处理章节中的所有页面内容
                        chapter_text = self._process_chapter_pages(content['pages'])
                        full_text.append(chapter_text)
                        
                        # 合并文本
                        combined_text = "\n".join(full_text)
                        
                        # 使用布局模型格式化文本为Markdown
                        markdown_result = self._format_with_layout_model(combined_text)
                        
                        # 保存Markdown文件
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(markdown_result.content)
                        
                        chapter_files.append(file_path)
                        logger.info(f"章节Markdown文件生成完成: {file_path}")
                    
                    # 生成章节索引文件
                    index_path = os.path.join(output_dir, "章节索引.md")
                    self._generate_chapter_index(chapters, chapter_files, index_path)
                    
                    return None
        
        # 创建模拟生成器
        markdown_generator = MockMarkdownGenerator()
        
        # 生成章节Markdown文件
        markdown_generator._generate_chapter_markdowns(
            translated_content=translated_content,
            images=images,
            output_dir=temp_dir,
            target_lang='zh',
            doc_id='test_doc',
            chapters=chapters
        )
        
        # 检查生成的文件
        generated_files = os.listdir(temp_dir)
        logger.info(f"生成的文件: {generated_files}")
        
        # 检查章节索引文件
        if "章节索引.md" in generated_files:
            logger.info("✓ 章节索引文件生成成功")
        else:
            logger.error("✗ 章节索引文件生成失败")
        
        # 检查章节文件
        chapter_files = [f for f in generated_files if f.endswith('.md') and f != "章节索引.md"]
        logger.info(f"生成的章节文件数量: {len(chapter_files)}")
        
        # 预期的章节文件
        expected_chapters = [
            "4 The Journey to Production.md",
            "4.1 Evaluation as a Quality Gate.md",
            "4.2 The Automated CI_CD Pipeline.md",
            "4.3 Safe Rollout Strategies.md",
            "4.4 Building Security from the Start.md",
            "5 Operations in-Production.md",
            "5.1 Observe_ Your Agent's Sensory System.md",
            "5.2 Act_ The Levers of Operational Control.md",
            "5.2.1 Managing System Health_ Performance, Cost, and Scale.md",
            "5.2.2 Managing Risk_ The Security Response Playbook.md",
            "5.3 Evolve_ Learning from Production.md",
            "5.3.1 The Engine of Evolution_ An Automated Path to Production.md",
            "5.3.2 The Evolution Workflow_ From Insight to Deployed Improvement.md",
            "5.4 Evolving Security_ The Production Feedback Loop.md",
            "5.5 Beyond Single-Agent Operations.md"
        ]
        
        # 检查是否生成了所有预期的章节文件
        for expected_file in expected_chapters:
            if expected_file in chapter_files:
                logger.info(f"✓ 章节文件生成成功: {expected_file}")
            else:
                logger.error(f"✗ 章节文件生成失败: {expected_file}")
        
        # 检查每个章节文件是否包含内容
        for chapter_file in chapter_files:
            file_path = os.path.join(temp_dir, chapter_file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if content.strip():
                logger.info(f"✓ 章节文件包含内容: {chapter_file}")
            else:
                logger.error(f"✗ 章节文件为空: {chapter_file}")
        
        logger.info("✓ 章节Markdown生成测试完成")
        
    except Exception as e:
        logger.error(f"测试章节Markdown生成时出错: {str(e)}", exc_info=True)

if __name__ == "__main__":
    test_chapter_markdown_generation()
