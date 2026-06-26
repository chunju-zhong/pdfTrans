from models.result_types import TranslationResult, TruncationInfo


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

    def cleanup_blocks(self, block_pairs, target_lang="zh"):
        """使用LLM清理翻译后的文本块

        对翻译完成且拆分后的文本块做后处理格式清理，
        修复页脚残留、前导点号、错位拼接等问题。

        基类实现调用 self._get_cleanup_api_kwargs() 获取平台特异的
        extra_body 等参数，子类只需覆盖该钩子方法即可。

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
            api_kwargs = self._get_cleanup_api_kwargs()
            response = self.client.chat.completions.create(
                model=self.model,
                stream=False,
                temperature=0.1,
                max_tokens=4096,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                **api_kwargs
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

    def _get_cleanup_api_kwargs(self):
        """获取cleanup API调用的额外参数

        子类可覆盖此方法以传入平台特定的参数（如 extra_body）。

        Returns:
            dict: 传递给 chat.completions.create 的额外关键字参数
        """
        return {}

    def _parse_cleanup_result(self, result_text, expected_count):
        """解析cleanup_blocks的LLM返回结果

        按 ---块N--- 标记分割LLM返回的清理结果文本。

        Args:
            result_text: LLM返回的文本
            expected_count: 期望的块数量

        Returns:
            list[str]: 解析出的清理后文本列表
        """
        import re
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
11. **列表格式保持**：原文中的列表格式（换行、项目符号如•、-、数字编号等），在翻译结果中保持，不将列表项合并为连续段落；
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
