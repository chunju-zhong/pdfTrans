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
        # 设置max_tokens属性，默认值为8192
        self.max_tokens = 8192
    
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
                max_tokens=self.max_tokens,  # 使用类属性作为最大token数
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


