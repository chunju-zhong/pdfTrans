from openai import OpenAI
from .translator import Translator

class SiliconFlowTranslator(Translator):
    """硅基流动翻译API实现
    
    继承自Translator基类，实现硅基流动翻译API的调用逻辑。
    """
    
    def __init__(self, api_key, api_url, model):
        """初始化硅基流动翻译器
        
        Args:
            api_key (str): 硅基流动翻译API的密钥
            api_url (str): 硅基流动翻译API的请求地址
            model (str): 要使用的模型名称
        """
        super().__init__(api_key, api_url)
        self.api_url = api_url
        self.model = model
        # 初始化OpenAI客户端
        self.client = OpenAI(
            base_url=self.api_url,
            api_key=self.api_key,
        )
    
    def translate(self, text, source_lang, target_lang, doc_type, glossary):
        """使用硅基流动翻译API翻译文本
        
        Args:
            text (str): 要翻译的文本
            source_lang (str): 源语言代码
            target_lang (str): 目标语言代码
            doc_type (str): 文档类型
            glossary (str): 术语表
            
        Returns:
            str: 翻译后的文本
        """
        # 检查原语言与目标语言是否一致
        if source_lang == target_lang:
            # 语言一致，直接返回原文本
            return text
        
        # 验证语言代码
        if not self._validate_language(source_lang) or not self._validate_language(target_lang):
            raise ValueError(f"不支持的语言代码: {source_lang} 或 {target_lang}")
        
        # 文本预处理
        processed_text = self._preprocess_text(text)
        
        # 构建优化的系统提示词
        lang_map = {
            'zh': '中文',
            'en': '英文',
            'ja': '日文',
            'ko': '韩文',
            'fr': '法文',
            'de': '德文',
            'es': '西班牙文',
            'ru': '俄文'
        }
        
        source_lang_name = lang_map.get(source_lang, source_lang)
        target_lang_name = lang_map.get(target_lang, target_lang)
        
        # 生成提示词
        system_prompt = self._generate_system_prompt(doc_type, source_lang_name, target_lang_name, glossary)
        user_prompt = self._generate_user_prompt(source_lang_name, target_lang_name, doc_type, processed_text)
        
        
        try:
            # 调用硅基流动API - 使用与aiping一致的参数
            response = self.client.chat.completions.create(
                model=self.model,
                stream=False,  # 非流式调用
                temperature=0.1,  # 降低温度，提高翻译准确性
                top_p=0.9,  # 核采样参数
                max_tokens=8192,  # 最大token数
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
            
            # 处理响应 - stream=False时直接处理非流式响应
            translated_text = ""
            if hasattr(response, "choices") and len(response.choices) > 0:
                translated_text = response.choices[0].message.content.strip()
            
            # 文本后处理
            return self._postprocess_text(translated_text, text)
                
        except Exception as e:
            raise Exception(f"硅基流动翻译API请求失败: {str(e)}")

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
            # 调用硅基流动API - 使用与translate一致的参数
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

            # 处理响应 - stream=False时直接处理非流式响应
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
            logger.error(f"silicon_flow语义分析API请求失败: {str(e)}，返回默认值False")
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
        retry_delay = 2  # 重试间隔（秒）

        for attempt in range(max_retries):
            try:
                logger.info(f"执行API调用 (尝试 {attempt + 1}/{max_retries})")
                # 调用硅基流动API - 使用与translate一致的参数
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

                # 处理响应 - stream=False时直接处理非流式响应
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
                    # 返回默认值列表
                    default_results = [False] * len(text_pairs)
                    logger.info(f"返回默认结果: {default_results}")
                    return default_results
                
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
                    logger.error(f"silicon_flow批量语义分析API请求失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}，将在 {retry_delay} 秒后重试...")
                    logger.error(f"失败时的文本对数量: {len(text_pairs)}")
                    time.sleep(retry_delay)
                else:
                    # 最后一次尝试失败，返回默认值列表
                    logger.error(f"silicon_flow批量语义分析API请求最终失败: {str(e)}，返回默认值列表")
                    logger.error(f"失败时的文本对数量: {len(text_pairs)}")
                    return [False] * len(text_pairs)
