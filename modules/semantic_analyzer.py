from openai import OpenAI
from config import config

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
        )
        # 设置max_tokens属性，默认值为1024（用于单个语义分析）
        self.max_tokens = 1024
        # 设置batch_max_tokens属性，默认值为2048（用于批量语义分析）
        self.batch_max_tokens = 2048
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
                temperature=0.1,  # 降低温度，提高分析准确性
                top_p=0.9,  # 核采样参数
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
            if hasattr(response, "choices") and len(response.choices) > 0:
                analysis_result = response.choices[0].message.content.strip()

            logger.info(f"LLM返回的原始分析结果: '{analysis_result}'")

            # 解析LLM的分析结果
            analysis_json = json.loads(analysis_result)
            logger.info(f"解析后的JSON结果: {analysis_json}")
            
            should_merge = analysis_json.get("merge", False)
            logger.info(f"最终合并决策: {should_merge}，块1='{text1}', 块2='{text2}'")
            return bool(should_merge)

        except Exception as e:
            # 分析失败时，返回默认值
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"语义分析API请求失败: {str(e)}，返回默认值False")
            logger.error(f"失败时的文本块: 块1='{text1}', 块2='{text2}'")
            return False
    
    def batch_analyze_semantic_relationship(self, text_pairs, source_lang):
        """批量分析多个文本块对之间的语义关系，判断是否应该合并

        Args:
            text_pairs (list): 文本块对列表，每个元素是包含两个文本的元组
            source_lang (str): 源语言代码

        Returns:
            list: 布尔值列表，表示每个文本块对是否应该合并
        """
        import json
        import logging
        import time

        logger = logging.getLogger(__name__)

        # 记录输入文本对的详细信息
        logger.info(f"开始批量语义分析: 文本对数量={len(text_pairs)}, 源语言={source_lang}")
        for i, (text1, text2) in enumerate(text_pairs):
            logger.debug(f"文本对 {i+1}: 块1='{text1[:100]}...' (长度={len(text1)}), 块2='{text2[:100]}...' (长度={len(text2)})")

        # 准备批量语义分析的提示词
        analysis_prompt = self._generate_batch_semantic_analysis_prompt(text_pairs, source_lang)
        logger.info(f"生成批量语义分析提示词: 文本对数量={len(text_pairs)}, 提示词长度={len(analysis_prompt)}")

        max_retries = 3  # 最大重试次数
        retry_delay = 0.5  # 重试间隔（秒）

        for attempt in range(max_retries):
            try:
                logger.info(f"执行API调用 (尝试 {attempt + 1}/{max_retries})")
                # 调用API - 使用标准OpenAI格式
                response = self.client.chat.completions.create(
                    model=self.model,
                    stream=False,  # 非流式调用
                    temperature=0.1,  # 降低温度，提高分析准确性
                    top_p=0.9,  # 核采样参数
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
                logger.info("开始处理响应")
                if hasattr(response, "choices") and len(response.choices) > 0:
                    analysis_result = response.choices[0].message.content.strip()
                    logger.info(f"获取到响应内容，长度={len(analysis_result)}")
                else:
                    logger.error("响应中没有有效的choices字段")

                logger.info(f"LLM返回的原始批量分析结果: '{analysis_result}'")

                # 解析LLM的分析结果
                analysis_json = json.loads(analysis_result)
                logger.info(f"解析后的JSON结果: {analysis_json}")
                
                merge_results = analysis_json.get("merge", [])
                logger.info(f"最终批量合并决策: {merge_results}")
                
                # 确保返回结果数量与输入文本对数量一致
                if len(merge_results) != len(text_pairs):
                    logger.error(f"批量分析结果数量与输入文本对数量不一致: 期望{len(text_pairs)}个结果，实际{len(merge_results)}个结果")
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
                        while len(final_results) < len(text_pairs):
                            final_results.append(False)
                        # 截断多余的项（如果有的话）
                        final_results = final_results[:len(text_pairs)]
                        logger.info(f"补足后结果: {final_results}")
                        return final_results
                
                # 详细记录每个文本对的分析结果
                final_results = [bool(result) for result in merge_results]
                
                logger.info(f"批量语义分析完成: 共分析 {len(text_pairs)} 个文本对，合并 {sum(final_results)} 个")
                return final_results

            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {str(e)}")
                logger.error(f"无法解析的原始结果: '{analysis_result}'")
                if attempt < max_retries - 1:
                    logger.error(f"将在 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                else:
                    logger.error("最终失败，返回默认值列表")
                    return [False] * len(text_pairs)
            except Exception as e:
                if attempt < max_retries - 1:
                    # 不是最后一次尝试，记录错误并重试
                    logger.error(f"批量语义分析API请求失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}，将在 {retry_delay} 秒后重试...")
                    logger.error(f"失败时的文本对数量: {len(text_pairs)}")
                    time.sleep(retry_delay)
                else:
                    # 最后一次尝试失败，返回默认值列表
                    logger.error(f"批量语义分析API请求最终失败: {str(e)}，返回默认值列表")
                    logger.error(f"失败时的文本对数量: {len(text_pairs)}")
                    return [False] * len(text_pairs)
    
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

        return f"""
你是专业的文本语义分析专家，负责分析相邻文本块之间的语义关系。
请使用**两步分析法**判断以下两个{lang_name}文本块是否应该合并。

## 第一步：识别每个文本块的语义角色（Semantic Role）

| 语义角色 | 特征描述 | 合并行为 |
|----------|----------|----------|
| **正文 (body)** | 完整句子或段落片段，描述具体内容，以大写字母或小写字母开头均可 | 可与相邻正文合并 |
| **标题 (title)** | 短语或简短句子，具有概括性、引导性，通常用于引入后续内容 | 不与任何其他角色合并 |
| **签名行/署名 (signature)** | 以 `—` 或 `--` 开头，后跟人名 + 职位/机构/书名等信息 | **独立语义单元，绝不与前不与后合并** |
| **列表项 (list_item)** | 以 `•`、`-`、`*`、数字+`.` 等列表标记开头 | 不与新列表项合并，但可与自身续行合并 |
| **引用正文 (quote_body)** | 引用或推荐的具体内容描述 | 可与同引用内的正文合并，不跨引用合并 |

## 第二步：基于语义角色的合并决策矩阵

```
              块2=正文    块2=标题    块2=签名    块2=列表项
块1=正文      [进一步判断]  不合       不合       [进一步判断]
块1=标题      不合        [进一步判断] 不合       不合
块1=签名      不合        不合       不合       不合
块1=列表项    [续行检查]   不合       不合       不合

[进一步判断] = 检查语义连贯性和语法完整性（是否为同一句子的延续）
[续行检查]   = 检查块2是否为块1列表项内容的续行（以小写字母开头）
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
理由：块2以小写字母"like"开头，是前一句的语法延续，属于同一引用同一句。

### 示例C：标题与正文边界
输入：
块1: "Praise for Designing Large Language Model Applications"
块2: "Designing Large Language Model Applications is a masterclass in building AI"
输出：merge: false
理由：块1是页面标题（短、概括性），块2是引用正文的开始。标题和正文不应合并。

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
    
    def _generate_batch_semantic_analysis_prompt(self, text_pairs, source_lang):
        """生成批量语义分析提示词

        Args:
            text_pairs (list): 文本块对列表，每个元素是包含两个文本的元组
            source_lang (str): 源语言代码

        Returns:
            str: 生成的批量语义分析提示词
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 记录输入信息
        logger.info(f"开始生成批量语义分析提示词: 文本对数量={len(text_pairs)}, 源语言={source_lang}")
        for i, (text1, text2) in enumerate(text_pairs):
            logger.debug(f"文本对 {i+1}: 块1长度={len(text1)}, 块2长度={len(text2)}")
            logger.debug(f"文本对 {i+1}: 块1='{text1[:100]}...'" if len(text1) > 100 else f"文本对 {i+1}: 块1='{text1}'")
            logger.debug(f"文本对 {i+1}: 块2='{text2[:100]}...'" if len(text2) > 100 else f"文本对 {i+1}: 块2='{text2}'")
        
        # 获取语言名称
        lang_name = self.supported_languages.get(source_lang, source_lang)
        
        prompt = f"""
你是专业的文本语义分析专家，负责分析相邻文本块之间的语义关系。
请使用**两步分析法**对以下多对{lang_name}文本块分别判断是否应该合并。
"""
        # 添加文本块对
        for i, (text1, text2) in enumerate(text_pairs):
            prompt += f"\n对{i+1}:\n块1: \"{text1}\"\n块2: \"{text2}\"\n"

        prompt += """
## 第一步：识别每个文本块的语义角色（Semantic Role）

对每一对文本，先识别块1和块2各自的语义角色：

| 语义角色 | 特征描述 | 合并行为 |
|----------|----------|----------|
| **正文 (body)** | 完整句子或段落片段，描述具体内容 | 可与相邻正文合并 |
| **标题 (title)** | 短语/简短句子，概括性、引导性 | 不与任何其他角色合并 |
| **签名行/署名 (signature)** | 以 `—` 或 `--` 开头 + 人名 + 职位/机构/书名 | **独立单元，绝不与前不与后合并** |
| **列表项 (list_item)** | 以 `•`、`-`、`*`、数字+`.` 开头 | 不与新列表项合并，可与自身续行合并 |
| **引用正文 (quote_body)** | 引用/推荐的具体内容描述 | 可与同引用内正文合并不跨引用 |

## 第二步：基于语义角色的合并决策矩阵

```
              块2=正文    块2=标题    块2=签名    块2=列表项
块1=正文      [进一步判断]  不合       不合       [进一步判断]
块1=标题      不合        [进一步判断] 不合       不合
块1=签名      不合        不合       不合       不合
块1=列表项    [续行检查]   不合       不合       不合

[进一步判断] = 检查语义连贯性和语法完整性（是否为同一句子的延续）
[续行检查]   = 检查块2是否为块1列表项内容的续行（以小写字母开头）
不合         = 直接返回 merge=false
```

## 边界场景参考示例（5个核心场景）

### 示例A：签名行边界——签名行是独立语义单元
输入：
对K:
块1: "—Jay Alammar, coauthor, Hands-On Large Language Models"
块2: "Designing Large Language Model Applications is a comprehensive tour of LLMs"
输出：merge: false
理由：块1是引用署名行（signature），标志引用A结束；块2是新引用B的正文。

### 示例B：同一引用内正文可合并
输入：
对L:
块1: "systems. It builds toward a powerful synthesis of advanced methods"
块2: "like tool use, reasoning, RAG, and fine-tuning"
输出：merge: true
理由：块2以小写字母"like"开头，是前一句的语法延续，属于同一引用同一句。

### 示例C：列表项边界——独立列表项不合并
输入：
对M:
块1: "• Understand how to prepare datasets for LLM training"
块2: "• Develop an intuition about the Transformer architecture"
输出：merge: false
理由：两个都是独立的列表项开头（都以 • 开头），每个列表项是独立的语义单元。

### 示例D：列表项续行应合并
输入：
对N:
块1: "• Context to guide reasoning defines the agent's fundamental"
块2: "reasoning patterns and available actions"
输出：merge: true
理由：块2以小写字母"r"开头，是块1列表项内容的续行。

### 示例E：标题与正文边界
输入：
对O:
块1: "Praise for Designing Large Language Model Applications"
块2: "Designing Large Language Model Applications is a masterclass in building AI"
输出：merge: false
理由：块1是页面标题（短、概括性），块2是引用正文的开始。标题和正文不应合并。

## 输出要求

1. 只返回纯JSON字符串，不包含任何其他文本
2. 不要包含Markdown代码块标记（如 ```json 或 ```）
3. 确保返回的内容可以直接被JSON解析器解析
4. 只输出一行JSON
5. 返回一个包含所有分析结果的JSON对象，键为"merge"，值为布尔值数组
6. **关键要求**：返回的 `merge` 数组长度必须与输入文本对数量完全一致，每对输入必须对应一个结果

正确输出格式示例（假设有5对输入）：
{{"merge": [true, false, true, false, true]}}

请严格按照要求输出，仅返回：
{{"merge": [true/false, true/false, ...]}}
"""
        
        logger.info(f"批量语义分析提示词生成完成，长度={len(prompt)}")
        return prompt
