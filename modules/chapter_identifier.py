import fitz
import logging

logger = logging.getLogger(__name__)

class Chapter:
    """章节模型
    
    表示PDF文档中的一个章节，包含章节标题、层级、编号等信息
    """
    
    def __init__(self, title, level, page_num, parent=None, position=None):
        """初始化章节
        
        Args:
            title (str): 章节标题
            level (int): 章节层级
            page_num (int): 章节起始页码
            parent (Chapter, optional): 父章节. Defaults to None.
            position (tuple, optional): 章节标题在页面上的位置坐标 (x, y). Defaults to None.
        """
        self.title = title
        self.level = level
        self.page_num = page_num
        self.position = position  # 章节标题在页面上的位置坐标
        self.parent = parent
        self.children = []
        self.id = None  # 章节唯一ID
        self.number = None  # 章节编号（如1, 1.1, 1.1.1等）
    
    def add_child(self, child):
        """添加子章节
        
        Args:
            child (Chapter): 子章节
        """
        self.children.append(child)

class ChapterIdentifier:
    """章节识别器
    
    使用PDF书签识别章节结构，构建章节树
    """
    
    def __init__(self):
        """初始化章节识别器"""
        self.chapters = []
        self.chapter_counter = 0
        self.max_level = 3  # 最大章节层级
        self._sorted_chapters = None
        self._chapters_by_page = None
        self._chapter_mapping = None
    
    def extract_bookmarks(self, pdf_path):
        """提取PDF文档的书签信息
        
        Args:
            pdf_path (str): PDF文件路径
            
        Returns:
            list: 章节列表
        """
        try:
            logger.info(f"开始提取PDF书签: {pdf_path}")
            
            with fitz.open(pdf_path) as doc:
                # 提取书签（包含详细位置信息）
                bookmarks = doc.get_toc(simple=False)
                
                if not bookmarks:
                    logger.warning("PDF文档没有书签信息")
                    return []
                
                logger.info(f"提取到 {len(bookmarks)} 个书签")
                
                # 构建章节树
                self.chapters = self._build_chapter_tree(bookmarks, doc)
                
                # 为章节分配编号
                self._assign_chapter_numbers()
                
                # 构建缓存，避免后续方法重复构建
                self._ensure_chapter_cache()
                
                return self.chapters
                
        except Exception as e:
            logger.error(f"提取书签时出错: {str(e)}")
            return []
    
    def _reset_cache(self):
        """重置章节缓存"""
        self._sorted_chapters = None
        self._chapters_by_page = None
        self._chapter_mapping = None
    
    def reset(self):
        """重置章节识别器状态"""
        self.chapters = []
        self.chapter_counter = 0
        self._reset_cache()
    
    def _extract_position(self, dest):
        """提取位置信息
        
        Args:
            dest: PyMuPDF返回的目标信息
            
        Returns:
            tuple: 位置坐标 (x, y) 或 None
        """
        if not dest:
            return None
        
        try:
            if isinstance(dest, dict) and 'to' in dest:
                # 包含直接位置信息
                if isinstance(dest['to'], (list, tuple)) and len(dest['to']) >= 2:
                    return (dest['to'][0], dest['to'][1])
            elif isinstance(dest, (list, tuple)) and len(dest) >= 3:
                # 列表格式：[page_num, x, y, zoom]
                return (dest[1], dest[2])
        except (IndexError, TypeError):
            logger.warning(f"无法解析位置信息: {dest}")
        
        return None
    
    def _find_title_position(self, doc, page_num, title):
        """在页面中查找包含标题名的文本块，并返回其左上角位置
        
        Args:
            doc: PyMuPDF文档对象
            page_num: 页码（1-based）
            title: 章节标题
            
        Returns:
            tuple: 位置坐标 (x, y) 或 None
        """
        try:
            # 检查页码是否有效
            if page_num < 1 or page_num > doc.page_count:
                logger.warning(f"页码 {page_num} 超出范围")
                return None
            
            # 获取页面
            page = doc[page_num - 1]  # PyMuPDF使用0-based索引
            
            # 提取页面中的所有文本块
            blocks = page.get_text('blocks')
            
            # 遍历文本块，查找包含标题的块
            for block in blocks:
                if len(block) >= 4:
                    x0, y0, x1, y1, text, _, _ = block
                    # 只使用标题的前15个字符进行匹配，避免长标题被分成多个文本块
                    title_prefix = title[:15]
                    # 检查文本是否包含标题前缀
                    if title_prefix in text:
                        # 返回文本块的左上角坐标
                        logger.debug(f"找到包含标题 '{title}' 的文本块，位置: ({x0}, {y0})")
                        return (x0, y0)
            
            # 未找到包含标题的文本块
            logger.debug(f"在页面 {page_num} 中未找到包含标题 '{title}' 的文本块")
            return None
        except Exception as e:
            logger.error(f"查找标题位置时出错: {str(e)}")
            return None
    
    def _build_chapter_tree(self, bookmarks, doc):
        """构建章节树
        
        Args:
            bookmarks (list): 书签列表
            doc: PyMuPDF文档对象
            
        Returns:
            list: 章节树
        """
        chapters = []
        stack = []
        
        logger.info(f"开始构建章节树，共 {len(bookmarks)} 个书签")
        
        for i, bookmark in enumerate(bookmarks):
            try:
                logger.debug(f"处理第 {i+1} 个书签: {bookmark}")
                
                if len(bookmark) >= 4:
                    # 详细书签信息：[level, title, page_num, dest, ...]
                    level, title, page_num, dest = bookmark[:4]
                    # 提取位置信息
                    position = self._extract_position(dest)
                    logger.debug(f"书签详细信息: 层级={level}, 标题='{title}', 页码={page_num}, 目标={dest}")
                    if position:
                        logger.info(f"书签 '{title}' 位置: {position}")
                    else:
                        logger.debug(f"书签 '{title}' 无位置信息，开始在页面中查找")
                        # 如果没有位置信息，在页面中查找包含标题名的文本块
                        position = self._find_title_position(doc, page_num, title)
                        if position:
                            logger.info(f"在页面中找到书签 '{title}' 的位置: {position}")
                elif len(bookmark) >= 3:
                    # 简单书签信息：[level, title, page_num]
                    level, title, page_num = bookmark[:3]
                    position = None
                    logger.debug(f"书签简单信息: 层级={level}, 标题='{title}', 页码={page_num}")
                    # 在页面中查找包含标题名的文本块
                    position = self._find_title_position(doc, page_num, title)
                    if position:
                        logger.info(f"在页面中找到书签 '{title}' 的位置: {position}")
                else:
                    # 无效书签，跳过
                    logger.warning(f"无效的书签格式: {bookmark}")
                    continue
                
                # 处理层级
                level = max(1, min(level, self.max_level))
                
                # 处理页码
                page_num = max(0, page_num)
                
                # 创建章节对象
                chapter = Chapter(title, level, page_num, position=position)
                chapter.id = f"chapter_{self.chapter_counter}"
                self.chapter_counter += 1
                
                logger.debug(f"创建章节: ID={chapter.id}, 编号={chapter.number}, 标题='{chapter.title}', 页码={chapter.page_num}, 位置={chapter.position}")
                
                # 处理层级关系
                while stack and stack[-1].level >= level:
                    popped_chapter = stack.pop()
                    logger.debug(f"弹出章节: {popped_chapter.id} - {popped_chapter.title}")
                
                if stack:
                    # 添加为子章节
                    stack[-1].add_child(chapter)
                    chapter.parent = stack[-1]
                    logger.debug(f"添加为子章节: {chapter.id} -> {stack[-1].id}")
                else:
                    # 添加为根章节
                    chapters.append(chapter)
                    logger.debug(f"添加为根章节: {chapter.id}")
                
                stack.append(chapter)
                logger.debug(f"压入章节: {chapter.id} - {chapter.title}")
            except (ValueError, IndexError) as e:
                logger.error(f"处理书签时出错: {str(e)}, 书签: {bookmark}")
                continue
        
        logger.info(f"章节树构建完成，共 {len(chapters)} 个根章节")
        return chapters
    
    def _assign_chapter_numbers(self):
        """为章节分配编号"""
        self._assign_numbers_recursive(self.chapters, "")
    
    def _assign_numbers_recursive(self, chapters, prefix=""):
        """递归为章节分配编号
        
        Args:
            chapters (list): 章节列表
            prefix (str): 父章节编号前缀
        """
        for i, chapter in enumerate(chapters, 1):
            chapter.number = f"{prefix}.{i}" if prefix else str(i)
            
            if chapter.children:
                self._assign_numbers_recursive(chapter.children, chapter.number)
    
    def _collect_all_chapters(self, chapters):
        """收集所有章节
        
        Args:
            chapters (list): 章节列表
            
        Returns:
            list: 所有章节的列表
        """
        all_chapters = []
        for chapter in chapters:
            all_chapters.append(chapter)
            if chapter.children:
                all_chapters.extend(self._collect_all_chapters(chapter.children))
        return all_chapters
    
    def _chapter_sort_key(self, chapter):
        """章节排序键
        
        Args:
            chapter (Chapter): 章节对象
            
        Returns:
            tuple: 排序键
        """
        return (chapter.page_num, chapter.position[1] if chapter.position else 0)
    
    def _build_chapters_by_page(self, all_chapters):
        """按页码分组章节
        
        Args:
            all_chapters (list): 所有章节的列表
            
        Returns:
            dict: 页码到章节列表的映射
        """
        chapters_by_page = {}
        for chapter in all_chapters:
            if chapter.page_num not in chapters_by_page:
                chapters_by_page[chapter.page_num] = []
            chapters_by_page[chapter.page_num].append(chapter)
        return chapters_by_page
    
    def _ensure_chapter_cache(self):
        """确保章节信息已排序和缓存"""
        if not self._sorted_chapters or not self._chapters_by_page:
            # 构建章节映射（包含页码和位置信息）
            self._chapter_mapping = self._build_chapter_mapping()
            
            # 收集所有章节
            all_chapters = self._collect_all_chapters(self.chapters)
            
            # 按页码和位置排序章节
            all_chapters.sort(key=self._chapter_sort_key)
            
            # 按页码分组章节
            chapters_by_page = self._build_chapters_by_page(all_chapters)
            
            # 缓存排序后的章节和按页码分组的章节
            self._sorted_chapters = all_chapters
            self._chapters_by_page = chapters_by_page
    
    def _find_best_chapter(self, page_num, block_y):
        """找到最适合的章节
        
        Args:
            page_num (int): 页码
            block_y (float): 元素的顶部y坐标
            
        Returns:
            Chapter: 最适合的章节
        """
        # 确保章节信息已缓存
        self._ensure_chapter_cache()
        
        # 找到最适合的章节
        best_chapter = None
        
        # 首先查找当前页码的章节
        current_page_chapters = self._chapters_by_page.get(page_num, [])
        
        if current_page_chapters:
            # 找到元素上方最近的章节
            for chapter in current_page_chapters:
                if chapter.position:
                    # 有位置信息的章节，按位置判断
                    if chapter.position[1] <= block_y:
                        best_chapter = chapter
                    else:
                        break
                else:
                    # 没有位置信息的章节，视为覆盖整个页面
                    best_chapter = chapter
                    break
        
        # 如果当前页码没有找到章节，查找前一页的最后一个章节
        if not best_chapter:
            # 找到页码小于当前页码的所有章节
            previous_chapters = [ch for ch in self._sorted_chapters if ch.page_num < page_num]
            if previous_chapters:
                # 找到前一页的最后一个章节
                best_chapter = previous_chapters[-1]
        
        # 如果还是没有找到，使用章节映射（向后兼容）
        if not best_chapter and self._chapter_mapping:
            best_chapter = self._chapter_mapping.get(page_num)
        
        return best_chapter
    
    def associate_text_blocks(self, text_blocks):
        """将文本块关联到对应的章节
        
        Args:
            text_blocks (list): 文本块列表
        """
        # 确保章节信息已缓存
        self._ensure_chapter_cache()
        
        for text_block in text_blocks:
            page_num = text_block.page_num
            block_y = text_block.block_bbox[1]  # 文本块的顶部y坐标
            
            # 找到最适合的章节
            best_chapter = self._find_best_chapter(page_num, block_y)
            
            if best_chapter:
                text_block.chapter_id = best_chapter.id
                text_block.chapter_title = best_chapter.title
                text_block.chapter_level = best_chapter.level
                text_block.chapter_number = best_chapter.number
                # 只在调试模式下输出详细日志
                if logger.isEnabledFor(logging.DEBUG):
                    chapter_position = best_chapter.position if best_chapter.position else "无位置信息"
                    logger.debug(f"文本块 {text_block.block_no} (页码: {page_num}, y: {block_y}) 归属于章节: {best_chapter.number} - {best_chapter.title} (章节位置: {chapter_position})")
    
    def associate_tables(self, tables):
        """将表格关联到对应的章节
        
        Args:
            tables (list): 表格列表
        """
        # 确保章节信息已缓存
        self._ensure_chapter_cache()
        
        for table in tables:
            page_num = table.page_num
            block_y = table.bbox[1]  # 表格的顶部y坐标
            
            # 找到最适合的章节
            best_chapter = self._find_best_chapter(page_num, block_y)
            
            if best_chapter:
                table.chapter_id = best_chapter.id
                table.chapter_title = best_chapter.title
                table.chapter_level = best_chapter.level
                table.chapter_number = best_chapter.number
                # 只在调试模式下输出详细日志
                if logger.isEnabledFor(logging.DEBUG):
                    chapter_position = best_chapter.position if best_chapter.position else "无位置信息"
                    logger.debug(f"表格 (页码: {page_num}, y: {block_y}) 归属于章节: {best_chapter.number} - {best_chapter.title} (章节位置: {chapter_position})")
    
    def associate_images(self, images):
        """将图像关联到对应的章节
        
        Args:
            images (list): 图像列表
        """
        # 确保章节信息已缓存
        self._ensure_chapter_cache()
        
        for image in images:
            page_num = image.page_num
            block_y = image.bbox[1]  # 图像的顶部y坐标
            
            # 找到最适合的章节
            best_chapter = self._find_best_chapter(page_num, block_y)
            
            if best_chapter:
                image.chapter_id = best_chapter.id
                image.chapter_title = best_chapter.title
                image.chapter_level = best_chapter.level
                image.chapter_number = best_chapter.number
                # 只在调试模式下输出详细日志
                if logger.isEnabledFor(logging.DEBUG):
                    chapter_position = best_chapter.position if best_chapter.position else "无位置信息"
                    logger.debug(f"图像 (页码: {page_num}, y: {block_y}) 归属于章节: {best_chapter.number} - {best_chapter.title} (章节位置: {chapter_position})")
    
    def _build_chapter_mapping(self):
        """构建章节页码映射
        
        Returns:
            dict: 页码到章节的映射
        """
        mapping = {}
        
        # 收集所有章节及其页码
        all_chapters = self._collect_all_chapters(self.chapters)
        
        # 按页码排序章节
        all_chapters.sort(key=lambda c: c.page_num)
        
        # 为每个页码范围分配章节
        for i, chapter in enumerate(all_chapters):
            start_page = chapter.page_num
            # 确定结束页码（下一个章节的起始页码减1）
            end_page = all_chapters[i + 1].page_num - 1 if i < len(all_chapters) - 1 else 999999
            
            # 为范围内的每个页码分配章节
            for page_num in range(start_page, end_page + 1):
                mapping[page_num] = chapter
        
        return mapping
    
    def get_chapters(self):
        """获取章节列表
        
        Returns:
            list: 章节列表
        """
        return self.chapters
    
    def has_chapters(self):
        """检查是否有章节
        
        Returns:
            bool: 是否有章节
        """
        return len(self.chapters) > 0
