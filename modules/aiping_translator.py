from openai import OpenAI
from .translator import Translator

class AipingTranslator(Translator):
    """aiping翻译API实现
    
    继承自Translator基类，实现aiping翻译API的调用逻辑。
    """
    
    def __init__(self, api_key, api_url=None, model="Qwen3-32B"):
        """初始化aiping翻译器
        
        Args:
            api_key (str): aiping翻译API的密钥
            api_url (str, optional): aiping翻译API的请求地址
            model (str, optional): 要使用的模型名称
        """
        super().__init__(api_key, api_url)
        self.api_url = api_url or "https://aiping.cn/api/v1"
        self.model = model
        # 初始化OpenAI客户端
        self.client = OpenAI(
            base_url=self.api_url,
            api_key=self.api_key,
        )
    
    def translate(self, text, source_lang, target_lang, doc_type="技术文档", glossary=""):
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
        
        # 构建针对技术文档英翻中的专属提示词
        system_prompt = f"""
你是专业的{doc_type}翻译专家，擅长将{source_lang_name}文档精准翻译成{target_lang_name}，严格遵循以下规则：
1. 语义连贯：必须基于完整上下文理解，禁止逐词直译导致的句子断裂；
2. 术语一致：严格使用以下术语表翻译，不随意变更：
{glossary if glossary else '无'}
3. 句式严谨：保持技术文档的正式语气，保留被动语态和逻辑连接词；
4. 不增删义：严格遵循原文含义，不添加额外解释，不遗漏任何细节（包括标点、括号、冒号的位置）；
5. 格式兼容：翻译结果需便于后续按原文本块拆分，不擅自添加换行、分段（保持段落级完整性）；
6. 技术精准：对于{doc_type}术语、代码片段、公式等，保持高度准确性，避免误译。
"""
        
        # 构建用户提示词 - 仅包含当前合并块文本，不包含额外上下文（Qwen3-32B上下文足够）
        user_prompt = f"请将以下{source_lang_name}的{doc_type}文本翻译成{target_lang_name}，严格遵守上述所有规则：\n\n{processed_text}"
        
        try:
            # 调用AI Ping API - 使用OpenAI Chat API格式，搭配Qwen3-32B优化参数
            response = self.client.chat.completions.create(
                model=self.model,
                stream=True,  # 保持流式调用，兼容现有测试
                temperature=0.1,  # 降低温度，提高翻译准确性
                top_p=0.9,  # 核采样参数
                max_tokens=8192,  # 最大token数
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
            raise Exception(f"aiping翻译API请求失败: {str(e)}")
