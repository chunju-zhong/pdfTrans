import os
import logging
import shutil
from openai import OpenAI

logger = logging.getLogger(__name__)

class MarkdownGenerator:
    """Markdown生成器基类
    
    负责将翻译后的文本转换为Markdown格式，支持文本、表格和图像的生成。
    可被扩展以支持不同的API平台，如硅基流动等。
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
        # 设置max_tokens属性，默认值为8192
        self.max_tokens = 8192
        # 初始化OpenAI客户端
        self.client = self._initialize_client()
        logger.info("Markdown生成器初始化完成")
    
    def _initialize_client(self):
        """初始化API客户端
        
        子类可以重写此方法以使用不同的API客户端实现
        
        Returns:
            初始化后的API客户端
        """
        return OpenAI(
            base_url=self.api_url,
            api_key=self.api_key,
            timeout=30.0,  # 添加超时设置，30秒
        )
    
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

1.  **主标题 (H1)**：
    * 使用 `# 标题` 格式，采用你在步骤 A.3 中选定的最佳标题。
2.  **内容结构**：
    * 保持内容不变情况下，不改变文章的结构和组织。
    * 原文一致，不丢失原文内容，不出现原文没有的内容
    * 适当拆分长分段，保持逻辑清晰
3.  **突出重点 (句子优先)**：
    * 内容跟原文一致，不丢失原文内容，不出现原文没有的内容，
    * **有选择性地**使用粗体 (`**`) 来突出你在步骤 A.1 确定的**核心论点**、**关键结论**、**重要定义**或**金句**。
    * **优先加粗**：优先考虑加粗**能够概括要点的完整句子**或**关键短语**。
    * **避免**：避免只加粗零散的单个关键词，并**切勿过度使用粗体**，保持文档的专业性和易读性。
4.  **【!!!】重要格式规范**：
    * 在设置粗体时，**绝对不要**将任何标点符号（如 `。`、`，`、`：`、`"`、`（`、`）` 等）包含在 `**` 标记内部。
    * ✅ **正确示例**(标点在 `**` 之外)：这是"**一个核心观点**"。
    * ❌ **错误示例**：这是**"一个核心观点"**。
5.  **【!!!】禁止使用代码块标记**：
    * **绝对不要**在输出的开头或结尾添加 ```markdown ``` 或任何其他代码块标记。
    * 直接返回纯 Markdown 文本内容，不需要任何包装或标记。
6.  **【!!!】保留图像元素**：
    * **绝对不要**删除或修改任何图像URL元素，保持所有图像URL的完整性。
    * 图像URL格式为 `![image](path/to/image.png)`，请确保完全保留这些元素。
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
                formatted_text = self._call_api(system_prompt, user_prompt)
                
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
    
    def _call_api(self, system_prompt, user_prompt):
        """调用API进行文本格式化
        
        子类可以重写此方法以使用不同的API调用方式
        
        Args:
            system_prompt (str): 系统提示词
            user_prompt (str): 用户提示词
            
        Returns:
            str: 格式化后的文本
        """
        # 调用布局模型API（使用流式）
        stream = self.client.chat.completions.create(
            model=self.model,
            stream=True,  # 启用流式响应
            temperature=0.1,  # 降低温度，提高格式一致性
            max_tokens=self.max_tokens,  # 使用类属性作为最大token数
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
        
        # 处理流式响应 - 逐块接收并拼接
        formatted_text = ""
        for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                choice = chunk.choices[0]
                if choice.delta and choice.delta.content:
                    formatted_text += choice.delta.content
        
        return formatted_text


class AipingMarkdownGenerator(MarkdownGenerator):
    """Aiping特定的Markdown生成器
    
    继承自MarkdownGenerator基类，实现aiping特定的参数设置，
    特别是在extra_body中定义费用优先策略。
    """
    
    def _call_api(self, system_prompt, user_prompt):
        """调用Aiping API进行文本格式化
        
        重写基类方法以添加aiping特定的参数设置，
        在extra_body中定义费用优先策略。
        
        Args:
            system_prompt (str): 系统提示词
            user_prompt (str): 用户提示词
            
        Returns:
            str: 格式化后的文本
        """
        # 构建额外参数，定义费用优先策略
        extra_body = {
            "provider": {
                "only": [],
                "order": [],
                "sort": "output_price",
                "input_price_range": [],
                "output_price_range": [],
                "input_length_range": [],
                "throughput_range": [],
                "latency_range": []
            }
        }
        
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
            ],
            extra_body=extra_body  # 添加aiping特定参数
        )
        
        # 处理流式响应 - 逐块接收并拼接
        formatted_text = ""
        for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                choice = chunk.choices[0]
                if choice.delta and choice.delta.content:
                    formatted_text += choice.delta.content
        
        return formatted_text
    
    def _convert_table_to_markdown(self, table):
        """将表格转换为Markdown格式
        
        Args:
            table: 表格对象
            
        Returns:
            str: Markdown格式的表格
        """
        cells = table.cells
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
            cell_text = cell.text if hasattr(cell, 'text') else str(cell)
            row_cells.append(cell_text)
        markdown_table.append("|" + "|".join(row_cells) + "| ")
        
        # 添加表头分隔线
        header_separator = ["---"] * num_cols
        markdown_table.append(" |" + "|".join(header_separator) + "| ")
        
        # 添加表格内容（跳过表头行）
        for i, row in enumerate(cells[1:]):
            row_cells = []
            for cell in row:
                cell_text = cell.text if hasattr(cell, 'text') else str(cell)
                row_cells.append(cell_text)
            if i == len(cells[1:]) - 1:
                # 最后一行 - 无尾部空格
                markdown_table.append(" |" + "|".join(row_cells) + "|")
            else:
                # 非最后一行 - 保持一致的格式
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
                # 图像路径不存在，保持原始图像路径
                updated_images.append(image)
        
        return updated_images
    
    def _process_page_elements(self, page_elements, original_blocks_by_page, page_num, full_text):
        """处理页面元素，按顺序添加到Markdown文档
        
        Args:
            page_elements (list): 页面元素列表
            original_blocks_by_page: 按页码组织的原始文本块
            page_num: 当前页码
            full_text: 完整文本列表，用于存储生成的Markdown内容
        """
        logger.info(f"开始处理页面元素，元素数量: {len(page_elements)}")
        
        # 跟踪已处理的文本块索引
        processed_blocks = set()
        
        # 获取当前页面的原始文本块（已排序）
        original_blocks = original_blocks_by_page.get(page_num, [])
        
        # 分离文本块和图表元素
        text_elements = []
        chart_elements = []
        
        for element in page_elements:
            if element['type'] == 'text':
                text_elements.append(element)
            else:
                chart_elements.append(element)
        
        # 处理图表元素，确定它们的插入位置
        chart_insertions = []
        for chart in chart_elements:
            if chart['type'] == 'image' or chart['type'] == 'table':
                # 记录表格处理信息
                if chart['type'] == 'table':
                    table = chart['content']
                    logger.info(f"处理表格: 页码={table.page_num}, 表格索引={table.table_idx}, bbox={table.bbox}")
                
                # 查找图表/表格在原始文本块中的位置
                before_block, after_block = None, None
                if hasattr(chart['content'], 'bbox'):
                    # 如果有bbox属性，使用与图像相同的位置查找逻辑
                    logger.info(f"处理{chart['type']}的位置计算: bbox={chart['content'].bbox if hasattr(chart['content'], 'bbox') else 'N/A'}")
                    before_block, after_block = self._find_chart_position(chart['content'], original_blocks)
                
                # 查找包含图表/表格前后原始块的合并块
                merged_blocks = [e['content'] for e in text_elements]
                logger.info(f"查找合并块: before_block={before_block.block_no if before_block else None}, after_block={after_block.block_no if after_block else None}")
                merged_block, position = self._find_merged_block(before_block, after_block, merged_blocks)
                
                if merged_block:
                    logger.info(f"找到合并块: 内容='{merged_block.block_text[:50]}...', 位置={position}")
                    chart_insertions.append((merged_block, position, chart))
                else:
                    # 如果没有找到合适的合并块，直接添加图表/表格
                    logger.info(f"未找到合并块，将{chart['type']}添加到文档末尾")
                    chart_insertions.append((None, 'end', chart))
        
        # 处理文本块和图表
        for element in text_elements:
            block = element['content']
            block_idx = element['block_idx']
            
            if block_idx not in processed_blocks:
                # 检查是否有图表需要插入到当前块之前
                for merged_block, position, chart in chart_insertions:
                    if merged_block == block and position == 'before':
                        # 插入图表到当前块之前
                        if chart['type'] == 'image':
                            logger.info(f"  在文本块之前插入图像: {chart['content'].image_path}")
                            self._add_image_to_markdown(chart['content'], full_text)
                        elif chart['type'] == 'table':
                            table = chart['content']
                            logger.info(f"  在文本块之前插入表格: 页码={table.page_num}, 表格索引={table.table_idx}")
                            logger.info(f"  插入位置: 文本块内容='{block.block_text[:50]}...'")
                            self._add_table_to_markdown(table, full_text)
                
                # 添加文本块
                logger.info(f"  添加文本块 {block_idx+1}: 内容='{block.block_text[:50]}...'")
                # 检查是否包含目标文本
                if "表1：认证流程中不同参与方类别的非完整示例" in block.block_text:
                    logger.info(f"  发现目标文本: '表1：认证流程中不同参与方类别的非完整示例'")
                full_text.append(block.block_text)
                full_text.append("")
                processed_blocks.add(block_idx)
                logger.info(f"  文本块 {block_idx+1} 处理完成")
                
                # 检查是否有图表需要插入到当前块之后
                for merged_block, position, chart in chart_insertions:
                    if merged_block == block and position == 'after':
                        # 插入图表到当前块之后
                        if chart['type'] == 'image':
                            logger.info(f"  在文本块之后插入图像: {chart['content'].image_path}")
                            self._add_image_to_markdown(chart['content'], full_text)
                        elif chart['type'] == 'table':
                            table = chart['content']
                            logger.info(f"  在文本块之后插入表格: 页码={table.page_num}, 表格索引={table.table_idx}")
                            logger.info(f"  插入位置: 文本块内容='{block.block_text[:50]}...'")
                            self._add_table_to_markdown(table, full_text)
        
        # 处理需要添加到文档末尾的图表
        for merged_block, position, chart in chart_insertions:
            if position == 'end':
                if chart['type'] == 'image':
                    logger.info(f"  在文档末尾插入图像: {chart['content'].image_path}")
                    self._add_image_to_markdown(chart['content'], full_text)
                elif chart['type'] == 'table':
                    table = chart['content']
                    logger.info(f"  在文档末尾插入表格: 页码={table.page_num}, 表格索引={table.table_idx}, bbox={table.bbox}")
                    self._add_table_to_markdown(table, full_text)
        
        logger.info(f"页面元素处理完成，已处理 {len(processed_blocks)} 个文本块")
    
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
    
    def _find_chart_position(self, image, original_blocks):
        """查找图表在原始文本块中的位置
        
        Args:
            image: 图像对象
            original_blocks: 原始文本块列表（已排序）
            
        Returns:
            tuple: (before_block, after_block) - 图表前后的原始块
        """
        chart_y = image.bbox[1]
        
        # 在已排序的原始文本块中查找图表前后的块
        # 由于原始文本块已经按垂直位置排序，可以使用线性查找
        before_block = None
        after_block = None
        
        for i, block in enumerate(original_blocks):
            block_y = block.block_bbox[1]
            if block_y <= chart_y:
                before_block = block
            else:
                after_block = block
                break
        
        logger.info(f"图表位置查找完成: before_block={before_block.block_no if before_block else None}, after_block={after_block.block_no if after_block else None}")
        return before_block, after_block
    
    def _find_merged_block(self, before_block, after_block, merged_blocks):
        """查找包含图表前后原始块的合并块
        
        Args:
            before_block: 图表前的原始块
            after_block: 图表后的原始块
            merged_blocks: 合并块列表
            
        Returns:
            tuple: (merged_block, position) - 包含图表的合并块和位置关系
        """
        for block in merged_blocks:
            original_blocks = block.original_blocks
            original_block_nos = [b.block_no for b in original_blocks]
            
            # 检查是否包含目标文本
            if "表1：认证流程中不同参与方类别的非完整示例" in block.block_text:
                logger.info(f"发现包含目标文本的合并块: '{block.block_text[:50]}...'")
                logger.info(f"  合并块包含原始块编号: {original_block_nos}")
                logger.info(f"  与before_block({before_block.block_no if before_block else None})和after_block({after_block.block_no if after_block else None})的关系")
            
            # 检查before_block是否在当前合并块中（使用块编号）
            if before_block and before_block.block_no in original_block_nos:
                logger.info(f"找到包含before_block的合并块: {block.block_text[:50]}...")
                return block, 'after'  # 图表在before_block之后
            
            # 检查after_block是否在当前合并块中（使用块编号）
            if after_block and after_block.block_no in original_block_nos:
                logger.info(f"找到包含after_block的合并块: {block.block_text[:50]}...")
                return block, 'before'  # 图表在after_block之前
        
        logger.info("未找到包含图表前后原始块的合并块")
        return None, None
    
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
            
            # 复制图像到输出目录并更新路径为相对路径
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
                    page_num = table.page_num
                    if page_num not in tables_by_page:
                        tables_by_page[page_num] = []
                    tables_by_page[page_num].append(table)
            
            # 按页码组织原始文本块
            original_blocks_by_page = {}
            if 'blocks' in translated_content:
                for page in translated_content['blocks']:
                    page_num = page.page_num
                    if page_num not in original_blocks_by_page:
                        original_blocks_by_page[page_num] = []
                    # 原始文本块已经按垂直位置排序
                    original_blocks_by_page[page_num] = page.text_blocks
            
            # 获取所有页码的列表并排序
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
                    page_elements.append({
                        'type': 'text',
                        'content': block,
                        'block_idx': block_idx
                    })
                
                # 添加图像元素
                page_images = images_by_page.get(page_num, [])
                for image_idx, image in enumerate(page_images):
                    page_elements.append({
                        'type': 'image',
                        'content': image
                    })
                
                # 添加表格元素
                page_tables = tables_by_page.get(page_num, [])
                for table_idx, table in enumerate(page_tables):
                    page_elements.append({
                        'type': 'table',
                        'content': table
                    })
                
                # 处理元素，按顺序添加到Markdown文档
                self._process_page_elements(page_elements, original_blocks_by_page, page_num, full_text)
            
            # 合并文本
            combined_text = "\n".join(full_text)
            
            # 记录处理前的文本内容，特别是图像URL
            logger.info(f"布局模型处理前的文本包含图像URL: {'![](images_' in combined_text}")
            # 记录前1000个字符，包含图像URL的部分
            if '![](images_' in combined_text:
                start_idx = combined_text.find('![](images_')
                logger.info(f"处理前的图像URL示例: {combined_text[start_idx:start_idx+100]}")
            
            # 使用布局模型格式化文本为Markdown
            formatted_text = self._format_with_layout_model(combined_text)
            
            # 记录处理后的文本内容，特别是图像URL
            logger.info(f"布局模型处理后的文本包含图像URL: {'![](images_' in formatted_text}")
            # 记录前1000个字符，检查图像URL是否保留
            if '![](images_' in formatted_text:
                start_idx = formatted_text.find('![](images_')
                logger.info(f"处理后的图像URL示例: {formatted_text[start_idx:start_idx+100]}")
            else:
                logger.warning("布局模型处理后丢失了图像URL元素")
            
            # 保存Markdown文件
            with open(output_md_path, 'w', encoding='utf-8') as f:
                f.write(formatted_text)
            
            logger.info(f"Markdown文档生成完成，输出文件: {output_md_path}")
            
        except Exception as e:
            logger.error(f"生成Markdown文档时出错: {str(e)}", exc_info=True)
            raise Exception(f"生成Markdown文档时出错: {str(e)}")


def create_markdown_generator(api_type, api_key, api_url, model):
    """创建Markdown生成器实例
    
    根据API类型返回相应的Markdown生成器实例
    
    Args:
        api_type (str): API类型，如'aiping'或'silicon_flow'
        api_key (str): API密钥
        api_url (str): API请求地址
        model (str): 布局模型名称
    
    Returns:
        MarkdownGenerator: 相应的Markdown生成器实例
    
    Raises:
        ValueError: 当API类型无效时
    """
    if api_type == 'aiping':
        logger.info("创建AipingMarkdownGenerator实例")
        return AipingMarkdownGenerator(api_key, api_url, model)
    elif api_type == 'silicon_flow':
        logger.info("创建基础MarkdownGenerator实例")
        return MarkdownGenerator(api_key, api_url, model)
    else:
        error_msg = f"无效的API类型: {api_type}。支持的类型: 'aiping', 'silicon_flow'"
        logger.error(error_msg)
        raise ValueError(error_msg)
