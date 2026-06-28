# 修复 LLM OCR 藏文重复输出与超长生成 Spec

## Why

使用 Qianfan 调用 DeepSeek-OCR 模型对藏文 PDF 第 8 页进行 OCR 时，模型陷入重复循环，生成 7399 tokens（接近 8192 上限）几乎全部是重复短语 `གུ་རུ་དཔྲན་རྒྱལ་པོའི་གསང་སྒྲུབ་ལ་ལྡེབ་གཉིས། ༤༨༽` 等的循环，最终输出 6319 字符的"假识别"文本。第 9 页同样问题（completion=7399 tokens），第 10 页（completion=797 tokens）正常。

这导致下游翻译收到一份由幻觉重复组成的"原文"，既浪费 token 又让翻译质量毫无意义（翻译一份根本不存在的重复内容）。日志已记录 `finish_reason=length` 警告但未采取任何纠正措施。

## 根因分析

### 时间线还原（来自 app.log）

```
16:05:24 - LLM OCR第8页尺寸: 页面=1191.0x231.8pt, 图像=2482x483px（窄长横版页）
16:06:05 - 第8页Token使用: prompt=793, completion=7399, total=8192（命中上限）
16:06:05 - 第8页OcrBlock映射结果: 1个文本块（6319字符藏文，含大量重复）
```

第 8 页 OCR 响应内容节选（来自日志第 100 行原文）：
```
... གུ་རུ་དཔྲན་རྒྱལ་པོའི་གསང་སྒྲུབ་ལ་ལྡེབ་གཉིས། ༤༨༽
   གུ་རུ་དཔྲན་རྒྱལ་པོའི་གསང་སྒྲུབ་ལ་ལྡེབ་གཉིས། ༤༨༽
   གུ་རུ་དཔྲན་རྒྱལ་པོའི་གསང་སྒྲུབ་ལ་ལྡེབ་གཉིས། ༤༨༽
   ...（同一短语重复数十次）...
```

第 9 页（日志第 104 行）同样重复 `གུ་རུ་རྣོ་རྗེ་ཁྲོ་ལོད་ཀྱི་སྒྲུབ་པ་ལ་ལྡེབ་གཉིས། ༥༥༡` 数十次。

### 根因 1：模型参数缺失防重复控制

文件：`modules/ocr/llm_extractor.py:383-388`

```python
response = self.client.chat.completions.create(
    model=model_name,
    messages=messages,
    temperature=config.OCR_LLM_TEMPERATURE,    # 0.1（过低，倾向于重复）
    max_tokens=effective_max_tokens,           # 8000（远超窄页实际所需）
)
```

- **未设置 `frequency_penalty`**：OpenAI 兼容 API 默认 `frequency_penalty=0`，对已出现 token 无惩罚，模型可无限重复同一短语
- **未设置 `presence_penalty`**：默认 `0`，对已出现 token 不增加使用新词的倾向
- **`temperature=0.1` 过低**：低温使模型过于确定性，对低资源语言（藏文 token 化效率低、训练数据少）极易陷入局部最优的重复循环
- **`max_tokens=8000` 过高**：对窄横版页（483px 高，实际文本量小）允许生成 7399 tokens 完全无必要，反而放大重复伤害

对比 OpenAI 官方文档建议：处理易重复场景应使用 `frequency_penalty=0.3~0.6` + `temperature=0.3~0.5`。

### 根因 2：DeepSeek-OCR prompt 过于简洁，无防重复/防幻觉指导

文件：`modules/ocr/llm_extractor.py:36`

```python
DEEPSEEK_OCR_PROMPT = "<image>\n<|grounding|>Convert the document to markdown."
```

- 仅 5 个英文单词 + 2 个标签，未告诉模型：
  - 仅识别图像中实际可见的文字，不要根据上下文编造或推断
  - 不要重复同一短语
  - 输出长度应与图像实际文字量匹配

### 根因 3：藏文 OCR 专项规则缺少防重复指导

文件：`prompts/language_rules/bo_to_zh.py:103-123`

现有规则覆盖：bbox 行宽、易混淆字形、藏文数字、藏文标点。但完全没有：
- 防止重复识别同一短语
- 强调只识别图像中可见内容
- 输出长度合理范围提示

### 根因 4：`finish_reason=length` 仅告警未纠正

文件：`modules/ocr/llm_extractor.py:397-401`

```python
if finish_reason == 'length':
    logger.warning(
        f"第{page_num}页LLM OCR响应被截断（finish_reason=length），"
        f"当前输出={len(result_text)}字符，可考虑增大OCR_LLM_MAX_TOKENS"
    )
```

- 检测到 `length` 截断仅打印 warning
- 日志建议"增大 max_tokens"——这恰恰是反方向建议，长输出本身已是问题，增大上限只会让重复更严重
- 没有触发任何后处理：未做重复检测、未做去重、未标记该页 OCR 质量可疑

### 根因 5：无 OCR 后处理去重逻辑

文件：`modules/ocr/llm_extractor.py`、`modules/ocr/llm_response_parser.py`

- OCR 响应直接交由 parser 解析为 `TextBlock`
- 没有"检测连续 N 个相同短语则折叠为 1 个"的去重逻辑
- 没有"输出长度与图像像素面积比例异常"的合理性检查

> **本次范围说明**：后处理去重逻辑不在本次 spec 范围内，留待后续独立 spec 处理。本次通过参数与 prompt 调优从源头抑制重复。

## What Changes

- 在 `chat.completions.create` 调用中新增 `frequency_penalty`、`presence_penalty` 参数（可通过环境变量配置）
- 将 `OCR_LLM_MAX_TOKENS` 默认值从 8000 降至 4096（窄页足够，限制重复伤害）
- 将 `OCR_LLM_TEMPERATURE` 默认值从 0.1 提升至 0.3（避免低资源语言陷入重复局部最优）
- 在 `DEEPSEEK_OCR_PROMPT` 中新增防重复、防幻觉指导
- 在藏文 OCR 专项规则中新增防重复条目
- 修正 `finish_reason=length` 日志建议方向（从"增大 max_tokens"改为"检查输出是否含重复"）

## Impact

- Affected specs:
  - `fix-llm-ocr-tibetan-recognition` — 该 spec 已修复藏文识别（英文幻觉 → 藏文输出），本 spec 在其基础上修复"识别出藏文但内容重复"
  - `diagnose-glm4v-tibetan-retry` — 该 spec 已修复 LLM OCR 超时（120s → 300s），与本 spec 正交
  - `add-llm-ocr-extra-body-provider` — 该 spec 增加 `extra_body` 配置，与本 spec 正交
- Affected code:
  - `modules/ocr/llm_extractor.py` — `chat.completions.create` 新增参数、`finish_reason=length` 日志修正
  - `config.py` — 新增 `OCR_LLM_FREQUENCY_PENALTY`、`OCR_LLM_PRESENCE_PENALTY` 配置项；修改 `OCR_LLM_MAX_TOKENS`、`OCR_LLM_TEMPERATURE` 默认值
  - `.env.example` — 新增环境变量说明
  - `prompts/language_rules/bo_to_zh.py` — 藏文 OCR 规则新增防重复条目

## ADDED Requirements

### Requirement: LLM OCR 调用支持防重复惩罚参数

`LlmOcrExtractor._extract_page` 的 `chat.completions.create` 调用 SHALL 传递 `frequency_penalty` 和 `presence_penalty` 参数，值从 `config.OCR_LLM_FREQUENCY_PENALTY`（默认 0.3）和 `config.OCR_LLM_PRESENCE_PENALTY`（默认 0.2）读取。

#### Scenario: 默认防重复参数生效
- **WHEN** 用户未设置 `OCR_LLM_FREQUENCY_PENALTY` 和 `OCR_LLM_PRESENCE_PENALTY` 环境变量
- **THEN** `chat.completions.create` 调用包含 `frequency_penalty=0.3`、`presence_penalty=0.2`
- **AND** 藏文页面 OCR 不再陷入重复循环

#### Scenario: 用户自定义防重复参数
- **WHEN** 用户设置 `OCR_LLM_FREQUENCY_PENALTY=0.6`
- **THEN** 调用使用 0.6 作为 `frequency_penalty`

### Requirement: finish_reason=length 日志建议方向修正

`LlmOcrExtractor._extract_page` 中 `finish_reason == 'length'` 的 warning 日志 SHALL 不再建议"增大 max_tokens"，改为建议"检查输出是否含重复短语、调整 frequency_penalty"。

#### Scenario: 响应被截断
- **WHEN** `finish_reason == 'length'`
- **THEN** 日志输出形如：`第N页LLM OCR响应被截断（finish_reason=length），当前输出=X字符，请检查输出是否含重复短语，或调高 OCR_LLM_FREQUENCY_PENALTY`

### Requirement: DeepSeek-OCR prompt 增加防重复指导

`DEEPSEEK_OCR_PROMPT` SHALL 在原有 markdown 转换指令后追加防重复、防幻觉的明确指导。

#### Scenario: DeepSeek-OCR 模型调用
- **WHEN** 使用 DeepSeek-OCR 模型
- **THEN** prompt 包含以下要点（英文，与原 prompt 风格一致）：
  - "Only transcribe text actually visible in the image"
  - "Do not repeat the same phrase"
  - "Output length must match the visible text amount"

### Requirement: 藏文 OCR 专项规则新增防重复条目

`prompts/language_rules/bo_to_zh.py` 的 OCR 规则 SHALL 新增以下条目：
- 仅识别图像中实际可见的藏文字符，不要根据上下文编造或推断
- 不要重复输出同一短语（即使图像中确实有相似内容，每条应只输出一次）
- 输出长度应与图像实际文字量匹配，避免无意义的重复填充

## MODIFIED Requirements

### Requirement: OCR_LLM_MAX_TOKENS 默认值

`config.OCR_LLM_MAX_TOKENS` 默认值 SHALL 从 `8000` 修改为 `4096`。

#### Scenario: 用户未配置
- **WHEN** 用户未设置 `OCR_LLM_MAX_TOKENS` 环境变量
- **THEN** 使用默认值 `4096`
- **AND** 窄横版页（如 483px 高）OCR 不再生成 7399 tokens 的重复内容

### Requirement: OCR_LLM_TEMPERATURE 默认值

`config.OCR_LLM_TEMPERATURE` 默认值 SHALL 从 `0.1` 修改为 `0.3`，避免低资源语言陷入重复局部最优。

#### Scenario: 用户未配置
- **WHEN** 用户未设置 `OCR_LLM_TEMPERATURE` 环境变量
- **THEN** 使用默认值 `0.3`

## REMOVED Requirements

（无）
