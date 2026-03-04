import logging
from abc import ABC, abstractmethod
from config import config

logger = logging.getLogger(__name__)


class GlossaryExtractor(ABC):
    """术语提取器抽象基类"""
    
    @abstractmethod
    def extract_glossary(self, text, source_lang, target_lang):
        """从文本中提取术语表
        
        Args:
            text (str): 要提取术语的文本
            source_lang (str): 源语言
            target_lang (str): 目标语言
            
        Returns:
            str: 提取的术语表，格式为"术语: 翻译"每行一个
        """
        pass


class AipingGlossaryExtractor(GlossaryExtractor):
    """aiping术语提取器"""
    
    def __init__(self, api_key=None, api_url=None, model=None):
        """初始化aiping术语提取器
        
        Args:
            api_key (str, optional): aiping API密钥. Defaults to None.
            api_url (str, optional): aiping API URL. Defaults to None.
            model (str, optional): aiping模型名称. Defaults to None.
        """
        self.api_key = api_key or config.AIPING_API_KEY
        self.api_url = api_url or config.AIPING_API_URL
        self.model = model or config.AIPING_MODEL_GLOSSARY
        self.extra_body = config.AIPING_EXTRA_BODY
    
    def extract_glossary(self, text, source_lang, target_lang):
        """从文本中提取术语表
        
        Args:
            text (str): 要提取术语的文本
            source_lang (str): 源语言
            target_lang (str): 目标语言
            
        Returns:
            str: 提取的术语表，格式为"术语: 翻译"每行一个
        """
        try:
            logger.info("使用aiping提取术语表")
            
            # 构建提示词
            prompt = f"请从以下文本中提取专业术语及其{target_lang}翻译，严格按照以下格式生成：\n\n术语: 翻译\n\n每行只包含一个术语，不要包含任何其他文本或解释。例如：\n\nAgents: 代理\nAI Agents: 人工智能代理\n\n文本：\n\n{text[:2000]}"
            
            # 调用aiping API
            import openai
            client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.api_url
            )
            
            # 构建请求参数
            messages = [
                {"role": "system", "content": "你是一个专业的术语提取工具，擅长从文本中识别专业术语并提供准确的翻译。"},
                {"role": "user", "content": prompt}
            ]
            
            # 添加额外参数
            extra_params = {}
            if self.extra_body:
                extra_params["extra_body"] = self.extra_body
            
            # 发送请求
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                **extra_params
            )
            
            # 处理响应
            glossary_text = response.choices[0].message.content.strip()
            logger.info(f"aiping术语提取结果: {glossary_text}")
            
            # 确保返回格式正确
            return self._format_glossary(glossary_text)
            
        except Exception as e:
            logger.error(f"aiping术语提取失败: {str(e)}")
            return ""
    
    def _format_glossary(self, glossary_text):
        """格式化术语表
        
        Args:
            glossary_text (str): 术语表文本
            
        Returns:
            str: 格式化后的术语表
        """
        # 确保每行都是"术语: 翻译"格式
        lines = glossary_text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line and ': ' in line:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)


class SiliconFlowGlossaryExtractor(GlossaryExtractor):
    """硅基流动术语提取器"""
    
    def __init__(self, api_key=None, api_url=None, model=None):
        """初始化硅基流动术语提取器
        
        Args:
            api_key (str, optional): 硅基流动API密钥. Defaults to None.
            api_url (str, optional): 硅基流动API URL. Defaults to None.
            model (str, optional): 硅基流动模型名称. Defaults to None.
        """
        self.api_key = api_key or config.SILICON_FLOW_API_KEY
        self.api_url = api_url or config.SILICON_FLOW_API_URL
        self.model = model or config.SILICON_FLOW_MODEL_GLOSSARY
    
    def extract_glossary(self, text, source_lang, target_lang):
        """从文本中提取术语表
        
        Args:
            text (str): 要提取术语的文本
            source_lang (str): 源语言
            target_lang (str): 目标语言
            
        Returns:
            str: 提取的术语表，格式为"术语: 翻译"每行一个
        """
        try:
            logger.info("使用硅基流动提取术语表")
            
            # 构建提示词
            prompt = f"请从以下文本中提取专业术语及其{target_lang}翻译，严格按照以下格式生成：\n\n术语: 翻译\n\n每行只包含一个术语，不要包含任何其他文本或解释。例如：\n\nAgents: 代理\nAI Agents: 人工智能代理\n\n文本：\n\n{text[:2000]}"
            
            # 调用硅基流动API
            import openai
            client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.api_url
            )
            
            # 构建请求参数
            messages = [
                {"role": "system", "content": "你是一个专业的术语提取工具，擅长从文本中识别专业术语并提供准确的翻译。"},
                {"role": "user", "content": prompt}
            ]
            
            # 发送请求
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3
            )
            
            # 处理响应
            glossary_text = response.choices[0].message.content.strip()
            logger.info(f"硅基流动术语提取结果: {glossary_text}")
            
            # 确保返回格式正确
            return self._format_glossary(glossary_text)
            
        except Exception as e:
            logger.error(f"硅基流动术语提取失败: {str(e)}")
            return ""
    
    def _format_glossary(self, glossary_text):
        """格式化术语表
        
        Args:
            glossary_text (str): 术语表文本
            
        Returns:
            str: 格式化后的术语表
        """
        # 确保每行都是"术语: 翻译"格式
        lines = glossary_text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line and ': ' in line:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)


def create_glossary_extractor(extractor_type):
    """创建术语提取器实例
    
    Args:
        extractor_type (str): 提取器类型 (aiping/silicon_flow)
        
    Returns:
        GlossaryExtractor: 术语提取器实例
    """
    if extractor_type == 'aiping':
        return AipingGlossaryExtractor()
    elif extractor_type == 'silicon_flow':
        return SiliconFlowGlossaryExtractor()
    else:
        raise ValueError(f"不支持的术语提取器类型: {extractor_type}")
