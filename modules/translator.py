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
    
    def translate(self, text, source_lang, target_lang, doc_type="技术文档", glossary=""):
        """翻译文本
        
        Args:
            text (str): 要翻译的文本
            source_lang (str): 源语言代码
            target_lang (str): 目标语言代码
            doc_type (str): 文档类型（如"AI/软件技术文档"）
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
    
    def batch_translate(self, texts, source_lang, target_lang):
        """批量翻译文本
        
        Args:
            texts (list): 要翻译的文本列表
            source_lang (str): 源语言代码
            target_lang (str): 目标语言代码
            
        Returns:
            list: 翻译后的文本列表
        """
        # 检查原语言与目标语言是否一致
        if source_lang == target_lang:
            # 语言一致，直接返回原文本列表
            return texts.copy()
        
        results = []
        for text in texts:
            translated_text = self.translate(text, source_lang, target_lang)
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
    