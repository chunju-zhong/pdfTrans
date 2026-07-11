from openai import OpenAI
from .translator import Translator
from models.result_types import TranslationResult, TruncationInfo
from config import config
from modules.llm_error_handler import classify_llm_error


class QianfanTranslator(Translator):
    """百度千帆翻译API实现
    
    继承自Translator基类，实现百度千帆翻译API的调用逻辑。
    百度千帆平台提供OpenAI兼容API，支持ERNIE系列及开源模型。
    """
    
    def __init__(self, api_key, api_url, model):
        """初始化百度千帆翻译器
        
        Args:
            api_key (str): 百度千帆API的密钥
            api_url (str): 百度千帆API的请求地址
            model (str): 要使用的模型名称
        """
        super().__init__(api_key, api_url)
        self.model = model
        self.max_tokens = config.TRANSLATION_MAX_TOKENS
        # 初始化OpenAI客户端
        self.client = OpenAI(
            base_url=self.api_url,
            api_key=self.api_key,
            timeout=config.TRANSLATION_TIMEOUT,
            max_retries=0,  # 禁用SDK内置重试，避免请求超时后静默重试拖延整体流程
        )
    
    def translate(self, text, source_lang, target_lang, doc_type, glossary):
        """使用百度千帆翻译API翻译文本
        
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
        
        # 构建优化的系统提示词
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
        
        
        try:
            # 调用百度千帆API - 使用OpenAI兼容格式，流式调用以避免长请求整体超时
            response = self.client.chat.completions.create(
                model=self.model,
                stream=True,  # 流式调用，避免长请求整体超时
                temperature=config.TRANSLATION_TEMPERATURE,
                top_p=config.TRANSLATION_TOP_P,
                max_tokens=self._calculate_max_tokens(text),
                extra_body=config.QIANFAN_EXTRA_BODY,  # 补传 extra_body（含 enable_thinking 等配置）
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

            # 处理响应 - 累积流式 chunk
            translated_text_raw = ""
            reasoning_content_raw = ""
            token_usage = {}
            finish_reason = ""

            for chunk in response:
                if hasattr(chunk, "choices") and len(chunk.choices) > 0:
                    choice = chunk.choices[0]
                    delta = choice.delta if hasattr(choice, "delta") else None
                    if delta is not None:
                        # 累积主翻译内容
                        if hasattr(delta, "content") and delta.content:
                            translated_text_raw += delta.content
                        # 累积 reasoning_content（用于 fallback）
                        if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                            reasoning_content_raw += delta.reasoning_content
                    # 读取 finish_reason（通常出现在最后一个 chunk）
                    if hasattr(choice, "finish_reason") and choice.finish_reason:
                        finish_reason = choice.finish_reason
                # 读取 token usage（通常出现在最后一个 chunk）
                if hasattr(chunk, "usage") and chunk.usage:
                    token_usage = {
                        "prompt_tokens": getattr(chunk.usage, "prompt_tokens", 0),
                        "completion_tokens": getattr(chunk.usage, "completion_tokens", 0),
                        "total_tokens": getattr(chunk.usage, "total_tokens", 0)
                    }

            translated_text = translated_text_raw.strip()
            reasoning_content = reasoning_content_raw.strip()

            # reasoning_content 非空时记录 INFO 诊断日志（用于监控思考模式是否真正关闭）
            if reasoning_content:
                import logging
                _diag_logger = logging.getLogger(__name__)
                _diag_logger.info(
                    f"百度千帆翻译残留 reasoning_content: 长度={len(reasoning_content)}, "
                    f"finish_reason={finish_reason}, 原文前100字符='{text[:100]}'"
                )

            # 翻译结果为空时记录诊断日志并尝试从 reasoning_content fallback
            if not translated_text:
                import logging
                _diag_logger = logging.getLogger(__name__)
                _diag_logger.warning(
                    f"百度千帆翻译结果为空: reasoning_content长度={len(reasoning_content)}, "
                    f"finish_reason={finish_reason}, 原文前100字符='{text[:100]}'"
                )
                if reasoning_content:
                    translated_text = reasoning_content
            
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
            error_info = classify_llm_error(e)
            raise Exception(f"百度千帆翻译API请求失败: {error_info['user_message']}") from e

    def _get_format_api_kwargs(self):
        """百度千帆API调用额外参数"""
        return {"extra_body": config.QIANFAN_EXTRA_BODY}



