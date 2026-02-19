class Translator:
    """翻译基类
    
    定义翻译API的统一接口，具体翻译服务需要继承此类并实现translate方法。
    """
    
    def __init__(self, api_key, api_url=None):
        """初始化翻译器
        
        Args:
            api_key (str): API密钥
            api_url (str, optional): API请求地址
        """
        self.api_key = api_key
        self.api_url = api_url
        self.supported_languages = {
            'zh': '中文',
            'en': '英语',
            'ja': '日语',
            'ko': '韩语',
            'fr': '法语',
            'de': '德语',
            'es': '西班牙语',
            'ru': '俄语'
        }
    
    def translate(self, text, source_lang, target_lang, doc_type, glossary):
        """翻译文本
        
        Args:
            text (str): 要翻译的文本
            source_lang (str): 源语言代码
            target_lang (str): 目标语言代码
            doc_type (str): 文档类型
            glossary (str): 术语表，格式为"术语1: 翻译1\n术语2: 翻译2"
            
        Returns:
            str: 翻译后的文本
        """
        # 检查原语言与目标语言是否一致
        if source_lang == target_lang:
            # 语言一致，直接返回原文本
            return text
    
        # 语言不一致，调用具体翻译实现
        raise NotImplementedError("子类必须实现translate方法")
    
    def _postprocess_text(self, text, original_text=""):
        """文本后处理
        
        Args:
            text (str): 要处理的文本
            original_text (str): 原始文本，用于当翻译结果无效时作为fallback
            
        Returns:
            str: 后处理后的文本
        """
        import re
        
        processed_text = text.strip()
        
        # 移除多余的空格和换行
        processed_text = ' '.join(processed_text.split())
        
        # 如果翻译结果为空或只有占位符（如'...'），返回原始文本
        if not processed_text or processed_text == '...':
            return original_text
        
        return processed_text
    
    def batch_translate(self, texts, source_lang, target_lang, doc_type="AI技术", glossary=""):
        """批量翻译文本
        
        Args:
            texts (list): 要翻译的文本列表
            source_lang (str): 源语言代码
            target_lang (str): 目标语言代码
            doc_type (str): 文档类型
            glossary (str): 术语表，格式为"术语1: 翻译1\n术语2: 翻译2"
            
        Returns:
            list: 翻译后的文本列表
        """
        # 检查原语言与目标语言是否一致
        if source_lang == target_lang:
            # 语言一致，直接返回原文本列表
            return texts.copy()
        
        results = []
        for text in texts:
            translated_text = self.translate(text, source_lang, target_lang, doc_type, glossary)
            results.append(translated_text)
        return results
    
    def _validate_language(self, lang_code):
        """验证语言代码是否支持
        
        Args:
            lang_code (str): 语言代码
            
        Returns:
            bool: 如果支持返回True，否则返回False
        """
        return lang_code in self.supported_languages
    
    def _preprocess_text(self, text):
        """文本预处理
        
        Args:
            text (str): 要处理的文本
            
        Returns:
            str: 预处理后的文本
        """
        # 移除多余的空格和换行
        return ' '.join(text.split())
    
    def _generate_system_prompt(self, doc_type, source_lang_name, target_lang_name, glossary):
        """生成系统提示词
        
        Args:
            doc_type (str): 文档类型
            source_lang_name (str): 源语言名称
            target_lang_name (str): 目标语言名称
            glossary (str): 术语表
            
        Returns:
            str: 生成的系统提示词
        """
        return f"""
你是专业的{doc_type}翻译专家，擅长将{source_lang_name}的{doc_type}文档转写成{target_lang_name}，严格遵循以下规则：
1. 语义连贯：必须基于完整上下文理解，句式适配{target_lang_name}表达习惯，表达流畅，转折自然；
2. 增加必要的过渡：在保持原文逻辑的基础上，适当增加过渡词，转换句，增强阅读体验；
3. 风格一致：符合原文风格，保持原文档的语气；
4. 书写习惯：句子和段落有长有短，更符合人类书写习惯及说话方式；
5. 术语一致：严格使用以下术语表翻译，不随意变更：
{glossary if glossary else '无'}
6. 不增删义：严格遵循原文含义，不添加额外解释，不遗漏任何细节（包括标点、括号、冒号的位置）；
7. 语法正确：符合{target_lang_name}语法规则，避免语法错误，避免缺少句子成分；
8. 格式兼容：翻译结果需便于后续按原文本块拆分，不擅自添加换行、分段（保持段落级完整性）；
9. 技术精准：对于{doc_type}术语、代码片段、公式等，保持高度准确性，避免误译。
10. 不要翻译URL：原文中包含的URL地址，保持原状，不进行翻译。
11. 不要翻译代码段：原文中包含的代码段（包括但不限于代码块、行内代码），保持原状，不进行翻译。
"""
    
    def _generate_user_prompt(self, source_lang_name, target_lang_name, doc_type, processed_text):
        """生成用户提示词

        Args:
            source_lang_name (str): 源语言名称
            target_lang_name (str): 目标语言名称
            doc_type (str): 文档类型
            processed_text (str): 预处理后的文本

        Returns:
            str: 生成的用户提示词
        """
        return f"请将以下{source_lang_name}的{doc_type}文本转写成{target_lang_name}，严格遵守上述所有规则：\n\n{processed_text}"

    def _generate_semantic_analysis_prompt(self, text1, text2, source_lang):
        """生成语义分析提示词

        Args:
            text1 (str): 第一个文本块
            text2 (str): 第二个文本块
            source_lang (str): 源语言代码

        Returns:
            str: 生成的语义分析提示词
        """
        # 获取语言名称
        lang_name = self.supported_languages.get(source_lang, source_lang)
        
        return f"""
        你是专业的文本语义分析专家，负责分析相邻文本块之间的语义关系。
        
        请分析以下两个{lang_name}相邻文本块是否应该合并为一个语义单元：
        
        块1: "{text1}"
        块2: "{text2}"
        
        # 分析标准：
        1. 语义连贯性：两个块是否表达同一个完整的语义单元
        2. 语法完整性：前一个块是否是不完整的句子，后一个块是否是其延续
        3. 逻辑关系：两个块之间是否存在紧密的逻辑联系
        4. 标题识别：如果任一文本块是标题（大小标题），则不应合并
        
        # 标题识别规则：
        - 标题通常具有简洁性、概括性和引导性
        - 标题通常是短语或简短句子，不包含详细内容
        - 标题通常用于引入或概括后续内容
        - 标题示例："1. 引言"、"2.1 方法概述"、"结论"、"背景介绍"
        - 非标题示例："这是一个详细的段落内容，包含具体的信息和解释。"
        
        # 重要判断规则：
        - 如果块1是标题，块2不是标题，返回merge: false
        - 如果块2是标题，块1不是标题，返回merge: false
        - 如果两个块都是标题，返回merge: false
        - 只有当两个块都不是标题且满足其他合并条件时，才返回merge: true
        
        请根据{lang_name}的语法和语义规则进行分析，给出明确的判断。
        
        # 重要输出要求：
        1. 只返回纯JSON字符串，不包含任何其他文本
        2. 不要包含Markdown代码块标记（如 ```json 或 ```）
        3. 确保返回的内容可以直接被JSON解析器解析
        4. 只输出一行JSON，不要有多余的空白行
        5. 只包含merge字段，值为true或false
        
        正确输出示例：
        {{"merge": true}}
        
        错误输出示例：
        ```json
        {{"merge": true}}
        ```
        
        请严格按照要求输出，仅返回：
        {{"merge": true/false}}
        """

    def analyze_semantic_relationship(self, text1, text2, source_lang):
        """分析两个文本块之间的语义关系，判断是否应该合并

        Args:
            text1 (str): 第一个文本块
            text2 (str): 第二个文本块
            source_lang (str): 源语言代码

        Returns:
            bool: 是否应该合并
        """

        # 子类必须实现此方法
        raise NotImplementedError("子类必须实现analyze_semantic_relationship方法")
    
    def batch_analyze_semantic_relationship(self, text_pairs, source_lang):
        """批量分析多个文本块对之间的语义关系，判断是否应该合并

        Args:
            text_pairs (list): 文本块对列表，每个元素是包含两个文本的元组
            source_lang (str): 源语言代码

        Returns:
            list: 布尔值列表，表示每个文本块对是否应该合并
        """

        # 子类必须实现此方法
        raise NotImplementedError("子类必须实现batch_analyze_semantic_relationship方法")
    
    def _generate_batch_semantic_analysis_prompt(self, text_pairs, source_lang):
        """生成批量语义分析提示词

        Args:
            text_pairs (list): 文本块对列表，每个元素是包含两个文本的元组
            source_lang (str): 源语言代码

        Returns:
            str: 生成的批量语义分析提示词
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 记录输入信息
        logger.info(f"开始生成批量语义分析提示词: 文本对数量={len(text_pairs)}, 源语言={source_lang}")
        for i, (text1, text2) in enumerate(text_pairs):
            logger.debug(f"文本对 {i+1}: 块1长度={len(text1)}, 块2长度={len(text2)}")
            logger.debug(f"文本对 {i+1}: 块1='{text1[:100]}...'" if len(text1) > 100 else f"文本对 {i+1}: 块1='{text1}'")
            logger.debug(f"文本对 {i+1}: 块2='{text2[:100]}...'" if len(text2) > 100 else f"文本对 {i+1}: 块2='{text2}'")
        
        # 获取语言名称
        lang_name = self.supported_languages.get(source_lang, source_lang)
        
        prompt = f"""
        你是专业的文本语义分析专家，负责分析相邻文本块之间的语义关系。
        请分析以下多对{lang_name}的相邻文本块，分别判断文本块是否应该合并为一个语义单元。
        """        
        # 添加文本块对
        for i, (text1, text2) in enumerate(text_pairs):
            prompt += f"\n对{i+1}:\n块1: \"{text1}\"\n块2: \"{text2}\"\n"
        
        prompt += """
        # 分析标准：
        1. 语义连贯性：如果两个块表达同一个完整的语义单元，逻辑上的延续，返回: true
        2. 语法完整性：如果前一个块是不完整的句子，后一个块是其延续，返回: true
        3. 标题识别：如果任一文本块是标题（大小标题），则不应合并，返回: false
        4. 列表项开头：如果前一块不是列表项，后一个块是列表项开头，返回: false
        5. 多列表项：如果前一个是列表项，后一个也是列表项，返回: false
        6. 列表项延续：如果前一个块是列表项，后一个块是其延续，返回: true
        
        # 重要输出要求：
        1. 只返回纯JSON字符串，不包含任何其他文本
        2. 不要包含Markdown代码块标记（如 ```json 或 ```）
        3. 确保返回的内容可以直接被JSON解析器解析
        4. 只输出一行JSON，不要有多余的空白行
        5. 返回一个包含所有分析结果的JSON对象，键为"merge"，值为布尔值数组
        6. **关键要求**：返回的 `merge` 数组长度必须与输入文本对数量完全一致
        7. **严格要求**：每对输入文本必须对应一个分析结果，不得遗漏或重复
        
        # 具体输出长度要求
        - 如果输入 n 对文本，返回的 `merge` 数组必须包含 n 个布尔值
        - `merge` 数组的长度必须等于输入文本对的数量
        - 例如：输入 3 对文本时，`merge` 数组必须包含 3 个元素
        - 例如：输入 5 对文本时，`merge` 数组必须包含 5 个元素
        
        # 详细示例
        ## 示例 1：输入 3 对文本
        输入：
        对1:
        块1: "Hello"
        块2: "world"
        
        对2:
        块1: "How are"
        块2: "you"
        
        对3:
        块1: "I am"
        块2: "fine"
        
        正确输出：
        {{"merge": [true, true, true]}}
        
        ## 示例 2：输入 5 对文本
        输入：
        对1:
        块1: "a variety"
        块2: "of components:"
        
        对2:
        块1: "such"
        块2: "as"
        
        对3:
        块1: "for example"
        块2: ":"
        
        对4:
        块1: "including"
        块2: "the following"
        
        对5:
        块1: "consisting"
        块2: "of"
        
        正确输出：
        {{"merge": [true, true, true, true, true]}}
        
        ## 示例 3：列表项延续示例
        输入：
        对1:
        块1: "• Context to guide reasoning defines the agent's fundamental reasoning patterns and"
        块2: "available actions, dictating its behavior:"
        
        对2:
        块1: "available actions, dictating its behavior:"
        块2: "• System Instructions: High-level directives defining the agent's persona, capabilities,"
        
        正确输出：
        {"merge": [true, false]}
        
        解释：
        - 对1: 块1是列表项，块2是非列表项且是其延续，应该合并（返回true）
        - 对2: 块2是新的列表项，不应该合并（返回false）
        
        # 错误提示
        - 如果返回的结果数量与输入数量不一致，将被视为无效输出
        - 如果返回的 JSON 格式错误，将被视为无效输出
        - 请确保返回的 JSON 格式正确，且 `merge` 数组长度与输入文本对数量一致
        
        请严格按照要求输出，仅返回：
        {{"merge": [true/false, true/false, ...]}}
        """
        
        logger.info(f"批量语义分析提示词生成完成，长度={len(prompt)}")
        return prompt
    