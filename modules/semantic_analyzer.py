import re
from openai import OpenAI
from config import config
from modules.llm_error_handler import classify_llm_error

class SemanticAnalyzer:
    """语义分析基类
    
    定义语义分析API的统一接口，具体语义分析服务需要继承此类并实现相应方法。
    """
    
    def __init__(self, api_key, api_url=None, model=None):
        """初始化语义分析器
        
        Args:
            api_key (str): API密钥
            api_url (str, optional): API请求地址
            model (str, optional): 要使用的模型名称
        """
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        # 初始化OpenAI客户端
        self.client = OpenAI(
            base_url=self.api_url,
            api_key=self.api_key,
            timeout=config.SEMANTIC_ANALYSIS_TIMEOUT,
        )
        # 设置max_tokens属性（使用config的常量）
        self.max_tokens = config.SEMANTIC_ANALYSIS_SINGLE_MAX_TOKENS
        # 设置batch_max_tokens属性
        self.batch_max_tokens = config.SEMANTIC_ANALYSIS_BATCH_MAX_TOKENS
        self.supported_languages = {
            'zh': '中文',
            'en': '英语',
            'ja': '日语',
            'ko': '韩语',
            'fr': '法语',
            'de': '德语',
            'es': '西班牙语',
            'ru': '俄语',
            'bo': '藏语'
        }

    def _extract_json_from_response(self, text):
        """从LLM响应中提取JSON（3级容错）

        Args:
            text (str): LLM返回的原始文本

        Returns:
            dict | None: 解析后的JSON字典，或None
        """
        import json

        # 1. 尝试直接解析（仅当文本以{开头时）
        stripped = text.strip()
        if stripped.startswith('{'):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass

        # 2. 尝试从markdown代码块中提取（兼容 ```json 和裸 ``` 围栏）
        match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # 3. 尝试找到第一个 { 和最后一个 } 之间的内容
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

        return None

    def analyze_semantic_relationship(self, text1, text2, source_lang):
        """分析两个文本块之间的语义关系，判断是否应该合并

        Args:
            text1 (str): 第一个文本块
            text2 (str): 第二个文本块
            source_lang (str): 源语言代码

        Returns:
            bool: 是否应该合并
        """
        import json
        import logging

        logger = logging.getLogger(__name__)

        # 准备语义分析的提示词
        analysis_prompt = self._generate_semantic_analysis_prompt(text1, text2, source_lang)
        logger.info(f"生成语义分析提示词: 块1='{text1}', 块2='{text2}', 提示词长度={len(analysis_prompt)}")

        try:
            # 调用API - 使用标准OpenAI格式
            response = self.client.chat.completions.create(
                model=self.model,
                stream=False,  # 非流式调用
                temperature=config.SEMANTIC_ANALYSIS_TEMPERATURE,
                top_p=config.SEMANTIC_ANALYSIS_TOP_P,
                max_tokens=self.max_tokens,  # 使用类属性作为最大token数
                extra_body=config.SILICON_FLOW_EXTRA_BODY,
                messages=[
                    {
                        "role": "system",
                        "content": "你是专业的文本语义分析专家，负责分析相邻文本块之间的语义关系。"
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ]
            )

            # 处理响应
            analysis_result = ""
            reasoning_content = ""
            finish_reason = ""
            if hasattr(response, "choices") and len(response.choices) > 0:
                choice = response.choices[0]
                if hasattr(choice, "message"):
                    if hasattr(choice.message, "content") and choice.message.content:
                        analysis_result = choice.message.content.strip()
                    # 读取 reasoning_content（用于 fallback）
                    if hasattr(choice.message, "reasoning_content") and choice.message.reasoning_content:
                        reasoning_content = choice.message.reasoning_content.strip()
                if hasattr(choice, "finish_reason"):
                    finish_reason = choice.finish_reason

            # content 为空时记录诊断日志并尝试从 reasoning_content fallback
            if not analysis_result:
                logger.warning(
                    f"语义分析结果 content 为空: reasoning_content长度={len(reasoning_content)}, "
                    f"finish_reason={finish_reason}, 块1前100字符='{text1[:100]}', 块2前100字符='{text2[:100]}'"
                )
                if reasoning_content:
                    analysis_result = reasoning_content

            logger.info(f"LLM返回的原始分析结果: '{analysis_result}'")

            # 解析LLM的分析结果
            analysis_json = self._extract_json_from_response(analysis_result)
            if analysis_json is None:
                raise json.JSONDecodeError("无法从响应中提取JSON", analysis_result, 0)
            logger.info(f"解析后的JSON结果: {analysis_json}")

            should_merge = analysis_json.get("merge", False)
            logger.info(f"最终合并决策: {should_merge}，块1='{text1}', 块2='{text2}'")
            return bool(should_merge)

        except Exception as e:
            # 分析失败时，返回默认值
            import logging
            logger = logging.getLogger(__name__)
            error_info = classify_llm_error(e)
            logger.error(f"语义分析API请求失败: {error_info['user_message']}，返回默认值False")
            logger.error(f"失败时的文本块: 块1='{text1}', 块2='{text2}'")
            return False
    
    def batch_analyze_semantic_relationship(self, blocks, source_lang):
        """批量分析顺序文本块之间的语义关系，判断相邻块是否应该合并

        Args:
            blocks (list[str]): 顺序文本块列表
            source_lang (str): 源语言代码

        Returns:
            list: 布尔值列表，长度为 len(blocks)-1，表示每对相邻块是否应该合并
        """
        import json
        import logging
        import time

        logger = logging.getLogger(__name__)

        # 少于2个块时无需分析
        if len(blocks) <= 1:
            logger.info(f"文本块数量={len(blocks)}，不足2个，无需分析")
            return []

        expected_merge_count = len(blocks) - 1

        # 记录输入文本块的详细信息
        logger.info(f"开始批量语义分析: 文本块数量={len(blocks)}, 源语言={source_lang}, 预期合并决策数={expected_merge_count}")
        for i, block in enumerate(blocks):
            logger.debug(f"块 {i+1}: '{block[:100]}...' (长度={len(block)})")

        # 准备批量语义分析的提示词
        analysis_prompt = self._generate_batch_semantic_analysis_prompt(blocks, source_lang)
        logger.info(f"生成批量语义分析提示词: 文本块数量={len(blocks)}, 提示词长度={len(analysis_prompt)}")

        max_retries = 3  # 最大重试次数
        retry_delay = 0.5  # 重试间隔（秒）

        for attempt in range(max_retries):
            try:
                logger.info(f"执行API调用 (尝试 {attempt + 1}/{max_retries})")
                # 调用API - 使用标准OpenAI格式
                response = self.client.chat.completions.create(
                    model=self.model,
                    stream=False,  # 非流式调用
                    temperature=config.SEMANTIC_ANALYSIS_TEMPERATURE,
                    top_p=config.SEMANTIC_ANALYSIS_TOP_P,
                    max_tokens=self.batch_max_tokens,  # 使用类属性作为最大token数
                    extra_body=config.SILICON_FLOW_EXTRA_BODY,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是专业的文本语义分析专家，负责分析相邻文本块之间的语义关系。"
                        },
                        {
                            "role": "user",
                            "content": analysis_prompt
                        }
                    ]
                )

                # 处理响应
                analysis_result = ""
                reasoning_content = ""
                finish_reason = ""
                logger.info("开始处理响应")
                if hasattr(response, "choices") and len(response.choices) > 0:
                    choice = response.choices[0]
                    if hasattr(choice, "message"):
                        if hasattr(choice.message, "content") and choice.message.content:
                            analysis_result = choice.message.content.strip()
                            logger.info(f"获取到响应内容，长度={len(analysis_result)}")
                        # 读取 reasoning_content（用于 fallback）
                        if hasattr(choice.message, "reasoning_content") and choice.message.reasoning_content:
                            reasoning_content = choice.message.reasoning_content.strip()
                    if hasattr(choice, "finish_reason"):
                        finish_reason = choice.finish_reason
                else:
                    logger.error("响应中没有有效的choices字段")

                # content 为空时记录诊断日志并尝试从 reasoning_content fallback
                if not analysis_result:
                    logger.warning(
                        f"批量语义分析结果 content 为空: reasoning_content长度={len(reasoning_content)}, "
                        f"finish_reason={finish_reason}, 文本块数量={len(blocks)}, 块1前100字符='{blocks[0][:100] if blocks else ''}'"
                    )
                    if reasoning_content:
                        analysis_result = reasoning_content

                logger.info(f"LLM返回的原始批量分析结果: '{analysis_result}'")

                # 解析LLM的分析结果
                analysis_json = self._extract_json_from_response(analysis_result)
                if analysis_json is None:
                    raise json.JSONDecodeError("无法从响应中提取JSON", analysis_result, 0)
                logger.info(f"解析后的JSON结果: {analysis_json}")

                merge_results = analysis_json.get("merge", [])
                logger.info(f"最终批量合并决策: {merge_results}")
                
                # 确保返回结果数量与预期一致（len(blocks) - 1）
                if len(merge_results) != expected_merge_count:
                    logger.error(f"批量分析结果数量与预期不一致: 期望{expected_merge_count}个结果，实际{len(merge_results)}个结果")
                    if attempt < max_retries - 1:
                        logger.error(f"结果数量不一致，将在 {retry_delay} 秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        # 最后一次尝试失败，保留已有结果并将缺失的项记为false
                        logger.error("最终失败，保留已有结果并将缺失的项记为false")
                        # 转换为布尔值
                        final_results = [bool(result) for result in merge_results]
                        # 补足缺失的项
                        while len(final_results) < expected_merge_count:
                            final_results.append(False)
                        # 截断多余的项（如果有的话）
                        final_results = final_results[:expected_merge_count]
                        logger.info(f"补足后结果: {final_results}")
                        return final_results
                
                # 详细记录每个相邻块对的分析结果
                final_results = [bool(result) for result in merge_results]
                
                logger.info(f"批量语义分析完成: 共分析 {len(blocks)} 个文本块，{expected_merge_count} 个相邻对，合并 {sum(final_results)} 个")
                return final_results

            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {str(e)}")
                logger.error(f"无法解析的原始结果: '{analysis_result}'")
                if attempt < max_retries - 1:
                    logger.error(f"将在 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                else:
                    logger.error("最终失败，返回默认值列表")
                    return [False] * expected_merge_count
            except Exception as e:
                if attempt < max_retries - 1:
                    # 不是最后一次尝试，记录错误并重试
                    logger.error(f"批量语义分析API请求失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}，将在 {retry_delay} 秒后重试...")
                    logger.error(f"失败时的文本块数量: {len(blocks)}")
                    time.sleep(retry_delay)
                else:
                    # 最后一次尝试失败，返回默认值列表
                    logger.error(f"批量语义分析API请求最终失败: {str(e)}，返回默认值列表")
                    logger.error(f"失败时的文本块数量: {len(blocks)}")
                    return [False] * expected_merge_count
    
    def _generate_semantic_analysis_prompt(self, text1, text2, source_lang):
        """生成语义分析提示词

        Args:
            text1 (str): 第一个文本块
            text2 (str): 第二个文本块
            source_lang (str): 源语言代码

        Returns:
            str: 生成的语义分析提示词
        """
        # 获取语言名称
        lang_name = self.supported_languages.get(source_lang, source_lang)

        base_prompt = f"""
你是专业的文本语义分析专家，负责分析相邻文本块之间的语义关系。
请使用**两步分析法**判断以下两个{lang_name}文本块是否应该合并。

## 第一步：识别每个文本块的语义角色（Semantic Role）

| 语义角色 | 特征描述 | 合并行为 |
|----------|----------|----------|
| **正文 (body)** | 完整句子或段落片段，描述具体内容，以大写字母或小写字母开头均可 | 可与相邻正文合并 |
| **标题 (title)** | 短语或简短句子，具有概括性、引导性，通常用于引入后续内容 | 不与任何其他角色合并 |
| **签名行/署名 (signature)** | 署名、签名或归属行，通常包含人名和职位/机构信息，标志一段引用或推荐的结束 | **独立语义单元，绝不与前不与后合并** |
| **列表项 (list_item)** | 以列表标记开头（如项目符号、数字编号等），是独立的列举条目 | 不与新列表项合并，但可与自身续行合并 |
| **引用正文 (quote_body)** | 引用或推荐的具体内容描述 | 可与同引用内的正文合并，不跨引用合并 |

## 第二步：基于语义角色的合并决策矩阵

```
              块2=正文    块2=标题    块2=签名    块2=列表项
块1=正文      [进一步判断]  不合       不合       [进一步判断]
块1=标题      不合        [进一步判断] 不合       不合
块1=签名      不合        不合       不合       不合
块1=列表项    [续行检查]   不合       不合       不合

[进一步判断] = 检查语义连贯性和语法完整性（是否为同一句子的延续），重点检测段落边界：
  - **段落边界信号（任一满足即不合并 merge=false）**：
    ① 前块以终结标点结尾（如句号。/./！/？/！等），是完整的终结语句
    ② 后块以新句子的开头标志起始（如独立的新主语、新话题起始词等），而非前句的语法延续
    ③ 后块引入全新话题或主语（与前块讨论对象明显不同）
  - **句子延续信号（才合并 merge=true）**：后块是前句的语法延续（如连接词、逗号后的内容、或明显是前句未完成的部分）
[续行检查]   = 检查块2是否为块1列表项内容的续行（非独立新句子，而是块1内容的延续）
不合         = 直接返回 merge=false
```

## 待分析的文本对

块1: "{text1}"
块2: "{text2}"

## 边界场景参考示例

### 示例A：签名行边界（核心场景——签名行是独立单元）
输入：
块1: "—Jay Alammar, coauthor, Hands-On Large Language Models"
块2: "Designing Large Language Model Applications is a comprehensive tour of LLMs"
输出：merge: false
理由：块1是引用署名行（signature），标志引用A结束；块2是新引用B的正文。两者属于不同引用。

### 示例B：同一引用内正文可合并
输入：
块1: "systems. It builds toward a powerful synthesis of advanced methods"
块2: "like tool use, reasoning, RAG, and fine-tuning"
输出：merge: true
理由：块2"like tool use..."是块1前一句的语法延续（非独立新句），属于同一引用同一句。

### 示例C：标题与正文边界
输入：
块1: "Praise for Designing Large Language Model Applications"
块2: "Designing Large Language Model Applications is a masterclass in building AI"
输出：merge: false
理由：块1是页面标题（短、概括性），块2是引用正文的开始。标题和正文不应合并。

### 示例F：段落边界——完整的独立段落之间不合并
输入：
块1: "The book is so much better for it."
块2: "I am thankful to the Toronto AI ecosystem, especially the Aggregate Intellect community for providing me with space"
输出：merge: false
理由：块1以句号结尾，是完整的终结语句；块2以全新句子开头，引入了不同的话题（从感谢Amber Teng转为感谢Toronto AI生态）。这是典型的段落边界，两个独立段落不应合并。

## 输出要求

1. 只返回纯JSON字符串，不包含任何其他文本
2. 不要包含Markdown代码块标记（如 ```json 或 ```）
3. 确保返回的内容可以直接被JSON解析器解析
4. 只输出一行JSON，只包含merge字段，值为true或false

正确输出格式：
{{"merge": true}}

请严格按照要求输出，仅返回：
{{"merge": true/false}}
"""
        # 追加语言专项规则
        try:
            from prompts import rule_registry  # noqa: F811
            return rule_registry.merge_into_prompt(
                base_prompt, "semantic", source_lang, "*"
            )
        except ImportError:
            pass
        return base_prompt

    def _generate_batch_semantic_analysis_prompt(self, blocks, source_lang):
        """生成批量语义分析提示词

        Args:
            blocks (list[str]): 顺序文本块列表
            source_lang (str): 源语言代码

        Returns:
            str: 生成的批量语义分析提示词
        """
        import logging
        logger = logging.getLogger(__name__)

        n = len(blocks)
        # 记录输入信息
        logger.info(f"开始生成批量语义分析提示词: 文本块数量={n}, 源语言={source_lang}")
        for i, block in enumerate(blocks):
            logger.debug(f"块 {i+1}: 长度={len(block)}")
            logger.debug(f"块 {i+1}: '{block[:100]}...'" if len(block) > 100 else f"块 {i+1}: '{block}'")

        # 获取语言名称
        lang_name = self.supported_languages.get(source_lang, source_lang)

        # 构建块列表部分
        blocks_section = ""
        for i, block in enumerate(blocks):
            blocks_section += f"\n块{i+1}: \"{block}\"\n"

        prompt = f"""
你是专业的文本语义分析专家，负责分析相邻文本块之间的语义关系。
请使用**两步分析法**对以下 {n} 个顺序排列的{lang_name}文本块，判断每对相邻块是否应该合并。

## 待分析的文本块（共{n}个，需输出{n-1}个合并决策）

{blocks_section}
## 第一步：识别每个文本块的语义角色（Semantic Role）

对每个文本块，先识别其语义角色：

| 语义角色 | 特征描述 | 合并行为 |
|----------|----------|----------|
| **正文 (body)** | 完整句子或段落片段，描述具体内容 | 可与相邻正文合并 |
| **标题 (title)** | 短语/简短句子，概括性、引导性 | 不与任何其他角色合并 |
| **签名行/署名 (signature)** | 署名、签名或归属行，通常包含人名和职位/机构信息，标志引用或推荐的结束 | **独立单元，绝不与前不与后合并** |
| **列表项 (list_item)** | 以列表标记开头（如项目符号、数字编号等），是独立的列举条目 | 不与新列表项合并，可与自身续行合并 |
| **引用正文 (quote_body)** | 引用/推荐的具体内容描述 | 可与同引用内正文合并不跨引用 |

## 第二步：基于语义角色的合并决策矩阵

```
              块i+1=正文    块i+1=标题    块i+1=签名    块i+1=列表项
块i=正文      [进一步判断]  不合       不合       [进一步判断]
块i=标题      不合        [进一步判断] 不合       不合
块i=签名      不合        不合       不合       不合
块i=列表项    [续行检查]   不合       不合       不合

[进一步判断] = 检查语义连贯性和语法完整性（是否为同一句子的延续），重点检测段落边界：
  - **段落边界信号（任一满足即不合并 merge=false）**：
    ① 块i以终结标点结尾（如句号。/./！/？/！等），是完整的终结语句
    ② 块i+1以新句子的开头标志起始（如独立的新主语、新话题起始词等），而非前句的语法延续
    ③ 块i+1引入全新话题或主语（与块i讨论对象明显不同）
  - **句子延续信号（才合并 merge=true）**：块i+1是块i前句的语法延续（如连接词、逗号后的内容、或明显是前句未完成的部分）
[续行检查]   = 检查块i+1是否为块i列表项内容的续行（非独立新句子，而是块i内容的延续）
不合         = 直接返回 merge=false
```

## 上下文感知指导

**重要**：在判断块i和块i+1是否应合并时，你**应该参考**块1到块i-1的语义角色和内容来做出更准确的决策。前文上下文能帮助你：
- 判断当前块是否处于某个引用/推荐的内部（前文有引用正文则当前块更可能是同一引用的延续）
- 判断签名行是否标志着一个引用的结束（前文有引用正文则签名行更可能是该引用的署名）
- 判断标题是否引入了新的主题段落（前文主题已结束则标题更可能是新段落的开始）
- 判断正文是否属于同一话题的延续（前文讨论同一主题则更可能需要合并）

## 边界场景参考示例（6个核心场景）

### 示例A：签名行边界——签名行是独立语义单元
输入：
块1: "—Jay Alammar, coauthor, Hands-On Large Language Models"
块2: "Designing Large Language Model Applications is a comprehensive tour of LLMs"
输出：merge: [false]
理由：块1是引用署名行（signature），标志引用A结束；块2是新引用B的正文。

### 示例B：同一引用内正文可合并
输入：
块1: "systems. It builds toward a powerful synthesis of advanced methods"
块2: "like tool use, reasoning, RAG, and fine-tuning"
输出：merge: [true]
理由：块2"like tool use..."是块1前一句的语法延续（非独立新句），属于同一引用同一句。

### 示例C：列表项边界——独立列表项不合并
输入：
块1: "• Understand how to prepare datasets for LLM training"
块2: "• Develop an intuition about the Transformer architecture"
输出：merge: [false]
理由：两个都是独立的列表项开头（都以 • 开头），每个列表项是独立的语义单元。

### 示例D：列表项续行应合并
输入：
块1: "• Context to guide reasoning defines the agent's fundamental"
块2: "reasoning patterns and available actions"
输出：merge: [true]
理由：块2"reasoning patterns..."是块1列表项内容的续行（非独立新列表项）。

### 示例E：标题与正文边界
输入：
块1: "Praise for Designing Large Language Model Applications"
块2: "Designing Large Language Model Applications is a masterclass in building AI"
输出：merge: [false]
理由：块1是页面标题（短、概括性），块2是引用正文的开始。标题和正文不应合并。

### 示例F：段落边界——完整的独立段落之间不合并
输入：
块1: "The book is so much better for it."
块2: "I am thankful to the Toronto AI ecosystem, especially the Aggregate Intellect community for providing me with space"
输出：merge: [false]
理由：块1以句号结尾，是完整的终结语句；块2以全新句子开头，引入了不同的话题。这是典型的段落边界，两个独立段落不应合并。

## 输出要求

1. 只返回纯JSON字符串，不包含任何其他文本
2. 不要包含Markdown代码块标记（如 ```json 或 ```）
3. 确保返回的内容可以直接被JSON解析器解析
4. 只输出一行JSON
5. 返回一个包含所有分析结果的JSON对象，键为"merge"，值为布尔值数组
6. **关键要求**：返回的 `merge` 数组长度必须为 {n-1}（即块数减1），每个元素对应一对相邻块的合并决策：merge[0]对应块1与块2，merge[1]对应块2与块3，依此类推

正确输出格式示例（假设有{n}个块，需输出{n-1}个决策）：
{{"merge": [true, false, true, false, true]}}

请严格按照要求输出，仅返回：
{{"merge": [true/false, true/false, ...]}}
"""

        logger.info(f"批量语义分析提示词生成完成，长度={len(prompt)}")
        # 追加语言专项规则
        try:
            from prompts import rule_registry
            return rule_registry.merge_into_prompt(
                prompt, "semantic", source_lang, "*"
            )
        except ImportError:
            pass
        return prompt
