import logging
import re

from config import config
from models.result_types import TranslationResult, TruncationInfo

logger = logging.getLogger(__name__)


def calculate_max_tokens(input_text, max_ceiling, chars_per_token=3, expansion_factor=3, min_output_tokens=256):
    """独立函数版本，供非 Translator 子类使用

    Args:
        input_text: 输入文本
        max_ceiling: 最大上限
        chars_per_token: 每个token对应的字符数，默认3
        expansion_factor: 扩展因子，默认3
        min_output_tokens: 最小输出token数，默认256

    Returns:
        int: 计算出的 max_tokens
    """
    estimated_tokens = len(input_text) / chars_per_token
    dynamic = max(min_output_tokens, int(estimated_tokens * expansion_factor))
    return min(dynamic, max_ceiling)


_FORMAT_SYSTEM_PROMPT = """你是一个PDF翻译排版质量检查助手。你的工作是检查并优化文本块的格式排版，
使内容在格式上更清晰、更美观、更专业。

【输出格式要求（最高优先级，必须严格遵守）】
- 输出每个块前必须以 `---块N---` 标记开头（N 为块编号，从 1 开始，与输入一致）。
- `---块N---` 标记是结构分隔符，必须在输出中按相同位置回显，不得剥离或省略。
- 一个块对应一个 `---块N---` 标记，块之间不得合并。

示例：
输入：
---块1---
这是第一段译文。
---块2---
这是第二段译文。

正确输出：
---块1---
这是第一段译文。
---块2---
这是第二段译文。

（标记原样回显，仅对正文做格式排版优化。）

严格规则：
- 只做格式排版优化，**不新增内容、不修改正确的文本**
- **结构保留（最高优先级）**：保留目录、列表、多行结构化文本的逐行换行。识别目录模式（条目+页码、序号. 条目 页码、含前导点号的目录行）和页脚/页眉多行结构（如"页码 | 章节名"），逐行保留，不得将结构化文本的换行替换为空格或合并多行为一行。保留原文的换行结构，不得擅自合并行或把换行改为空格。
- 不要改写、润色或重述原文意思
- 如果一个块经处理后变为空，输出空字符串
- 如果不确定，保持文本**完全不变**
- 不要输出解释、注释、备注、思考过程"""


class Translator:
    """翻译基类
    
    定义翻译API的统一接口，具体翻译服务需要继承此类并实现translate方法。
    """
    
    # 动态 max_tokens 计算常量
    CHARS_PER_TOKEN = 3
    EXPANSION_FACTOR = 3
    MIN_OUTPUT_TOKENS = 256
    
    def __init__(self, api_key, api_url=None):
        """初始化翻译器
        
        Args:
            api_key (str): API密钥
            api_url (str, optional): API请求地址
        """
        self.api_key = api_key
        self.api_url = api_url
        self.client = None
        self.supported_languages = {
            'zh': '中文',
            'en': '英语',
            'ja': '日语',
            'ko': '韩语',
            'fr': '法语',
            'de': '德语',
            'es': '西班牙语',
            'ru': '俄语',
            'bo': '藏文'
        }
    
    def translate(self, text, source_lang, target_lang, doc_type, glossary):
        """翻译文本
        
        Args:
            text (str): 要翻译的文本
            source_lang (str): 源语言代码
            target_lang (str): 目标语言代码
            doc_type (str): 文档类型
            glossary (str): 术语表，格式为"术语1: 翻译1\n术语2: 翻译2"
            
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
    
        # 语言不一致，调用具体翻译实现
        raise NotImplementedError("子类必须实现translate方法")
    
    def _postprocess_text(self, text, original_text=""):
        """翻译后处理
        
        Args:
            text (str): 翻译后的文本
            original_text (str): 原始文本，用于回退
            
        Returns:
            str: 处理后的文本
        """
        
        processed_text = text.strip()
        
        # 如果翻译结果为空或只有占位符（如'...'），返回原始文本
        if not processed_text or processed_text == '...':
            return original_text
        
        return processed_text
    
    def batch_translate(self, texts, source_lang, target_lang, doc_type="AI技术", glossary=""):
        """批量翻译文本
        
        Args:
            texts (list): 要翻译的文本列表
            source_lang (str): 源语言代码
            target_lang (str): 目标语言代码
            doc_type (str): 文档类型
            glossary (str): 术语表，格式为"术语1: 翻译1\n术语2: 翻译2"
            
        Returns:
            list: 翻译结果对象列表，每个元素为TranslationResult实例
        """
        # 检查原语言与目标语言是否一致
        if source_lang == target_lang:
            # 语言一致，直接返回原文本列表和空截断信息
            return [TranslationResult(
                content=text,
                token_usage={},
                finish_reason="",
                truncation_info=TruncationInfo(truncated=False, token_usage={}, finish_reason="")
            ) for text in texts]
        
        results = []
        for text in texts:
            result = self.translate(text, source_lang, target_lang, doc_type, glossary)
            results.append(result)
        return results
    
    def _validate_language(self, lang_code):
        """验证语言代码是否支持

        Args:
            lang_code (str): 语言代码

        Returns:
            bool: 如果支持返回True，否则返回False
        """
        return lang_code in self.supported_languages

    def _calculate_max_tokens(self, input_text, max_ceiling=None):
        """根据输入文本长度动态计算 max_tokens

        Args:
            input_text: 输入文本
            max_ceiling: 最大上限，默认使用 self.max_tokens

        Returns:
            int: 计算出的 max_tokens
        """
        estimated_tokens = len(input_text) / self.CHARS_PER_TOKEN
        dynamic = max(self.MIN_OUTPUT_TOKENS, int(estimated_tokens * self.EXPANSION_FACTOR))
        ceiling = max_ceiling if max_ceiling is not None else self.max_tokens
        result = min(dynamic, ceiling)
        logger.debug(f"动态max_tokens: 输入{len(input_text)}字符, 估算{estimated_tokens:.0f}tokens, 计算={dynamic}, 上限={ceiling}, 最终={result}")
        return result

    def format_blocks(self, translated_texts, target_lang="zh"):
        """使用LLM对翻译后的文本块进行格式排版优化

        对翻译完成后的文本块做后处理格式排版，
        包括标点符号规范、中英文混排间距、多余空白清理、
        以及页脚残留、前导点号等异常内容清理。

        基类实现调用 self._get_format_api_kwargs() 获取平台特异的
        extra_body 等参数，子类只需覆盖该钩子方法即可。

        Args:
            translated_texts: 同一页上的译文文本列表（不需要原文配对）
            target_lang: 目标语言代码

        Returns:
            list[str]: 格式排版优化后的文本列表，与输入一一对应
        """
        if not translated_texts:
            return []

        # 无 API client 时回退到原文（基类或未配置的子类）
        if self.client is None:
            return translated_texts

        # 构建输入文本
        parts = [f"---块{i+1}---\n{text}\n\n" for i, text in enumerate(translated_texts)]
        blocks_text = "".join(parts)

        # 注入目标语言名称，使 LLM 按目标语言排版规范优化标点和间距
        target_lang_name = self.supported_languages.get(target_lang, target_lang)

        user_prompt = (
            "请对以下文本块进行格式排版优化。\n"
            f"目标语言为{target_lang_name}，请按{target_lang_name}排版规范优化标点、间距等。\n"
            "输入中的 `---块N---` 标记是结构分隔符，输出时必须为每个块保留对应编号的标记，不得剥离。\n\n"
            f"{blocks_text}"
        )

        # 异常向上抛出由调用方统一处理（task.add_warning 上报 UI）
        api_kwargs = self._get_format_api_kwargs()
        response = self.client.chat.completions.create(
            model=self.model,
            stream=True,
            temperature=0.1,
            max_tokens=self._calculate_max_tokens(blocks_text, max_ceiling=config.LAYOUT_MAX_TOKENS),
            messages=[
                {"role": "system", "content": _FORMAT_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            **api_kwargs
        )

        result_text = ""
        for chunk in response:
            if hasattr(chunk, "choices") and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if hasattr(delta, "content") and delta.content:
                    result_text += delta.content

        # 解析结果：按 ---块N--- 标记分割
        cleaned = self._parse_format_result(result_text, len(translated_texts))

        if len(cleaned) != len(translated_texts):
            logger.warning(
                f"format_blocks: LLM返回了{len(cleaned)}个块（期望{len(translated_texts)}个），回退到原文"
            )
            return translated_texts

        return cleaned

    def _get_format_api_kwargs(self):
        """获取format API调用的额外参数

        子类可覆盖此方法以传入平台特定的参数（如 extra_body）。

        Returns:
            dict: 传递给 chat.completions.create 的额外关键字参数
        """
        return {}

    def _parse_format_result(self, result_text, expected_count):
        """解析format_blocks的LLM返回结果

        按 ---块N--- 标记分割LLM返回的格式化排版结果文本。

        Args:
            result_text: LLM返回的文本
            expected_count: 期望的块数量

        Returns:
            list[str]: 解析出的格式化排版文本列表
        """
        pattern = r'---\s*块(\d+)\s*---'
        parts = re.split(pattern, result_text)

        if len(parts) < 3:
            # 缺少标记，尝试按非空行分割回退
            lines = [l.strip() for l in result_text.strip().split('\n') if l.strip()]
            if len(lines) >= expected_count:
                return lines[:expected_count]
            # 行级回退数量仍不足，返回空列表触发整页回退
            # （返回 [] 使 format_blocks 的长度检查 len([]) != expected_count 恒为 True）
            logger.warning(
                "_parse_format_result: LLM返回结果缺少 ---块N--- 标记且回退行数不足，回退到原文"
            )
            return []

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
    
    def _preprocess_text(self, text):
        """文本预处理
        
        Args:
            text (str): 要处理的文本
            
        Returns:
            str: 预处理后的文本
        """
        return text.strip()
    
    def _generate_system_prompt(self, doc_type, source_lang_name, target_lang_name, glossary,
                                 source_lang_code=None, target_lang_code=None):
        """生成系统提示词

        Args:
            doc_type (str): 文档类型
            source_lang_name (str): 源语言名称
            target_lang_name (str): 目标语言名称
            glossary (str): 术语表
            source_lang_code (str, optional): 源语言代码（如 bo/zh/en），用于追加专项规则
            target_lang_code (str, optional): 目标语言代码（如 zh/en）

        Returns:
            str: 生成的系统提示词
        """
        base_prompt = f"""
你是专业的{doc_type}翻译专家，擅长将{source_lang_name}的{doc_type}文档转写成{target_lang_name}，严格遵循以下规则：

一、核心原则（最高优先级）
1. **忠实直译**：只翻译原文明确包含的信息，禁止脑补、添加原文不存在的细节（如作者、别名、版本、品类、传承等），不编造原文未提及的内容；
2. **禁止膨胀**：翻译长度与原文相当，不添加解释性说明、注释、备注，标题、列表项等短文本尤其应保持简洁；
3. **术语一致**：严格使用以下术语表翻译，不自行创译：
{glossary if glossary else '无'}

二、语义与风格
4. **语义连贯**：基于完整上下文理解，句式适配{target_lang_name}表达习惯，表达流畅，转折自然；
5. **风格一致**：符合原文风格，保持原文档的语气；
6. **语法正确**：符合{target_lang_name}语法规则，避免语法错误，避免缺少句子成分。

三、保持格式（不翻译、不解释）
7. **代码段保留**：原文中的代码段（代码块、行内代码），保持原状不翻译，保持正确的代码格式（缩进、空格、换行、对齐），代码中的注释保持原文；
8. **公式不翻译**：数学公式、LaTeX表达式、数学符号（如 $...$、\\frac{{}}{{}}、α、β、∑ 等），保持原状不翻译；
9. **缩写不解释**：专业缩写（如 AI、LLM、API、CPU 等），保持原状不展开解释；
10. **URL不翻译**：原文中的URL地址，保持原状不翻译；
11. **列表与多行结构保持**：原文中的列表格式（换行、项目符号如•、-、数字编号等）、目录（条目+页码的多行结构，含"序号. 条目 页码"、"条目 ........ 页码"、含前导点号的目录行）、以及其它多行结构化文本（页脚/页眉的"页码 | 章节名"等多行结构），在翻译结果中保持逐行换行，不合并为连续段落，不将换行替换为空格；
12. **单元格分隔符保留**：输入文本包含 "|||" 分隔符时，在翻译结果的对应位置保留每个 "|||"，每个分隔段独立翻译，不合并相邻段内容。

四、禁止元注释
13. **禁止元注释和原文输出**：翻译结果中严禁添加任何形式的注释、说明、备注（如"注："、"说明："等），严禁输出原文内容，只输出{target_lang_name}翻译结果本身，不解释翻译决策。
"""
        # 追加语言专项规则
        if source_lang_code or target_lang_code:
            try:
                from prompts import rule_registry
                return rule_registry.merge_into_prompt(
                    base_prompt, "translation",
                    source_lang_code or "",
                    target_lang_code or "",
                )
            except ImportError:
                pass  # prompts 模块不存在时保持原有行为
        return base_prompt
    
    def _generate_user_prompt(self, source_lang_name, target_lang_name, doc_type, processed_text):
        """生成用户提示词

        Args:
            source_lang_name (str): 源语言名称
            target_lang_name (str): 目标语言名称
            doc_type (str): 文档类型
            processed_text (str): 预处理后的文本

        Returns:
            str: 生成的用户提示词
        """
        return f"请将以下{source_lang_name}的{doc_type}文本转写成{target_lang_name}，严格遵守上述所有规则：\n\n{processed_text}"
