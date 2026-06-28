import logging
from abc import ABC, abstractmethod
from config import config
from modules.llm_error_handler import classify_llm_error

logger = logging.getLogger(__name__)


class GlossaryExtractor(ABC):
    """术语提取器抽象基类"""

    @abstractmethod
    def extract_glossary(self, text, source_lang, target_lang, doc_type=None):
        """从文本中提取术语表

        Args:
            text (str): 要提取术语的文本
            source_lang (str): 源语言
            target_lang (str): 目标语言
            doc_type (str): 文档类型

        Returns:
            str: 提取的术语表，格式为"术语: 翻译"每行一个
        """
        pass


class BaseApiGlossaryExtractor(GlossaryExtractor):
    """基于OpenAI兼容API的术语提取器基类

    封装了共享的 extract_glossary() 和 _format_glossary() 实现，
    子类仅需在构造函数中提供 API 密钥、URL、模型和 extra_body 配置。
    """

    def __init__(self, api_key, api_url, model, extra_body=None, provider_name='api'):
        """初始化基类术语提取器

        Args:
            api_key (str): API密钥
            api_url (str): API请求地址
            model (str): 模型名称
            extra_body (dict | None): 额外的请求体参数
            provider_name (str): 服务商名称（用于日志）
        """
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.extra_body = extra_body
        self.provider_name = provider_name

    def extract_glossary(self, text, source_lang, target_lang, doc_type=None):
        """从文本中提取术语表

        Args:
            text (str): 要提取术语的文本
            source_lang (str): 源语言
            target_lang (str): 目标语言
            doc_type (str): 文档类型

        Returns:
            str: 提取的术语表，格式为"术语: 翻译"每行一个
        """
        try:
            logger.info(f"使用{self.provider_name}提取术语表")

            # 构建提示词
            doc_type_text = f"，文档类型为{doc_type}" if doc_type else ""
            prompt = f"""
请从以下文本中提取专业术语，并根据以下规则处理：

1. 源语言：{source_lang}
2. 目标语言：{target_lang}

提取规则：
- 核心要求：只提取{doc_type_text}领域中真正的专业术语，具有行业或专业领域的特定含义
- 重要：只提取{source_lang}源语言中的术语，绝对不要提取其他语言的术语
- 重要：确保所有提取的术语都是{source_lang}源语言中的词汇，并且严格属于{doc_type_text}领域的专业术语
- 严格按照源语言和目标语言进行提取和翻译，只处理{source_lang}源语言中的术语
- 核心要求：专业术语必须是{doc_type_text}领域中被广泛认可的、具有特定专业含义的词汇，严格排除普通词汇、日常用语、通用表达和生活词汇
- 核心要求：深入分析文本内容，只识别{doc_type_text}领域中真正的专业术语，绝对避免提取与该领域无关的词汇和普通词汇
- 核心要求：如果文本中只有普通词汇、日常用语或与{doc_type_text}领域无关的词汇，应视为没有专业术语，返回空字符串
- 排除普通词汇、日常用语和通用表达
- 排除人名、地名、公司名等普通专有名词
- 如果源语言和目标语言相同，不要提供翻译
- 每个术语只提取一次，不要重复
- 重要：约定俗成的词汇必须完全保持原样，不进行任何翻译，例如：
  - AI相关：AI、ML、LLM、LLMs
  - 模型名称：ChatGPT、Gemini、Midjourney
  - 其他技术缩写和约定俗成术语
- 核心要求：如果文本中没有{doc_type_text}领域的专业术语需要提取，请严格返回"NO_GLOSSARY"标识，绝对不要返回任何其他文本，包括"无专业术语需要提取"、"没有专业术语"、"（空字符串）"等任何类似内容。直接返回"NO_GLOSSARY"，不要有任何其他输出。
- 核心要求：即使不确定是否有专业术语，只要认为没有符合要求的{doc_type_text}领域专业术语，就必须返回"NO_GLOSSARY"标识，不要返回任何解释或说明，也不要返回任何占位符。
- 核心要求：当返回"NO_GLOSSARY"标识时，确保输出结果只包含"NO_GLOSSARY"这一个词，不要有任何其他字符。

输出格式：
术语: 翻译

核心要求：
- 只返回纯粹的术语列表，严格按照"术语: 翻译"格式，每行一个术语
- 绝对不要返回任何中间过程、思考过程、注释、说明或其他任何文本
- 绝对不要返回"（注：...）"、"修正后输出："等任何形式的注释或说明
- 只返回最终的术语列表，不要有任何其他内容

例如：

AI agents: AI智能体
Large Language Model (LLM): 大语言模型（LLM）
Agent: 智能体
paradigm: 范式
passive, discrete tasks: 被动式、离散型任务
prompt: 提示词
autonomous problem-solving: 自主问题解决

文本：

{text[:5000]}
            """

            # 追加语言专项规则
            try:
                from prompts import rule_registry
                prompt = rule_registry.merge_into_prompt(
                    prompt, "glossary", source_lang, target_lang
                )
            except ImportError:
                pass  # prompts 模块不存在时保持原有行为

            # 调用API
            import openai
            client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.api_url
            )

            # 构建请求参数
            messages = [
                {"role": "system", "content": "你是一个专业的术语提取工具，擅长从文本中识别特定领域的真正专业术语并提供准确的翻译。你严格遵循提取规则，只提取指定领域中具有行业特定含义的专业术语，排除普通词汇和日常用语。"},
                {"role": "user", "content": prompt}
            ]

            # 添加额外参数
            extra_params = {}
            if self.extra_body:
                extra_params["extra_body"] = self.extra_body

            # 发送请求，设置超时时间为30秒
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=config.GLOSSARY_TEMPERATURE,
                max_tokens=config.GLOSSARY_MAX_TOKENS,
                timeout=config.GLOSSARY_TIMEOUT,
                **extra_params
            )

            # 处理响应
            glossary_text = response.choices[0].message.content.strip()
            logger.info(f"{self.provider_name}术语提取结果: {glossary_text}")

            # 确保返回格式正确
            return self._format_glossary(glossary_text)

        except Exception as e:
            error_info = classify_llm_error(e)
            logger.error(f"{self.provider_name}术语提取失败: {error_info['user_message']}")
            return ""

    def _format_glossary(self, glossary_text):
        """格式化术语表

        Args:
            glossary_text (str): 术语表文本

        Returns:
            str: 格式化后的术语表
        """
        lines = glossary_text.split('\n')
        formatted_lines = []

        for line in lines:
            line = line.strip()
            if line:
                # 跳过包含NO_GLOSSARY的行
                if 'NO_GLOSSARY' in line:
                    continue
                # 如果包含冒号，直接添加
                if ': ' in line:
                    formatted_lines.append(line)
                # 否则，作为术语本身添加（当源语言和目标语言相同时）
                else:
                    formatted_lines.append(f"{line}: {line}")

        return '\n'.join(formatted_lines)


class AipingGlossaryExtractor(BaseApiGlossaryExtractor):
    """aiping术语提取器"""

    def __init__(self, api_key=None, api_url=None, model=None):
        """初始化aiping术语提取器

        Args:
            api_key (str, optional): aiping API密钥. Defaults to None.
            api_url (str, optional): aiping API URL. Defaults to None.
            model (str, optional): aiping模型名称. Defaults to None.
        """
        super().__init__(
            api_key=api_key or config.AIPING_API_KEY,
            api_url=api_url or config.AIPING_API_URL,
            model=model or config.AIPING_MODEL_GLOSSARY,
            extra_body=config.AIPING_EXTRA_BODY,
            provider_name='aiping',
        )


class SiliconFlowGlossaryExtractor(BaseApiGlossaryExtractor):
    """硅基流动术语提取器"""

    def __init__(self, api_key=None, api_url=None, model=None):
        """初始化硅基流动术语提取器

        Args:
            api_key (str, optional): 硅基流动API密钥. Defaults to None.
            api_url (str, optional): 硅基流动API URL. Defaults to None.
            model (str, optional): 硅基流动模型名称. Defaults to None.
        """
        super().__init__(
            api_key=api_key or config.SILICON_FLOW_API_KEY,
            api_url=api_url or config.SILICON_FLOW_API_URL,
            model=model or config.SILICON_FLOW_MODEL_GLOSSARY,
            extra_body=config.SILICON_FLOW_EXTRA_BODY,
            provider_name='silicon_flow',
        )


class QianfanGlossaryExtractor(BaseApiGlossaryExtractor):
    """百度千帆术语提取器"""

    def __init__(self, api_key=None, api_url=None, model=None):
        """初始化百度千帆术语提取器

        Args:
            api_key (str, optional): 百度千帆API密钥. Defaults to None.
            api_url (str, optional): 百度千帆API URL. Defaults to None.
            model (str, optional): 百度千帆模型名称. Defaults to None.
        """
        super().__init__(
            api_key=api_key or config.QIANFAN_API_KEY,
            api_url=api_url or config.QIANFAN_API_URL,
            model=model or config.QIANFAN_MODEL_GLOSSARY,
            extra_body=config.QIANFAN_EXTRA_BODY,
            provider_name='qianfan',
        )


def create_glossary_extractor(extractor_type, model=None):
    """创建术语提取器实例

    Args:
        extractor_type (str): 提取器类型 (aiping/silicon_flow/qianfan)
        model (str, optional): 模型名称，None表示使用默认配置

    Returns:
        GlossaryExtractor: 术语提取器实例
    """
    if extractor_type == 'aiping':
        return AipingGlossaryExtractor(model=model)
    elif extractor_type == 'silicon_flow':
        return SiliconFlowGlossaryExtractor(model=model)
    elif extractor_type == 'qianfan':
        return QianfanGlossaryExtractor(model=model)
    else:
        raise ValueError(f"不支持的术语提取器类型: {extractor_type}")
