import os
import logging
import shutil
from openai import OpenAI

logger = logging.getLogger(__name__)

class MarkdownGenerator:
    """Markdown生成器类
    
    负责将翻译后的文本使用大模型转换为Markdown格式，支持文本、表格和图像的生成。
    """
    
    def __init__(self, api_key, api_url, model):
        """初始化MarkdownGenerator对象
        
        Args:
            api_key (str): API密钥
            api_url (str): API请求地址
            model (str): 布局模型名称
        """
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        # 初始化OpenAI客户端
        self.client = OpenAI(
            base_url=self.api_url,
            api_key=self.api_key,
            timeout=30.0,  # 添加超时设置，30秒
        )
        logger.info("Markdown生成器初始化完成")
    
    def _load_layout_prompt(self):
        """加载布局提示词模板
        
        Returns:
            str: 布局提示词模板
        """
        # 直接返回硬编码的提示词，与翻译类似
        return """
# 任务：将文本转换为结构化 Markdown

请你扮演一个专业的编辑，在不改变原文的基础上，将提供的内容转成格式良好、结构清晰、重点突出的 Markdown 文档。

## A. 内部推理步骤 (请在你的思考过程中执行，无需输出)

在生成最终的 Markdown 之前，请先在内部完成以下思考：

1.  **理解与提取**：
    * 通读全文，准确把握文章的核心主旨和目的。
    * 识别并提取文中的**核心论点**、**关键结论**和**重要定义**。
    * 找出文中具有高度概括性或特别精辟的**"金句" (Golden Sentences)**。

## B. 最终输出规范 (请严格按此格式生成)

请根据你的内部推理，生成符合以下所有规范的 Markdown 文本：

1.  **内容结构**：
    * 保持内容不变情况下，不改变文章的结构和组织。
    * 原文一致，不丢失原文内容，不出现原文没有的内容
2.  **突出重点 (句子优先)**：
    * 内容跟原文一致，不丢失原文内容，不出现原文没有的内容，
    * **有选择性地**使用粗体 (`**`) 来突出你在步骤 A.1 确定的**核心论点**、**关键结论**、**重要定义**或**金句**。
    * **优先加粗**：优先考虑加粗**能够概括要点的完整句子**或**关键短语**。
    * **避免**：避免只加粗零散的单个关键词，并**切勿过度使用粗体**，保持文档的专业性和易读性。
3.  **【!!!】重要格式规范**：
    * 在设置粗体时，**绝对不要**将任何标点符号（如 `。`、`，`、`：`、`"`、`（`、`）` 等）包含在 `**` 标记内部。
    * ✅ **正确示例**(标点在 `**` 之外)：这是"**一个核心观点**"。
    * ❌ **错误示例**：这是**"一个核心观点"**。
4.  **【!!!】禁止使用代码块标记**：
    * **绝对不要**在输出的开头或结尾添加 ```markdown ``` 或任何其他代码块标记。
    * 直接返回纯 Markdown 文本内容，不需要任何包装或标记。
        """
    
    def _format_with_layout_model(self, text):
        """使用布局模型格式化文本为Markdown
        
        Args:
            text (str): 要格式化的文本
            
        Returns:
            str: 格式化后的Markdown文本
        """
        logger.info("使用布局模型格式化文本为Markdown")
        
        # 加载布局提示词模板
        system_prompt = self._load_layout_prompt()
        
        # 构建用户提示词
        user_prompt = f"请将以下内容转换为Markdown格式：\n\n{text}"
        
        max_retries = 3  # 最大重试次数
        retry_delay = 2  # 重试间隔（秒）
        
        import time
        
        for attempt in range(max_retries):
            try:
                # 调用布局模型API（使用流式）
                stream = self.client.chat.completions.create(
                    model=self.model,
                    stream=True,  # 启用流式响应
                    temperature=0.1,  # 降低温度，提高格式一致性
                    max_tokens=8192,  # 最大token数
                    timeout=60.0,  # 增加超时时间
                    n=1,  # 只返回一个结果
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": user_prompt
                        }
                    ]
                )
                
                # 处理流式响应
                formatted_text = ""
                for chunk in stream:
                    if chunk.choices and len(chunk.choices) > 0:
                        choice = chunk.choices[0]
                        if choice.delta and choice.delta.content:
                            formatted_text += choice.delta.content
                
                formatted_text = formatted_text.strip()
                
                if not formatted_text:
                    raise Exception("布局模型返回空响应")
                
                logger.info("布局模型格式化完成")
                return formatted_text
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    # 不是最后一次尝试，记录错误并重试
                    logger.warning(f"布局模型请求失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}，将在 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                else:
                    # 最后一次尝试失败，抛出异常
                    logger.error(f"布局模型请求失败: {str(e)}")
                    # 直接抛出异常，不使用降级方案
                    raise Exception(f"布局模型请求失败: {str(e)}")
    
    def _convert_table_to_markdown(self, table):
        """将表格转换为Markdown格式
        
        Args:
            table (dict): 表格对象
            
        Returns:
            str: Markdown格式的表格
        """
        cells = table.get('cells', [])
        if not cells:
            return ""
        
        # 获取表格尺寸
        num_rows = len(cells)
        num_cols = len(cells[0]) if num_rows > 0 else 0
        
        if num_rows == 0 or num_cols == 0:
            return ""
        
        # 构建Markdown表格
        markdown_table = []
        
        # 添加表头行
        header_row = cells[0]
        row_cells = []
        for cell in header_row:
            cell_text = cell.get('text', '') if isinstance(cell, dict) else str(cell)
            row_cells.append(cell_text)
        markdown_table.append("|" + "|".join(row_cells) + "| ")
        
        # 添加表头分隔线
        header_separator = ["---"] * num_cols
        markdown_table.append(" |" + "|".join(header_separator) + "| ")
        
        # 添加表格内容（跳过表头行）
        for i, row in enumerate(cells[1:]):
            row_cells = []
            for cell in row:
                cell_text = cell.get('text', '') if isinstance(cell, dict) else str(cell)
                row_cells.append(cell_text)
            if i == len(cells[1:]) - 1:
                # 最后一行
                markdown_table.append(" |" + "|".join(row_cells) + "|")
            else:
                # 非最后一行
                markdown_table.append(" |" + "|".join(row_cells) + "| ")
        
        return "\n".join(markdown_table) + "\n"
    
    def _copy_images_to_output(self, images, output_dir, doc_id):
        """复制图像到输出目录
        
        Args:
            images (list): 图像对象列表
            output_dir (str): 输出目录
            doc_id (str): 文档唯一标识符
            
        Returns:
            list: 更新后的图像对象列表，包含相对路径
        """
        updated_images = []
        # 为每个文档创建独立的图像目录
        images_dir = os.path.join(output_dir, f'images_{doc_id}')
        os.makedirs(images_dir, exist_ok=True)
        
        for image in images:
            image_path = image.image_path
            if os.path.exists(image_path):
                # 生成新的图像文件名
                image_filename = os.path.basename(image_path)
                dest_path = os.path.join(images_dir, image_filename)
                
                # 复制图像
                try:
                    shutil.copy(image_path, dest_path)
                    # 更新图像路径为相对路径
                    relative_path = os.path.join(f'images_{doc_id}', image_filename)
                    updated_image = type('obj', (object,), {
                        'page_num': image.page_num,
                        'image_idx': image.image_idx,
                        'image_path': relative_path,
                        'bbox': image.bbox
                    })
                    updated_images.append(updated_image)
                    logger.info(f"复制图像成功: {image_path} -> {dest_path}")
                except Exception as e:
                    logger.error(f"复制图像失败: {e}")
                    # 保持原始图像路径
                    updated_images.append(image)
            else:
                updated_images.append(image)
        
        return updated_images
    
    def _process_page_elements(self, page_elements, text_blocks, full_text):
        """处理页面元素，按顺序添加到Markdown文档
        
        Args:
            page_elements (list): 排序后的页面元素列表
            text_blocks (list): 文本块列表
            full_text (list): 完整文本列表，用于存储生成的Markdown内容
        """
        # 跟踪已处理的文本块索引
        processed_blocks = set()
        
        # 预处理：检测元素是否位于文本块内部
        elements_with_context = []
        
        for element in page_elements:
            element_type = element['type']
            
            if element_type in ['image', 'table']:
                # 检查是否位于某个文本块内部
                containing_block = None
                insertion_point = 0.5  # 默认插入点（中间位置）
                
                elem_y = element['y_position']
                
                for block_idx, block in enumerate(text_blocks):
                    if block_idx not in processed_blocks:
                            block_bbox = block.bbox
                            if len(block_bbox) >= 4:
                                block_y0, block_y1 = block_bbox[1], block_bbox[3]
                                
                                # 检查元素是否位于文本块内部
                                if block_y0 <= elem_y <= block_y1:
                                    containing_block = {
                                        'block': block,
                                        'block_idx': block_idx
                                    }
                                    # 计算插入点比例
                                    insertion_point = (elem_y - block_y0) / (block_y1 - block_y0) if (block_y1 - block_y0) > 0 else 0.5
                                    break
                
                elements_with_context.append({
                    'element': element,
                    'containing_block': containing_block,
                    'insertion_point': insertion_point
                })
            
            elif element_type == 'text':
                elements_with_context.append({
                    'element': element,
                    'containing_block': None
                })
        
        # 处理元素
        for item in elements_with_context:
            element = item['element']
            element_type = element['type']
            containing_block = item.get('containing_block')
            
            if element_type == 'text':
                # 添加文本块
                block = element['content']
                block_idx = element['block_idx']
                
                if block_idx not in processed_blocks:
                    full_text.append(block.block_text)
                    full_text.append("")
                    processed_blocks.add(block_idx)
            
            elif element_type in ['image', 'table']:
                if containing_block:
                    # 元素位于文本块内部，需要拆分文本
                    block = containing_block['block']
                    block_idx = containing_block['block_idx']
                    insertion_point = item.get('insertion_point', 0.5)
                    
                    if block_idx not in processed_blocks:
                        # 拆分文本并插入元素
                        self._insert_element_in_text_block(
                            block, element, insertion_point, full_text
                        )
                        processed_blocks.add(block_idx)
                    else:
                        # 文本块已处理，直接添加元素
                        if element_type == 'image':
                            self._add_image_to_markdown(element['content'], full_text)
                        elif element_type == 'table':
                            self._add_table_to_markdown(element['content'], full_text)
                else:
                    # 元素位于文本块之间，直接添加
                    if element_type == 'image':
                        self._add_image_to_markdown(element['content'], full_text)
                    elif element_type == 'table':
                        self._add_table_to_markdown(element['content'], full_text)
    
    def _insert_element_in_text_block(self, text_block, element, insertion_point, full_text):
        """在文本块内部插入元素，拆分文本
        
        Args:
            text_block: 文本块对象
            element: 要插入的元素
            insertion_point: 插入点比例（0-1）
            full_text: 完整文本列表
        """
        text = text_block.block_text
        text_length = len(text)
        
        # 计算插入位置
        split_index = int(text_length * insertion_point)
        
        # 尝试在单词边界拆分
        if split_index > 0 and split_index < text_length:
            # 向前查找空格或标点
            while split_index > 0 and text[split_index-1].isalnum():
                split_index -= 1
        
        # 拆分为前后两段
        text_before = text[:split_index].rstrip()
        text_after = text[split_index:].lstrip()
        
        # 添加前段文本
        if text_before:
            full_text.append(text_before)
            full_text.append("")
        
        # 添加元素
        if element['type'] == 'image':
            self._add_image_to_markdown(element['content'], full_text)
        elif element['type'] == 'table':
            self._add_table_to_markdown(element['content'], full_text)
        
        # 添加后段文本
        if text_after:
            full_text.append(text_after)
            full_text.append("")
    
    def _add_image_to_markdown(self, image, full_text):
        """添加图像到Markdown文档
        
        Args:
            image: 图像对象
            full_text: 完整文本列表
        """
        image_path = image.image_path
        # 使用Markdown图像语法
        image_md = f"![]({image_path})"
        full_text.append("")
        full_text.append(image_md)
        full_text.append("")
    
    def _add_table_to_markdown(self, table, full_text):
        """添加表格到Markdown文档
        
        Args:
            table: 表格对象
            full_text: 完整文本列表
        """
        table_md = self._convert_table_to_markdown(table)
        if table_md:
            full_text.append("")
            full_text.append(table_md)
            full_text.append("")
    
    def generate_markdown(self, translated_content, images, output_md_path, target_lang="zh", doc_id=None):
        """生成翻译后的Markdown文档
        
        Args:
            translated_content (dict): 翻译后的内容
                - blocks (list): 每页的完整文本块列表 (翻译后的文本块)
                    - page_num (int): 页码
                    - text_blocks (list): TextBlock对象列表
                        - block_text (str): 完整文本块内容 (已翻译)
                        - block_bbox (tuple): 文本块位置 (x0, y0, x1, y1)
                        - block_no (int): 块编号
                        - block_type (int): 块类型
                - merged_translations (list): 合并后的翻译结果
                    - text (str): 合并后的翻译文本
                    - page_num (int): 页码
                    - font (str): 字体名称
                    - font_size (float): 字体大小
                    - color (int): 颜色值
                    - bold (bool): 是否粗体
                    - italic (bool): 是否斜体
                    - bbox (tuple): 文本块边界框 (x0, y0, x1, y1)
                - tables (list): 翻译后的表格列表
            images (list): 图像信息列表
                - page_num (int): 页码
                - image_idx (int): 图像索引
                - image_path (str): 图像路径
                - bbox (tuple): 图像位置
            output_md_path (str): 输出Markdown文件路径
            target_lang (str): 目标语言代码
            doc_id (str): 文档唯一标识符，用于创建独立的图像目录
        """
        logger.info(f"开始生成Markdown文档，输出文件: {output_md_path}, 目标语言: {target_lang}")
        
        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(output_md_path)
            os.makedirs(output_dir, exist_ok=True)
            
            # 如果没有提供doc_id，使用文件名的一部分作为doc_id
            if not doc_id:
                doc_id = os.path.splitext(os.path.basename(output_md_path))[0]
            
            # 复制图像到输出目录
            updated_images = self._copy_images_to_output(images, output_dir, doc_id)
            
            # 按页码组织合并后的翻译结果
            merged_by_page = {}
            for item in translated_content.get('merged_translations', []):
                page_num = item.page_num
                if page_num not in merged_by_page:
                    merged_by_page[page_num] = []
                merged_by_page[page_num].append(item)
            
            # 按页码组织图像
            images_by_page = {}
            for image in updated_images:
                page_num = image.page_num
                if page_num not in images_by_page:
                    images_by_page[page_num] = []
                images_by_page[page_num].append(image)
            
            # 按页码组织表格
            tables_by_page = {}
            if 'tables' in translated_content:
                for table in translated_content['tables']:
                    page_num = table.get('page_num', 1)  # 默认页码为1
                    if page_num not in tables_by_page:
                        tables_by_page[page_num] = []
                    tables_by_page[page_num].append(table)
            
            # 获取所有页码的列表
            all_pages = set(merged_by_page.keys())
            all_pages.update(images_by_page.keys())
            all_pages.update(tables_by_page.keys())
            sorted_pages = sorted(all_pages)
            
            # 构建完整文本
            full_text = []
            
            for page_num in sorted_pages:
                # 收集当前页的所有元素
                page_elements = []
                
                # 添加文本块元素
                text_blocks = merged_by_page.get(page_num, [])
                for block_idx, block in enumerate(text_blocks):
                    # 尝试获取文本块的边界框
                    bbox = block.bbox
                    y_position = bbox[1] if len(bbox) >= 2 else 0
                    
                    page_elements.append({
                        'type': 'text',
                        'content': block,
                        'y_position': y_position,
                        'block_idx': block_idx
                    })
                
                # 添加图像元素
                page_images = images_by_page.get(page_num, [])
                for image_idx, image in enumerate(page_images):
                    y_position = image.bbox[1] if image.bbox else 0
                    
                    page_elements.append({
                        'type': 'image',
                        'content': image,
                        'y_position': y_position
                    })
                
                # 添加表格元素
                page_tables = tables_by_page.get(page_num, [])
                for table in page_tables:
                    bbox = table.get('bbox', (0, 0, 0, 0))
                    y_position = bbox[1] if len(bbox) >= 2 else 0
                    
                    page_elements.append({
                        'type': 'table',
                        'content': table,
                        'y_position': y_position
                    })
                
                # 按垂直位置排序元素
                page_elements.sort(key=lambda x: x['y_position'])
                
                # 处理排序后的元素
                self._process_page_elements(page_elements, text_blocks, full_text)
            
            # 合并文本
            combined_text = "\n".join(full_text)
            
            # 使用布局模型格式化文本
            formatted_text = self._format_with_layout_model(combined_text)
            
            # 保存Markdown文件
            with open(output_md_path, 'w', encoding='utf-8') as f:
                f.write(formatted_text)
            
            logger.info(f"Markdown文档生成完成，输出文件: {output_md_path}")
            
        except Exception as e:
            logger.error(f"生成Markdown文档时出错: {str(e)}", exc_info=True)
            raise Exception(f"生成Markdown文档时出错: {str(e)}")
