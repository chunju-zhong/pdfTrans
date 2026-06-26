from openai import OpenAI
from .translator import Translator
from models.result_types import TranslationResult, TruncationInfo
from config import config

class AipingTranslator(Translator):
    """aiping翻译API实现
    
    继承自Translator基类，实现aiping翻译API的调用逻辑。
    """
    
    def __init__(self, api_key, api_url, model):
        """初始化aiping翻译器
        
        Args:
            api_key (str): aiping翻译API的密钥
            api_url (str): aiping翻译API的请求地址
            model (str): 要使用的模型名称
        """
        super().__init__(api_key, api_url)
        self.model = model
        # 初始化OpenAI客户端
        self.client = OpenAI(
            base_url=self.api_url,
            api_key=self.api_key,
            timeout=config.TRANSLATION_TIMEOUT,
        )
        # 设置max_tokens属性
        self.max_tokens = config.TRANSLATION_MAX_TOKENS
    
    def translate(self, text, source_lang, target_lang, doc_type, glossary):
        """使用aiping翻译API翻译文本
        
        Args:
            text (str): 要翻译的文本
            source_lang (str): 源语言代码
            target_lang (str): 目标语言代码
            doc_type (str): 文档类型
            glossary (str): 术语表
            
        Returns:
            TranslationResult: 包含翻译结果和截断信息的结果对象
        """
        # 检查原语言与目标语言是否一致
        if source_lang == target_lang:
            # 语言一致，直接返回原文本
            return TranslationResult(
                content=self._postprocess_text(text, text),
                token_usage={},
                finish_reason="",
                truncation_info=TruncationInfo(truncated=False, token_usage={}, finish_reason="")
            )
        
        # 验证语言代码
        if not self._validate_language(source_lang) or not self._validate_language(target_lang):
            raise ValueError(f"不支持的语言代码: {source_lang} 或 {target_lang}")
        
        # 文本预处理
        processed_text = self._preprocess_text(text)
        
        # 构建针对技术文档英翻中的专属提示词
        lang_map = {
            'zh': '中文',
            'en': '英文',
            'ja': '日文',
            'ko': '韩文',
            'fr': '法文',
            'de': '德文',
            'es': '西班牙文',
            'ru': '俄文',
            'bo': '藏文'
        }
        
        source_lang_name = lang_map.get(source_lang, source_lang)
        target_lang_name = lang_map.get(target_lang, target_lang)
        
        # 生成提示词
        system_prompt = self._generate_system_prompt(
            doc_type, source_lang_name, target_lang_name, glossary,
            source_lang_code=source_lang, target_lang_code=target_lang,
        )
        user_prompt = self._generate_user_prompt(source_lang_name, target_lang_name, doc_type, processed_text)
        
        import time
        
        max_retries = 3  # 最大重试次数
        retry_delay = 2  # 重试间隔（秒）
        
        for attempt in range(max_retries):
            try:
                # 调用AI Ping API - 使用OpenAI Chat API格式，搭配Qwen3-32B优化参数
                response = self.client.chat.completions.create(
                    model=self.model,
                    stream=True,  # 保持流式调用，兼容现有测试
                    temperature=config.TRANSLATION_TEMPERATURE,
                    top_p=config.TRANSLATION_TOP_P,
                    max_tokens=self.max_tokens,  # 使用类属性作为最大token数
                    extra_body=config.AIPING_EXTRA_BODY,
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
                
                # 处理响应 - stream=True时直接处理流式响应
                translated_text = ""
                token_usage = {}
                finish_reason = ""
                reasoning_content_length = 0
                
                for chunk in response:
                    if hasattr(chunk, "choices") and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, "content") and delta.content:
                            translated_text += delta.content
                        elif hasattr(delta, "reasoning_content") and delta.reasoning_content:
                            # 统计思考内容长度（用于诊断）
                            reasoning_content_length += len(delta.reasoning_content)
                    
                    # 捕获token使用信息
                    if hasattr(chunk, "usage") and chunk.usage:
                        token_usage = {
                            "prompt_tokens": getattr(chunk.usage, "prompt_tokens", 0),
                            "completion_tokens": getattr(chunk.usage, "completion_tokens", 0),
                            "total_tokens": getattr(chunk.usage, "total_tokens", 0)
                        }
                    
                    # 捕获finish_reason
                    if hasattr(chunk, "choices") and len(chunk.choices) > 0:
                        choice = chunk.choices[0]
                        if hasattr(choice, "finish_reason") and choice.finish_reason:
                            finish_reason = choice.finish_reason
                
                # 翻译结果为空时记录诊断日志
                if not translated_text:
                    import logging
                    _diag_logger = logging.getLogger(__name__)
                    _diag_logger.warning(
                        f"翻译结果为空: reasoning_content长度={reasoning_content_length}, "
                        f"finish_reason={finish_reason}, 原文前100字符='{text[:100]}'"
                    )
                
                # 检查是否被截断
                truncated = finish_reason == "length"
                
                # 创建TruncationInfo实例
                truncation_info = TruncationInfo(
                    truncated=truncated,
                    token_usage=token_usage,
                    finish_reason=finish_reason
                )
                
                # 文本后处理
                processed_translated_text = self._postprocess_text(translated_text, text)
                
                # 返回翻译结果和截断信息
                return TranslationResult(
                    content=processed_translated_text,
                    token_usage=token_usage,
                    finish_reason=finish_reason,
                    truncation_info=truncation_info
                )
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    # 不是最后一次尝试，记录错误并重试
                    print(f"aiping翻译API请求失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}，将在 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                else:
                    # 最后一次尝试失败，抛出异常
                    raise Exception(f"aiping翻译API请求失败: {str(e)}")

    def cleanup_blocks(self, block_pairs, target_lang="zh"):
        """使用LLM清理翻译后的文本块

        对翻译完成且拆分后的文本块做后处理格式清理，
        修复页脚残留、前导点号、错位拼接等问题。

        Args:
            block_pairs: 同一页上的 (原文, 译文) 对列表
            target_lang: 目标语言代码

        Returns:
            list[str]: 清理后的译文文本列表，与输入一一对应
        """
        if not block_pairs:
            return []

        # 构建输入文本：每块显示原文和译文
        blocks_text = ""
        for i, (orig, trans) in enumerate(block_pairs):
            blocks_text += f"--- 块{i+1} ---\n原文: {orig}\n译文: {trans}\n\n"

        system_prompt = """你是一个PDF翻译排版质量检查助手。你的工作是检查并清理翻译后的文本块。

对每个文本块，你都会看到它的英文原文和当前的中文译文。

需要修复的问题类型：
1. **页脚残留**：如果译文是罗马数字+竖线+标题（如"x | 目录"、"目录  |  xi"）→ 清空该块
2. **前导点号**：如果译文以" . . . . ."开头 → 去掉前导点号
3. **纯点号内容**：如果译文只剩点号、空白和数字 → 清空该块
4. **错位拼接**：如果译文中包含不属于原文的片段（如原文不含"319"但译文有"319 13. 设计模式"）→ 移除不属于原文的片段

严格规则：
- 只做修剪和清理，不新增内容，不修改正确的翻译
- 如果一个块因清理变为空，输出空字符串
- 如果不确定，输出译文不变
- 不要输出任何格式标记

输出格式：每个清理后的块单独一行，用 ---块N--- 标记。"""

        user_prompt = f"请清理以下翻译文本块：\n\n{blocks_text}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                stream=False,
                temperature=0.1,
                max_tokens=4096,
                extra_body=config.AIPING_EXTRA_BODY,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )

            result_text = response.choices[0].message.content or ""

            # 解析结果：按 ---块N--- 标记分割
            cleaned = self._parse_cleanup_result(result_text, len(block_pairs))

            if len(cleaned) != len(block_pairs):
                return [pair[1] for pair in block_pairs]

            return cleaned

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"cleanup_blocks API调用失败: {e}")
            return [pair[1] for pair in block_pairs]

    def _parse_cleanup_result(self, result_text, expected_count):
        """解析cleanup_blocks的LLM返回结果

        Args:
            result_text: LLM返回的文本
            expected_count: 期望的块数量

        Returns:
            list[str]: 解析出的清理后文本列表
        """
        import re
        # 按 ---块N--- 标记分割
        pattern = r'---\s*块(\d+)\s*---'
        parts = re.split(pattern, result_text)

        if len(parts) < 3:
            # 没有标记，尝试按行分割
            lines = [l.strip() for l in result_text.strip().split('\n') if l.strip()]
            return lines[:expected_count]

        # 解析编号和内容
        result = {}
        i = 1
        while i < len(parts) - 1:
            idx = int(parts[i])
            content = parts[i + 1].strip()
            result[idx] = content
            i += 2

        # 按编号排序返回
        return [result.get(j + 1, '') for j in range(expected_count)]


