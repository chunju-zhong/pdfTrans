from openai import OpenAI

class SemanticAnalyzer:
    """语义分析基类
    
    定义语义分析API的统一接口，具体语义分析服务需要继承此类并实现相应方法。
    """
    
    def __init__(self, api_key, api_url=None, model=None):
        """初始化语义分析器
        
        Args:
            api_key (str): API密钥
            api_url (str, optional): API请求地址
            model (str, optional): 要使用的模型名称
        """
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        # 初始化OpenAI客户端
        self.client = OpenAI(
            base_url=self.api_url,
            api_key=self.api_key,
        )
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
    
    def analyze_semantic_relationship(self, text1, text2, source_lang):
        """分析两个文本块之间的语义关系，判断是否应该合并

        Args:
            text1 (str): 第一个文本块
            text2 (str): 第二个文本块
            source_lang (str): 源语言代码

        Returns:
            bool: 是否应该合并
        """
        import json
        import logging

        logger = logging.getLogger(__name__)

        # 准备语义分析的提示词
        analysis_prompt = self._generate_semantic_analysis_prompt(text1, text2, source_lang)
        logger.info(f"生成语义分析提示词: 块1='{text1}', 块2='{text2}', 提示词长度={len(analysis_prompt)}")

        try:
            # 调用API - 使用标准OpenAI格式
            response = self.client.chat.completions.create(
                model=self.model,
                stream=False,  # 非流式调用
                temperature=0.1,  # 降低温度，提高分析准确性
                top_p=0.9,  # 核采样参数
                max_tokens=1024,  # 最大token数
                messages=[
                    {
                        "role": "system",
                        "content": "你是专业的文本语义分析专家，负责分析相邻文本块之间的语义关系。"
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ]
            )

            # 处理响应
            analysis_result = ""
            if hasattr(response, "choices") and len(response.choices) > 0:
                analysis_result = response.choices[0].message.content.strip()

            logger.info(f"LLM返回的原始分析结果: '{analysis_result}'")

            # 解析LLM的分析结果
            analysis_json = json.loads(analysis_result)
            logger.info(f"解析后的JSON结果: {analysis_json}")
            
            should_merge = analysis_json.get("merge", False)
            logger.info(f"最终合并决策: {should_merge}，块1='{text1}', 块2='{text2}'")
            return bool(should_merge)

        except Exception as e:
            # 分析失败时，返回默认值
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"语义分析API请求失败: {str(e)}，返回默认值False")
            logger.error(f"失败时的文本块: 块1='{text1}', 块2='{text2}'")
            return False
    
    def batch_analyze_semantic_relationship(self, text_pairs, source_lang):
        """批量分析多个文本块对之间的语义关系，判断是否应该合并

        Args:
            text_pairs (list): 文本块对列表，每个元素是包含两个文本的元组
            source_lang (str): 源语言代码

        Returns:
            list: 布尔值列表，表示每个文本块对是否应该合并
        """
        import json
        import logging
        import time

        logger = logging.getLogger(__name__)

        # 记录输入文本对的详细信息
        logger.info(f"开始批量语义分析: 文本对数量={len(text_pairs)}, 源语言={source_lang}")
        for i, (text1, text2) in enumerate(text_pairs):
            logger.debug(f"文本对 {i+1}: 块1='{text1[:100]}...' (长度={len(text1)}), 块2='{text2[:100]}...' (长度={len(text2)})")

        # 准备批量语义分析的提示词
        analysis_prompt = self._generate_batch_semantic_analysis_prompt(text_pairs, source_lang)
        logger.info(f"生成批量语义分析提示词: 文本对数量={len(text_pairs)}, 提示词长度={len(analysis_prompt)}")

        max_retries = 3  # 最大重试次数
        retry_delay = 0.5  # 重试间隔（秒）

        for attempt in range(max_retries):
            try:
                logger.info(f"执行API调用 (尝试 {attempt + 1}/{max_retries})")
                # 调用API - 使用标准OpenAI格式
                response = self.client.chat.completions.create(
                    model=self.model,
                    stream=False,  # 非流式调用
                    temperature=0.1,  # 降低温度，提高分析准确性
                    top_p=0.9,  # 核采样参数
                    max_tokens=2048,  # 最大token数
                    messages=[
                        {
                            "role": "system",
                            "content": "你是专业的文本语义分析专家，负责分析相邻文本块之间的语义关系。"
                        },
                        {
                            "role": "user",
                            "content": analysis_prompt
                        }
                    ]
                )

                # 处理响应
                analysis_result = ""
                logger.info("开始处理响应")
                if hasattr(response, "choices") and len(response.choices) > 0:
                    analysis_result = response.choices[0].message.content.strip()
                    logger.info(f"获取到响应内容，长度={len(analysis_result)}")
                else:
                    logger.error("响应中没有有效的choices字段")

                logger.info(f"LLM返回的原始批量分析结果: '{analysis_result}'")

                # 解析LLM的分析结果
                analysis_json = json.loads(analysis_result)
                logger.info(f"解析后的JSON结果: {analysis_json}")
                
                merge_results = analysis_json.get("merge", [])
                logger.info(f"最终批量合并决策: {merge_results}")
                
                # 确保返回结果数量与输入文本对数量一致
                if len(merge_results) != len(text_pairs):
                    logger.error(f"批量分析结果数量与输入文本对数量不一致: 期望{len(text_pairs)}个结果，实际{len(merge_results)}个结果")
                    if attempt < max_retries - 1:
                        logger.error(f"结果数量不一致，将在 {retry_delay} 秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        # 最后一次尝试失败，保留已有结果并将缺失的项记为false
                        logger.error("最终失败，保留已有结果并将缺失的项记为false")
                        # 转换为布尔值
                        final_results = [bool(result) for result in merge_results]
                        # 补足缺失的项
                        while len(final_results) < len(text_pairs):
                            final_results.append(False)
                        # 截断多余的项（如果有的话）
                        final_results = final_results[:len(text_pairs)]
                        logger.info(f"补足后结果: {final_results}")
                        return final_results
                
                # 详细记录每个文本对的分析结果
                final_results = [bool(result) for result in merge_results]
                
                logger.info(f"批量语义分析完成: 共分析 {len(text_pairs)} 个文本对，合并 {sum(final_results)} 个")
                return final_results

            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {str(e)}")
                logger.error(f"无法解析的原始结果: '{analysis_result}'")
                if attempt < max_retries - 1:
                    logger.error(f"将在 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                else:
                    logger.error("最终失败，返回默认值列表")
                    return [False] * len(text_pairs)
            except Exception as e:
                if attempt < max_retries - 1:
                    # 不是最后一次尝试，记录错误并重试
                    logger.error(f"批量语义分析API请求失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}，将在 {retry_delay} 秒后重试...")
                    logger.error(f"失败时的文本对数量: {len(text_pairs)}")
                    time.sleep(retry_delay)
                else:
                    # 最后一次尝试失败，返回默认值列表
                    logger.error(f"批量语义分析API请求最终失败: {str(e)}，返回默认值列表")
                    logger.error(f"失败时的文本对数量: {len(text_pairs)}")
                    return [False] * len(text_pairs)
    
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
