import fitz
import logging
import difflib
import os

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
        self.title_block_nos = []  # 标题对应的文本块编号列表
    
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
    
    def __init__(self, default_chapter_titles=None, default_chapter_level=1, enable_default_chapters=True, use_smart_naming=True, max_title_length=20):
        """初始化章节识别器
        
        Args:
            default_chapter_titles (list, optional): 默认章节标题列表. Defaults to ["封面", "目录", "前言", "引言"].
            default_chapter_level (int, optional): 默认章节层级. Defaults to 1.
            enable_default_chapters (bool, optional): 是否启用默认章节. Defaults to True.
            use_smart_naming (bool, optional): 是否使用智能命名（页面第一个文本块）. Defaults to True.
            max_title_length (int, optional): 标题最大长度（字符）. Defaults to 20.
        """
        self.chapters = []
        self.chapter_counter = 0
        self.max_level = 3  # 最大章节层级
        self.default_chapter_titles = default_chapter_titles if default_chapter_titles is not None else ["封面", "目录", "前言", "引言"]
        self.default_chapter_level = default_chapter_level
        self.enable_default_chapters = enable_default_chapters
        self.use_smart_naming = use_smart_naming
        self.max_title_length = max_title_length
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
                total_pages = doc.page_count
                logger.info(f"PDF文档总页数: {total_pages}")
                
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
                
                # 创建默认章节
                if self.enable_default_chapters:
                    logger.info("启用默认章节功能")
                    pages_without_chapters = self._detect_pages_without_chapters(total_pages, self.chapters)
                    if pages_without_chapters:
                        logger.info(f"检测到 {len(pages_without_chapters)} 个无章节页码: {pages_without_chapters}")
                        default_chapters = self._create_default_chapters(pages_without_chapters, doc, pdf_path)
                        logger.info(f"创建了 {len(default_chapters)} 个默认章节")
                        
                        # 将默认章节添加到开头
                        for chapter in reversed(default_chapters):
                            self.chapters.insert(0, chapter)
                        
                        # 重新分配编号
                        self._assign_chapter_numbers()
                        
                        # 重置并重新构建缓存
                        self._reset_cache()
                        self._ensure_chapter_cache()
                    else:
                        logger.info("没有检测到需要创建默认章节的页码")
                else:
                    logger.info("默认章节功能未启用")
                
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
    
    def _get_first_text_block(self, doc, page_num):
        """获取页面第一个文本块
        
        Args:
            doc: PyMuPDF文档对象
            page_num: 页码（1-based）
            
        Returns:
            str: 第一个文本块的文本，或None
        """
        try:
            if page_num < 1 or page_num > doc.page_count:
                logger.warning(f"页码 {page_num} 超出范围")
                return None
            
            page = doc[page_num - 1]
            
            text = page.get_text().strip()
            if text:
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line:
                        logger.debug(f"页面 {page_num} 第一个文本: '{line}'")
                        return line
            
            logger.debug(f"页面 {page_num} 没有文本")
            return None
        except Exception as e:
            logger.error(f"获取页面 {page_num} 第一个文本块时出错: {str(e)}")
            return None
    
    def _truncate_title(self, text):
        """截断标题文本
        
        Args:
            text (str): 原始文本
            
        Returns:
            str: 截断后的文本
        """
        if not text:
            return text
        
        text = text.strip()
        if len(text) <= self.max_title_length:
            return text
        
        truncated = text[:self.max_title_length].rstrip()
        return f"{truncated}..."
    
    def reset(self):
        """重置章节识别器状态"""
        self.chapters = []
        self.chapter_counter = 0
        self._reset_cache()
    
    def _locate_title_blocks(self, doc, page_num, title):
        """在页面中查找包含标题名的文本块，并返回其位置和块编号列表
        
        Args:
            doc: PyMuPDF文档对象
            page_num: 页码（1-based）
            title: 章节标题
            
        Returns:
            tuple: (位置坐标 (x, y), 块编号列表) 或 (None, [])
        """
        try:
            if page_num < 1 or page_num > doc.page_count:
                logger.warning(f"页码 {page_num} 超出范围")
                return None, []
            
            page = doc[page_num - 1]
            blocks = page.get_text('blocks', flags=1)
            
            if not blocks:
                logger.debug(f"页面 {page_num} 没有文本块")
                return None, []
            
            sorted_blocks = sorted(blocks, key=lambda x: x[1])
            
            logger.info(f"[DEBUG] _locate_title_blocks 页面{page_num}: 原始块数量={len(blocks)}, 排序后块数量={len(sorted_blocks)}")
            
            candidates = []
            normalized_title = title.strip()
            
            for display_order, block in enumerate(sorted_blocks):
                if len(block) >= 6:
                    x0, y0, _, _, text, original_block_no, _ = block
                    normalized_text = text.strip()
                    
                    if normalized_text == normalized_title:
                        candidates.append({
                            'score': 100,
                            'position': (x0, y0),
                            'type': 'exact_match',
                            'block_nos': [original_block_no],
                            'text': text
                        })
                        logger.debug(f"找到精确匹配: '{text}'")
                    
                    similarity = difflib.SequenceMatcher(None, normalized_text, normalized_title).ratio()
                    if similarity > 0.9:
                        candidates.append({
                            'score': 90 + similarity * 10,
                            'position': (x0, y0),
                            'type': 'high_similarity',
                            'similarity': similarity,
                            'block_nos': [original_block_no],
                            'text': text
                        })
                        logger.debug(f"找到高相似度匹配: '{text}', 相似度: {similarity:.3f}")
                    
                    if normalized_title in normalized_text:
                        candidates.append({
                            'score': 50,
                            'position': (x0, y0),
                            'type': 'substring_match',
                            'block_nos': [original_block_no],
                            'text': text
                        })
                        logger.debug(f"找到子字符串匹配: '{text}'")
            
            for display_order in range(len(sorted_blocks)):
                merged_text = ''
                for j in range(min(3, len(sorted_blocks) - display_order)):
                    block = sorted_blocks[display_order + j]
                    if len(block) >= 6:
                        merged_text += block[4].strip()
                        normalized_merged = merged_text
                        if normalized_merged == normalized_title:
                            x0, y0 = sorted_blocks[display_order][:2]
                            merged_blocks = sorted_blocks[display_order:display_order + j + 1]
                            block_nos = [b[5] for b in merged_blocks]
                            candidates.append({
                                'score': 80 + j * 5,
                                'position': (x0, y0),
                                'type': 'cross_block_match',
                                'block_count': j + 1,
                                'block_nos': block_nos,
                                'text': merged_text
                            })
                            logger.debug(f"找到跨块匹配: 合并{j + 1}个块, 文本: '{merged_text}'")
                            break
            
            if candidates:
                candidates.sort(key=lambda x: -x['score'])
                best_match = candidates[0]
                logger.info(f"为标题 '{title}' 找到最佳匹配: 类型={best_match['type']}, 位置={best_match['position']}, 块编号={best_match['block_nos']}")
                return best_match['position'], best_match['block_nos']
            
            logger.debug(f"在页面 {page_num} 中未找到包含标题 '{title}' 的文本块")
            return None, []
        except Exception as e:
            logger.error(f"查找标题位置时出错: {str(e)}")
            return None, []
    
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
                
                if len(bookmark) >= 3:
                    # 简单书签信息：[level, title, page_num]
                    level, title, page_num = bookmark[:3]
                    position = None
                    title_block_nos = []
                    logger.debug(f"书签简单信息: 层级={level}, 标题='{title}', 页码={page_num}")
                    # 在页面中查找包含标题名的文本块
                    position, title_block_nos = self._locate_title_blocks(doc, page_num, title)
                    if position:
                        logger.info(f"在页面中找到书签 '{title}' 的位置: {position}, 块编号: {title_block_nos}")
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
                chapter.title_block_nos = title_block_nos
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
        
        logger.info(f"[DEBUG] associate_text_blocks: 开始关联 {len(text_blocks)} 个文本块")
        
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
                # 检查是否为标题块：需要同时满足block_no匹配且页码相同
                title_block_nos = getattr(best_chapter, 'title_block_nos', [])
                chapter_page_num = getattr(best_chapter, 'page_num', None)
                is_title = False
                if title_block_nos and text_block.block_no in title_block_nos and chapter_page_num == text_block.page_num:
                    text_block.is_title_block = True
                    is_title = True
                else:
                    text_block.is_title_block = False
                    is_title = False
                logger.info(f"[DEBUG] 文本块 block_no={text_block.block_no}, title_block_nos={title_block_nos}, chapter_page_num={chapter_page_num}, text_page_num={text_block.page_num}, is_title_block={is_title}")
                # 输出INFO日志
                chapter_position = best_chapter.position if best_chapter.position else "无位置信息"
                logger.info(f"文本块 {text_block.block_no} (页码: {page_num}, y: {block_y}) 归属于章节: {best_chapter.number} - {best_chapter.title} (章节位置: {chapter_position})")
            else:
                # 输出WARNING日志
                logger.warning(f"文本块 {text_block.block_no} (页码: {page_num}, y: {block_y}) 未找到对应章节")
    
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
                # 输出INFO日志
                chapter_position = best_chapter.position if best_chapter.position else "无位置信息"
                logger.info(f"表格 (页码: {page_num}, y: {block_y}) 归属于章节: {best_chapter.number} - {best_chapter.title} (章节位置: {chapter_position})")
            else:
                # 输出WARNING日志
                logger.warning(f"表格 (页码: {page_num}, y: {block_y}) 未找到对应章节")
    
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
                # 输出INFO日志
                chapter_position = best_chapter.position if best_chapter.position else "无位置信息"
                logger.info(f"图像 (页码: {page_num}, y: {block_y}) 归属于章节: {best_chapter.number} - {best_chapter.title} (章节位置: {chapter_position})")
            else:
                # 输出WARNING日志
                logger.warning(f"图像 (页码: {page_num}, y: {block_y}) 未找到对应章节")
    
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
    
    def _detect_pages_without_chapters(self, total_pages, chapters):
        """检测开头连续无章节的页码
        
        Args:
            total_pages (int): PDF总页数
            chapters (list): 现有章节列表
            
        Returns:
            list: 开头连续无章节的页码列表 (1-based)
        """
        if not chapters:
            return list(range(1, total_pages + 1))
        
        all_chapters = self._collect_all_chapters(chapters)
        if not all_chapters:
            return list(range(1, total_pages + 1))
        
        first_chapter_page = min(ch.page_num for ch in all_chapters)
        
        if first_chapter_page <= 1:
            return []
        
        return list(range(1, first_chapter_page))
    
    def _create_default_chapters(self, pages_without_chapters, doc, pdf_path):
        """创建默认章节
        
        Args:
            pages_without_chapters (list): 需要创建默认章节的页码列表
            doc: PyMuPDF文档对象
            pdf_path (str): PDF文件路径
            
        Returns:
            list: 创建的默认章节列表
        """
        default_chapters = []
        
        file_name = os.path.splitext(os.path.basename(pdf_path))[0]
        
        for index, page_num in enumerate(pages_without_chapters):
            if self.use_smart_naming:
                first_text = self._get_first_text_block(doc, page_num)
                if first_text:
                    title = self._truncate_title(first_text)
                    logger.info(f"页面 {page_num} 使用智能命名: '{title}'")
                else:
                    title = f"{file_name}-第{page_num}页"
                    logger.info(f"页面 {page_num} 无文本块，使用文件名和页号: '{title}'")
            else:
                if index < len(self.default_chapter_titles):
                    title = self.default_chapter_titles[index]
                else:
                    base_title = self.default_chapter_titles[-1] if self.default_chapter_titles else "默认"
                    title = f"{base_title}{index - len(self.default_chapter_titles) + 2}"
            
            chapter = Chapter(
                title=title,
                level=self.default_chapter_level,
                page_num=page_num,
                position=(0, 0)
            )
            chapter.id = f"chapter_{self.chapter_counter}"
            
            default_chapters.append(chapter)
            self.chapter_counter += 1
        
        return default_chapters
    
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
