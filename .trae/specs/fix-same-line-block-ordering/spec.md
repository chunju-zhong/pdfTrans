# 修复右对齐正文块翻译拆分语序混乱 Spec

## Why

第3页（Praise 书评页）的签名行（如 `—Jay Alammar, coauthor...`）与下一个引用的正文被错误合并为一个 MergedBlock，导致 `split_translated_result()` 按原始块长度比例拆分翻译文本时语序混乱。

**根本原因**：当前 LLM 语义合并提示词对**独立语义单元边界**的识别不准确。LLM 仅基于"两块文本是否属于同一句子/段落"做判断，但缺乏对以下边界类型的显式认知：

* **引用署名行（signature line）**：标志一个引用的结束，后面是新引用的开始

* **独立结构元素**：标题、列表项、署名行等应作为独立语义单元

* **语义角色切换**：从正文→署名→新正文 是语义角色变化，不应合并

原文布局和问题数据见下方"根因分析"章节。

## 根因分析（三阶段演进）

### 阶段1：标题与正文跨对齐合并（已解决 ✅）

左对齐标题 "Prase for..." 与右对齐正文被合并 → 通过 **alignment 属性 + 对齐检测** 解决（Task 1-7）

### 阶段2：对齐检测误判（已解决 ✅）

左右对称布局中所有文本被误判为居中 → 修正检测优先级为**左/右对齐优先于居中**（Task 7）

### 阶段3（当前问题）：签名行跨引用合并（待解决 ❌）

对齐修复生效后标题正确分离，但**签名行仍与下一引用正文被合并**。

#### 实际日志数据（2026-06-10 06:53 运行）

**第3页文本块按 y0 排序：**

| 块编号 | 文本                                                                                     | 角色        | 对齐   |
| --- | -------------------------------------------------------------------------------------- | --------- | ---- |
| 0   | "Praise for Designing Large Language Model Applications"                               | 标题        | 左(0) |
| 1   | "Designing Large Language Model Applications is a masterclass..." (Jay 引用A正文)          | 正文        | 右(2) |
| 2   | "**—Jay Alammar**, coauthor, Hands-On Large Language Models"                           | **引用A签名** | 右(2) |
| 3   | "Designing Large Language Model Applications is a comprehensive tour..." (Megan 引用B正文) | 正文        | 右(2) |
| 4   | "**—Megan Risdal**, lead product manager, Kaggle (Google)"                             | **引用B签名** | 右(2) |
| 5   | "Designing Large Language Model Applications is a complete..." (Madhav 引用C正文)          | 正文        | 右(2) |
| 6   | "A rare, well-curated book that covers all..." (引用C续)                                  | 正文        | 右(2) |
| 7   | "**—Madhav Singhal**, CEO, AutoComputer"                                               | **引用C签名** | 右(2) |

**LLM 合并判断结果（错误）：**

| 合并块    | 内容                                           | 问题           |
| ------ | -------------------------------------------- | ------------ |
| 17     | "Praise for..." (单独)                         | ✅ 正确分离       |
| 18     | Jay Alammar 引用正文 (单独)                        | ✅ 正确         |
| **19** | **"—Jay Alammar... + Megan Risdal 引用正文"**    | ❌ **跨引用合并！** |
| **20** | **"—Megan Risdal... + Madhav Singhal 引用正文"** | ❌ **跨引用合并！** |
| 21     | Madhav Singhal 引用续 + 签名                      | ✅ 同一引用内正确    |

**为什么 LLM 判断错误？**

LLM 收到的文本对是：

```
块1: "—Jay Alammar, coauthor, Hands-On Large Language Models"
块2: "Designing Large Language Model Applications is a comprehensive tour..."
```

当前提示词让 LLM 判断"是否同一句子/段落"，LLM 看到两者都包含 "Large Language Models" 相关内容，判断为语义相关 → **merge=true**。

但实际语义关系是：**块1是引用A的结束署名，块2是引用B的开始正文**——这是两个完全独立的语义单元。

### 当前 LLM 提示词的问题

阅读 [semantic\_analyzer.py](file:///Users/chunju/work/pdfTrans/modules/semantic_analyzer.py#L284-L441) 中的 `_generate_batch_semantic_analysis_prompt`：

**现有分析标准：**

1. 语义连贯性：两个块是否表达同一个完整的语义单元或句子
2. 语法完整性：前一个块是否是不完整的句子
3. 逻辑关系：是否存在紧密的逻辑联系
4. 标题识别：任一是标题则不合并
5. 列表开头：块2是列表开头则不合并
6. 多列表项：两个都是列表项则不合并
7. 列表项延续：前一个列表项，后一个是延续则合并

**缺失的关键能力：**

1. ❌ **无签名行/署名行识别**：不知道 `—Name, Role, Org` 是引用结束标志
2. ❌ **无引用边界识别**：无法区分"引用正文结束"和"新引用开始"
3. ❌ **无语义角色理解**：不理解文本在文档中的结构角色（正文 vs 署名 vs 标题 vs 列表）
4. ❌ **示例不足**：few-shot 示例中没有签名行、引用边界等场景

### 为什么不用硬编码规则替代

硬编码 `is_signature_line()` 方案存在以下问题：

1. **模式覆盖不全**：不同 PDF 的署名格式差异大（有无 em-dash、名字格式、职位表述等）
2. **维护成本高**：每发现新的边界类型就需要新增规则
3. **误判风险**：`—` 开头的可能是列表项、装饰线、破折号句等
4. **违背 LLM 设计初衷**：既然已经使用 LLM 做语义分析，应该让 LLM 学会识别这些边界，而非绕过它

**正确做法**：增强 LLM 提示词，让它具备识别各种语义边界的能力。

## What Changes

**已完成的修改（Task 1-7）：**

* 为 TextBlock 增加 alignment 属性 + 对齐检测 + 合并逻辑对齐检查 + PDF 生成使用对齐（阶段1-2 已解决）

**本次修改（Task 8-9）：改进 LLM 语义合并提示词**

* 重写 `_generate_batch_semantic_analysis_prompt` 和 `_generate_semantic_analysis_prompt`

* 新增**语义边界类型教育**：签名行/署名行、引用边界、独立结构元素

* 新增**语义角色判断**：让 LLM 先识别每个文本块的语义角色，再判断是否合并

* 新增**边界场景 few-shot 示例**：签名行+引用正文、列表项边界、标题边界等

* 移除硬编码 `is_signature_line()` 方案，改用 LLM 智能识别

## Impact

* Affected code:

  * `modules/semantic_analyzer.py` — **重写 LLM 提示词**（核心修改）

  * `modules/aiping_semantic_analyzer.py` — 如果有独立提示词也需要同步修改

* 行为变更：LLM 将正确识别签名行、引用边界等语义分界点，不再跨引用合并

* 影响范围：所有使用 LLM 语义合并的 PDF 页面（特别是包含书评、引用、署名的页面）

## ADDED Requirements

### Requirement: TextBlock 增加对齐方式属性

系统 SHALL 为 `TextBlock` 类增加 `alignment` 属性，取值为 0（左对齐）、1（居中）、2（右对齐），默认值为 0。

#### Scenario: 新建 TextBlock 默认左对齐

* **WHEN** 创建 TextBlock 对象时未指定 alignment

* **THEN** alignment 默认为 0（左对齐）

### Requirement: 提取阶段检测文本块对齐方式

系统 SHALL 在文本块提取阶段，基于文本块 bbox 与页面宽度的位置关系检测对齐方式，**检测优先级为左/右对齐优先于居中**：

1. 左对齐：文本左边缘（x0）距页面左边缘 < 页面宽度的 15%
2. 右对齐：文本右边缘（x1）距页面右边缘 < 页面宽度的 15%
3. 居中：文本中心与页面中心偏移 < 页面宽度的 15%，**且不满足上述左/右对齐条件**
4. 其他：左对齐（默认）

**理由**：书籍页面布局通常左右对称（左右边距相近），导致左对齐和右对齐文本的区域中心都接近页面中心。如果居中检测优先，所有文本都会被误判为居中。先检查左/右边缘对齐，再检查居中，可以正确区分左对齐、右对齐和真正的居中文本。

#### Scenario: 右对齐正文块被正确检测

* **WHEN** 文本块 bbox 为 (350, 100, 550, 120)，页面宽度为 595pt

* **AND** 页面右边缘 595 - x1(550) = 45pt < 595 \* 15% = 89.25pt

* **THEN** alignment = 2（右对齐）

#### Scenario: 左对齐标题块被正确检测

* **WHEN** 文本块 bbox 为 (50, 100, 400, 120)，页面宽度为 595pt

* **AND** 文本左边缘 x0(50) < 595 \* 15% = 89.25pt

* **THEN** alignment = 0（左对齐）

#### Scenario: 居中文本块被正确检测

* **WHEN** 文本块中心 x = 297.5，页面中心 x = 297.5

* **AND** 偏移 < 页面宽度 \* 15%

* **AND** 文本左边缘距页面左边缘 > 15%，右边缘距页面右边缘 > 15%

* **THEN** alignment = 1（居中）

#### Scenario: 左右对称布局中左对齐标题不被误判为居中

* **WHEN** 文本块 bbox 为 (73.12, 139.54, 430.88, 163.5)，页面宽度为 504pt

* **AND** 文本中心 = 252.0，页面中心 = 252.0，center\_offset = 0.000（满足居中条件）

* **AND** 文本左边缘 x0(73.12) / 504 = 0.145 < 0.15（满足左对齐条件）

* **THEN** alignment = 0（左对齐，左对齐优先于居中）

#### Scenario: 左右对称布局中右对齐正文不被误判为居中

* **WHEN** 文本块 bbox 为 (89.24, 215.25, 432.0, 264.87)，页面宽度为 504pt

* **AND** 文本中心 = 260.62，页面中心 = 252.0，center\_offset = 0.017（满足居中条件）

* **AND** 页面右边缘 504 - x1(432.0) = 72.0，72.0 / 504 = 0.143 < 0.15（满足右对齐条件）

* **THEN** alignment = 2（右对齐，右对齐优先于居中）

### Requirement: 语义合并逻辑阻止不同对齐方式的块合并

系统 SHALL 在 `merge_semantic_blocks`、`merge_semantic_blocks_with_llm` 和 `merge_semantic_blocks_with_llm_two_phase` 中，当当前合并块与待合并块的对齐方式不同时，不进行合并。

对齐方式判断基于合并块中第一个原始块的 alignment 值。

**理由**：对齐方式变化是语义边界的信号。不同对齐方式的文本（如左对齐标题 vs 右对齐引用）语义角色不同，翻译时 LLM 更可能调整语序或合并重复内容，导致按比例拆分失败。

#### Scenario: 左对齐标题不与右对齐正文合并

* **WHEN** 当前合并块第一个原始块 alignment=0（左对齐，标题）

* **AND** 待合并块 alignment=2（右对齐，正文）

* **THEN** 不合并，结束当前合并块，开始新的合并块

#### Scenario: 相同对齐方式的块可以合并

* **WHEN** 当前合并块第一个原始块 alignment=2（右对齐）

* **AND** 待合并块 alignment=2（右对齐）

* **AND** 满足其他合并条件（垂直相邻等）

* **THEN** 可以合并

#### Scenario: 居中标题与左对齐正文不合并

* **WHEN** 当前合并块第一个原始块 alignment=1（居中，标题）

* **AND** 待合并块 alignment=0（左对齐，正文）

* **THEN** 不合并

### Requirement: PDF 生成使用检测到的对齐方式

系统 SHALL 在 `pdf_generator.py` 中使用 TextBlock 的 `alignment` 属性渲染翻译文本，替代硬编码的 `alignment = 0`。

#### Scenario: 右对齐文本块翻译后保持右对齐

* **WHEN** 原始文本块 alignment=2（右对齐）

* **THEN** 翻译文本以右对齐方式渲染

#### Scenario: 左对齐文本块翻译后保持左对齐

* **WHEN** 原始文本块 alignment=0（左对齐）

* **THEN** 翻译文本以左对齐方式渲染

### Requirement: 改进 LLM 语义合并提示词——增强边界识别能力

系统 SHALL 重写 `semantic_analyzer.py` 中的 `_generate_batch_semantic_analysis_prompt` 和 `_generate_semantic_analysis_prompt`，让 LLM 具备识别各种语义边界的能力。

#### 新增核心分析维度：语义角色判断

在原有的"语义连贯性、语法完整性"基础上，新增**两步分析法**：

**第一步：识别每个文本块的语义角色（Semantic Role）**

| 语义角色                   | 特征                         | 合并行为                |
| ---------------------- | -------------------------- | ------------------- |
| **正文 (body)**          | 完整句子或段落片段，描述具体内容           | 可与相邻正文合并            |
| **标题 (title)**         | 短语/简短句子，概括性、引导性            | 不与正文合并              |
| **签名行/署名 (signature)** | 以 `—`/`--` 开头 + 人名 + 职位/机构 | **独立语义单元，不与前不与后合并** |
| **列表项 (list\_item)**   | 以 `•`/`-`/`*`/数字+`.` 开头    | 不与新列表项合并，但可与自身续行合并  |
| **引用正文 (quote\_body)** | 引用/推荐的具体内容                 | 可与同引用内的正文合并，不跨引用合并  |

**第二步：基于语义角色判断是否合并**

```
合并决策矩阵（块1角色 × 块2角色）：

              块2=正文  块2=标题  块2=签名  块2=列表项
块1=正文      [判断]   不合     不合     [判断]
块1=标题      不合     [判断]   不合     不合
块1=签名      不合     不合     不合     不合
块1=列表项    [续行?]  不合     不合     不合

[判断] = 进一步检查语义连贯性和语法完整性
[续行?] = 检查是否为同一列表项的续行
不合 = 直接返回 merge=false
```

#### 提示词中必须包含的边界场景示例

**示例 A：签名行边界（核心修复场景）**

```
输入：
对K:
块1: "—Jay Alammar, coauthor, Hands-On Large Language Models"
块2: "Designing Large Language Model Applications is a comprehensive tour of LLMs"

输出：merge: false
理由：块1是引用署名行（signature），标志引用A结束；块2是新引用B的正文。两者属于不同引用，不应合并。
```

**示例 B：同一引用内正文可合并**

```
输入：
对L:
块1: "systems. It builds toward a powerful synthesis of advanced methods"
块2: "like tool use, reasoning, RAG, and fine-tuning"

输出：merge: true
理由：块1以小写字母开头的延续（"like"），是前一句的语法延续，属于同一引用同一句。
```

**示例 C：列表项边界**

```
输入：
对M:
块1: "• Understand how to prepare datasets for LLM training"
块2: "• Develop an intuition about the Transformer architecture"

输出：merge: false
理由：两个都是独立的列表项开头（都以 • 开头），每个列表项是独立的语义单元。
```

**示例 D：列表项续行应合并**

```
输入：
对N:
块1: "• Context to guide reasoning defines the agent's fundamental"
块2: "reasoning patterns and available actions"

输出：merge: true
理由：块2以小写字母 "r" 开头，是块1列表项内容的续行。
```

**示例 E：标题与正文边界**

```
输入：
对O:
块1: "Praise for Designing Large Language Model Applications"
块2: "Designing Large Language Model Applications is a masterclass in building AI"

输出：merge: false
理由：块1是页面标题（短、概括性），块2是引用正文的开始。标题和正文不应合并。
```

#### Scenario: 签名行后新引用不被合并

* **WHEN** LLM 收到文本对 `("—Jay Alammar, coauthor, Hands-On...", "Designing Large Language Model Applications is a comprehensive...")`

* **THEN** LLM 返回 `merge: false`，并在推理中识别出块1为签名行、块2为新引用正文

#### Scenario: 同一引用内句子延续正确合并

* **WHEN** LLM 收到文本对 `("systems. It builds toward a powerful synthesis", "of advanced methods like tool use...")`

* **THEN** LLM 返回 `merge: true`，识别出块2是块1的语法延续

#### Scenario: 列表项之间不合并

* **WHEN** LLM 收到文本对 `("• Understand how to prepare datasets", "• Develop an intuition about the Transformer")`

* **THEN** LLM 返回 `merge: false`，识别出两者都是独立列表项

#### Scenario: 标题后正文不合并

* **WHEN** LLM 收到文本对 `("Praise for Designing Large Language Model Applications", "Designing Large Language Model Applications is a masterclass...")`

* **THEN** LLM 返回 `merge: false`，识别出块1为标题

### Requirement: 同步修改 aiping\_semantic\_analyzer 提示词

经检查，`AipingSemanticAnalyzer`（[aiping\_semantic\_analyzer.py](file:///Users/chunju/work/pdfTrans/modules/aiping_semantic_analyzer.py)）继承自 `SemanticAnalyzer` 基类，**未重写** `_generate_semantic_analysis_prompt` 和 `_generate_batch_semantic_analysis_prompt` 方法。它仅重写了 API 调用方式（使用流式调用 + `config.AIPING_EXTRA_BODY`）。

**结论**：只需修改基类 [semantic\_analyzer.py](file:///Users/chunju/work/pdfTrans/modules/semantic_analyzer.py) 中的两个提示词生成方法，`AipingSemanticAnalyzer` 自动继承新提示词，无需额外修改。

## MODIFIED Requirements

### Requirement: 批量语义分析提示词（已修改）

系统的批量语义分析提示词 SHALL 从"仅判断是否同一句子"升级为"先识别语义角色再判断合并"，新增签名行/署名行、引用边界、列表边界等边界类型的识别能力。

### 阶段4（当前问题）：split\_translated\_result 的"分段长度平衡调整"破坏文本顺序

`split_translated_result()` 在按比例拆分后，有一个"分段长度平衡调整"步骤（L660-709），当最后一个块长度 > 平均长度 × 1.5 时，会从最后一个块尾部提取"多余"文本，**均匀分配到前面各个块**，直接破坏了文本顺序。

#### 日志证据（运行 `87cc0a28`，合并块75，6个原始块）

```text
调整前各块长度: [38, 163, 65, 168, 298, 266]
平均长度: 166.3, 最大长度: 298

块6(266) > 166.3 × 1.5 = 249.5 → 触发重新分配

从块6提取99字符: "Abdullah Al-hayali、Zach Nguyen、...精神支持，并经常检查我是否获得了足够的睡眠。"
均匀分配到块1-5，每块约19字符

调整后各块长度: [58, 183, 85, 188, 317, 167]
```

**这直接导致了语序混乱：**

* 块1 本来是 "他们常说...大都市" → 追加了 "Abdullah Al-hayali、Z" ← **朋友感谢名单被塞到了段落开头**

* 块3 本来是 "Kristen Brown...Amber Teng，hasin、Sadegh Raeisi和" → **比例拆分已经错位，又被追加了更多错误内容**

**问题本质**：这个"平衡调整"假设文本是均匀分布的，可以任意截取和重新分配。但对于跨段落合并的翻译文本，不同段落的字符密度差异很大，把最后一个块尾部的语义完整文本硬塞到前面各块中，必然破坏语义顺序。

#### 修复方向

**移除"分段长度平衡调整"步骤**。理由：

1. 按比例拆分已经尽量匹配原始块长度，再"平衡"只会破坏语义
2. 这个调整基于"文本均匀分布"的错误假设
3. 对于跨段落合并的情况，各块长度本来就不应该均匀
4. 没有任何场景需要这个调整——如果拆分比例正确，各块长度自然与原始块匹配

### 阶段5（当前问题）：LLM 提示词中 few-shot 示例和规则描述仅适用于英文

当前两个提示词方法中的 few-shot 示例（A-F）全部使用英文文本，规则描述也有英文特化痕迹。当源语言不是英文时（如中文、日语、韩语、法语、德语等），LLM 缺少对应语言的示例参考，判断准确性可能下降。

#### 具体问题

1. **示例全是英文**：6个 few-shot 示例（签名行边界、引用内合并、标题边界、列表项边界、列表续行、段落边界）全部使用英文文本
2. **规则描述有英文特化**：

   * "以大写字母开头" — 中文/日文没有大小写概念

   * "以小写字母开头" — 同上

   * "以 `—` 或 `--` 开头" — 英文书签名行风格，其他语言可能有不同格式
3. **签名行特征** — "人名 + 职位/机构"是西方格式，中日韩等语言可能使用不同格式

#### 修复方向

1. **根据** **`source_lang`** **动态选择示例语言**：当源语言是英文时使用英文示例，其他语言时使用对应语言的示例（或使用通用示例）
2. **规则描述改为语言无关**：将"大写字母/小写字母"改为"新句子开头/句子延续"等通用描述
3. **签名行特征扩展**：增加不同语言的签名行格式描述

