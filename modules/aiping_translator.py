from openai import OpenAI
from .translator import Translator

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
        self.api_url = api_url
        self.model = model
        # 初始化OpenAI客户端
        self.client = OpenAI(
            base_url=self.api_url,
            api_key=self.api_key,
            timeout=30.0,  # 添加超时设置，30秒
        )
        # 设置max_tokens属性，默认值为8192
        self.max_tokens = 8192
    
    def translate(self, text, source_lang, target_lang, doc_type, glossary):
        """使用aiping翻译API翻译文本
        
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
        
        # 构建针对技术文档英翻中的专属提示词
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
        
        import time
        
        max_retries = 3  # 最大重试次数
        retry_delay = 2  # 重试间隔（秒）
        
        for attempt in range(max_retries):
            try:
                # 调用AI Ping API - 使用OpenAI Chat API格式，搭配Qwen3-32B优化参数
                response = self.client.chat.completions.create(
                    model=self.model,
                    stream=True,  # 保持流式调用，兼容现有测试
                    temperature=0.1,  # 降低温度，提高翻译准确性
                    top_p=0.9,  # 核采样参数
                    max_tokens=self.max_tokens,  # 使用类属性作为最大token数
                    extra_body={
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
                    },
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
                for chunk in response:
                    if hasattr(chunk, "choices") and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, "content") and delta.content:
                            translated_text += delta.content
                        elif hasattr(delta, "reasoning_content"):
                            # 跳过思考内容
                            continue
                
                # 文本后处理
                return self._postprocess_text(translated_text, text)
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    # 不是最后一次尝试，记录错误并重试
                    print(f"aiping翻译API请求失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}，将在 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                else:
                    # 最后一次尝试失败，抛出异常
                    raise Exception(f"aiping翻译API请求失败: {str(e)}")


