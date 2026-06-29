from .semantic_analyzer import SemanticAnalyzer
from config import config
from modules.llm_error_handler import classify_llm_error

class AipingSemanticAnalyzer(SemanticAnalyzer):
    """aiping语义分析器实现
    
    继承自SemanticAnalyzer基类，实现aiping语义分析API的调用逻辑，包含费用优先参数。
    """
    
    def __init__(self, api_key, api_url, model):
        """初始化aiping语义分析器
        
        Args:
            api_key (str): aiping语义分析API的密钥
            api_url (str): aiping语义分析API的请求地址
            model (str): 要使用的模型名称
        """
        super().__init__(api_key, api_url, model)
        # 初始化OpenAI客户端，添加超时设置
        from openai import OpenAI
        self.client = OpenAI(
            base_url=self.api_url,
            api_key=self.api_key,
            timeout=config.SEMANTIC_ANALYSIS_TIMEOUT,
        )
        # 设置max_tokens属性（使用config的常量）
        self.max_tokens = config.SEMANTIC_ANALYSIS_SINGLE_MAX_TOKENS
        # 设置batch_max_tokens属性
        self.batch_max_tokens = config.SEMANTIC_ANALYSIS_BATCH_MAX_TOKENS
    
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
        import time

        logger = logging.getLogger(__name__)

        # 准备语义分析的提示词
        analysis_prompt = self._generate_semantic_analysis_prompt(text1, text2, source_lang)
        logger.info(f"生成语义分析提示词: 块1='{text1}', 块2='{text2}', 提示词长度={len(analysis_prompt)}")

        max_retries = 3  # 最大重试次数
        retry_delay = 0.5  # 重试间隔（秒）

        for attempt in range(max_retries):
            try:
                # 调用AI Ping API - 使用OpenAI Chat API格式，包含费用优先参数
                response = self.client.chat.completions.create(
                    model=self.model,
                    stream=True,  # 保持流式调用
                    temperature=config.SEMANTIC_ANALYSIS_TEMPERATURE,
                    top_p=config.SEMANTIC_ANALYSIS_TOP_P,
                    max_tokens=self.max_tokens,  # 使用类属性作为最大token数
                    extra_body=config.AIPING_EXTRA_BODY,
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

                # 处理响应 - stream=True时直接处理流式响应
                analysis_result = ""
                reasoning_content_accumulated = ""
                finish_reason = ""
                for chunk in response:
                    if hasattr(chunk, "choices") and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, "content") and delta.content:
                            analysis_result += delta.content
                        elif hasattr(delta, "reasoning_content") and delta.reasoning_content:
                            # 累积思考内容（用于诊断和 fallback）
                            reasoning_content_accumulated += delta.reasoning_content

                    # 捕获 finish_reason（用于诊断）
                    if hasattr(chunk, "choices") and len(chunk.choices) > 0:
                        choice = chunk.choices[0]
                        if hasattr(choice, "finish_reason") and choice.finish_reason:
                            finish_reason = choice.finish_reason

                # content 为空时记录诊断日志并尝试从 reasoning_content 提取 JSON
                if not analysis_result:
                    logger.warning(
                        f"语义分析结果 content 为空: reasoning_content长度={len(reasoning_content_accumulated)}, "
                        f"finish_reason={finish_reason}, 块1前100字符='{text1[:100]}', 块2前100字符='{text2[:100]}'"
                    )
                    if reasoning_content_accumulated:
                        analysis_result = reasoning_content_accumulated

                logger.info(f"LLM返回的原始分析结果: '{analysis_result}'")

                # 解析LLM的分析结果
                analysis_json = self._extract_json_from_response(analysis_result)
                if analysis_json is None:
                    raise json.JSONDecodeError("无法从响应中提取JSON", analysis_result, 0)
                logger.info(f"解析后的JSON结果: {analysis_json}")

                should_merge = analysis_json.get("merge", False)
                logger.info(f"最终合并决策: {should_merge}，块1='{text1}', 块2='{text2}'")
                return bool(should_merge)

            except Exception as e:
                error_info = classify_llm_error(e)
                if attempt < max_retries - 1:
                    # 不是最后一次尝试，记录错误并重试
                    logger.error(f"aiping语义分析API请求失败 (尝试 {attempt + 1}/{max_retries}): {error_info['user_message']}，将在 {retry_delay} 秒后重试...")
                    logger.error(f"失败时的文本块: 块1='{text1}', 块2='{text2}'")
                    time.sleep(retry_delay)
                else:
                    # 最后一次尝试失败，返回默认值
                    logger.error(f"aiping语义分析API请求最终失败: {error_info['user_message']}，返回默认值False")
                    logger.error(f"失败时的文本块: 块1='{text1}', 块2='{text2}'")
                    return False
    
    def batch_analyze_semantic_relationship(self, blocks, source_lang):
        """批量分析顺序文本块之间的语义关系，判断相邻块是否应该合并

        Args:
            blocks (list[str]): 顺序文本块列表
            source_lang (str): 源语言代码

        Returns:
            list: 布尔值列表，长度为 len(blocks)-1，表示每对相邻块是否应该合并
        """
        import json
        import logging
        import time

        logger = logging.getLogger(__name__)

        # 少于2个块时无需分析
        if len(blocks) <= 1:
            logger.info(f"文本块数量={len(blocks)}，不足2个，无需分析")
            return []

        expected_merge_count = len(blocks) - 1

        # 记录输入文本块的详细信息
        logger.info(f"开始批量语义分析: 文本块数量={len(blocks)}, 源语言={source_lang}, 预期合并决策数={expected_merge_count}")
        for i, block in enumerate(blocks):
            logger.debug(f"块 {i+1}: '{block[:100]}...' (长度={len(block)})")

        # 准备批量语义分析的提示词
        analysis_prompt = self._generate_batch_semantic_analysis_prompt(blocks, source_lang)
        logger.info(f"生成批量语义分析提示词: 文本块数量={len(blocks)}, 提示词长度={len(analysis_prompt)}")

        max_retries = 3  # 最大重试次数
        retry_delay = 0.5  # 重试间隔（秒）

        for attempt in range(max_retries):
            try:
                logger.info(f"执行API调用 (尝试 {attempt + 1}/{max_retries})")
                # 调用AI Ping API - 使用OpenAI Chat API格式，包含费用优先参数
                response = self.client.chat.completions.create(
                    model=self.model,
                    stream=True,  # 保持流式调用
                    temperature=config.SEMANTIC_ANALYSIS_TEMPERATURE,
                    top_p=config.SEMANTIC_ANALYSIS_TOP_P,
                    max_tokens=self.batch_max_tokens,  # 使用类属性作为最大token数
                    extra_body=config.AIPING_EXTRA_BODY,
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

                # 处理响应 - stream=True时直接处理流式响应
                analysis_result = ""
                reasoning_content_accumulated = ""
                finish_reason = ""
                chunk_count = 0
                logger.info("开始处理流式响应")
                for chunk in response:
                    chunk_count += 1
                    if hasattr(chunk, "choices") and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, "content") and delta.content:
                            analysis_result += delta.content
                            logger.debug(f"处理响应块 {chunk_count}: 添加内容长度={len(delta.content)}")
                        elif hasattr(delta, "reasoning_content") and delta.reasoning_content:
                            # 累积思考内容（用于诊断和 fallback）
                            reasoning_content_accumulated += delta.reasoning_content
                            logger.debug(f"处理响应块 {chunk_count}: 累积思考内容长度={len(reasoning_content_accumulated)}")

                    # 捕获 finish_reason（用于诊断）
                    if hasattr(chunk, "choices") and len(chunk.choices) > 0:
                        choice = chunk.choices[0]
                        if hasattr(choice, "finish_reason") and choice.finish_reason:
                            finish_reason = choice.finish_reason
                logger.info(f"完成处理响应，共处理 {chunk_count} 个块，结果长度={len(analysis_result)}")

                # content 为空时记录诊断日志并尝试从 reasoning_content 提取 JSON
                if not analysis_result:
                    logger.warning(
                        f"批量语义分析结果 content 为空: reasoning_content长度={len(reasoning_content_accumulated)}, "
                        f"finish_reason={finish_reason}, 文本块数量={len(blocks)}, 块1前100字符='{blocks[0][:100] if blocks else ''}'"
                    )
                    if reasoning_content_accumulated:
                        analysis_result = reasoning_content_accumulated

                logger.info(f"LLM返回的原始批量分析结果: '{analysis_result}'")

                # 解析LLM的分析结果
                analysis_json = self._extract_json_from_response(analysis_result)
                if analysis_json is None:
                    raise json.JSONDecodeError("无法从响应中提取JSON", analysis_result, 0)
                logger.info(f"解析后的JSON结果: {analysis_json}")

                merge_results = analysis_json.get("merge", [])
                logger.info(f"最终批量合并决策: {merge_results}")
                
                # 确保返回结果数量与预期一致（len(blocks) - 1）
                if len(merge_results) != expected_merge_count:
                    logger.error(f"批量分析结果数量与预期不一致: 期望{expected_merge_count}个结果，实际{len(merge_results)}个结果")
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
                        while len(final_results) < expected_merge_count:
                            final_results.append(False)
                        # 截断多余的项（如果有的话）
                        final_results = final_results[:expected_merge_count]
                        logger.info(f"补足后结果: {final_results}")
                        return final_results
                
                # 详细记录每个相邻块对的分析结果
                final_results = [bool(result) for result in merge_results]
                
                logger.info(f"批量语义分析完成: 共分析 {len(blocks)} 个文本块，{expected_merge_count} 个相邻对，合并 {sum(final_results)} 个")
                return final_results

            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {str(e)}")
                logger.error(f"无法解析的原始结果: '{analysis_result}'")
                if attempt < max_retries - 1:
                    logger.error(f"将在 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                else:
                    logger.error("最终失败，返回默认值列表")
                    return [False] * expected_merge_count
            except Exception as e:
                error_info = classify_llm_error(e)
                if attempt < max_retries - 1:
                    # 不是最后一次尝试，记录错误并重试
                    logger.error(f"aiping批量语义分析API请求失败 (尝试 {attempt + 1}/{max_retries}): {error_info['user_message']}，将在 {retry_delay} 秒后重试...")
                    logger.error(f"失败时的文本块数量: {len(blocks)}")
                    time.sleep(retry_delay)
                else:
                    # 最后一次尝试失败，返回默认值列表
                    logger.error(f"aiping批量语义分析API请求最终失败: {error_info['user_message']}，返回默认值列表")
                    logger.error(f"失败时的文本块数量: {len(blocks)}")
                    return [False] * expected_merge_count
