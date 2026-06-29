# 修复 DeepSeek-OCR 追加简短英文语言提示 Spec

## Why

spec `fix-deepseek-ocr-lang-hint-500-error` 将 `lang_hint`（含藏文字符 །༔༄༅、༠-༩ 等）插入 `<|grounding|>` 之前，仍然返回 HTTP 500 错误。表明问题不在 lang_hint 的位置，而在 lang_hint 中的**藏文 Unicode 字符**本身——DeepSeek-OCR 的服务端 tokenizer/解析器无法处理 prompt 中包含的藏文字符。

日志证据（旧版代码 20:52 运行成功）：
```
<image>\n<|grounding|>Convert the document to markdown. Only transcribe text actually visible in the image. Do not repeat the same phrase. Output length must match the visible text amount.
```
该 prompt 在 `Convert the document to markdown.` 之后追加了**纯英文**短语，**HTTP 200 成功**。仅因英文短语含"不要重复"指令导致模型回显，但 API 请求本身是成功的。

结论：在 `Convert the document to markdown.` 之后追加**纯英文**（不含藏文字符）是安全的。

## What Changes

- `modules/ocr/llm_extractor.py` **新增 `_build_short_english_hint()` 方法**: 根据 `source_lang` 返回简短纯英文语言提示（仅 ASCII 字符），无匹配时返回空字符串
- `modules/ocr/llm_extractor.py` **DeepSeek-OCR 分支**: 改为调用 `_build_short_english_hint()`，将结果追加到 `DEEPSEEK_OCR_PROMPT` 之后（即 `Convert the document to markdown.` 之后），格式 `f"{DEEPSEEK_OCR_PROMPT} {short_hint}"`
- `modules/ocr/llm_extractor.py` **VLM 分支**: 保持现有 `_build_lang_hint()` 中文注入逻辑不变（VLM 支持任意 Unicode 文本）
- **不修改** `_build_lang_hint` 方法（VLM 分支仍在使用）
- **不修改** 参数修改、`DEEPSEEK_OCR_PROMPT` 常量、`bo_to_zh.py` OCR 规则

## Impact

- Affected specs:
  - `fix-deepseek-ocr-lang-hint-500-error` — 替换其 DeepSeek-OCR 分支的 lang_hint 注入方式
  - `fix-llm-ocr-tibetan-penalty-regression` — DeepSeek-OCR 分支不再使用中文 lang_hint
- Affected code:
  - `modules/ocr/llm_extractor.py` — 新增 `_build_short_english_hint()` 方法，修改 DeepSeek-OCR 分支

## ADDED Requirements

### Requirement: DeepSeek-OCR 模式追加简短纯英文语言提示

系统 SHALL 在 DeepSeek-OCR 模式下，根据 `source_lang` 构建简短纯英文语言提示（仅 ASCII 字符），追加到 `DEEPSEEK_OCR_PROMPT` 之后。

#### Scenario: source_lang 为藏文时构建提示

- **WHEN** 模型名称包含 "deepseek-ocr"（`use_deepseek_prompt=True`）且 `source_lang="bo"`
- **THEN** 调用 `_build_short_english_hint()` 返回简短英文提示
- **AND** 提示内容 SHALL 为 `"For Tibetan: keep full line bbox width, preserve Tibetan numerals and punctuation, retain ||| separators."`
- **AND** 提示内容仅包含 ASCII 字符（不含藏文 Unicode）
- **AND** `user_text` 格式为 `f"{DEEPSEEK_OCR_PROMPT} {short_hint}"`
- **AND** 最终格式为 `"<image>\n<|grounding|>Convert the document to markdown. For Tibetan: keep full line bbox width, preserve Tibetan numerals and punctuation, retain ||| separators."`

#### Scenario: source_lang 无匹配时构建提示

- **WHEN** 模型名称包含 "deepseek-ocr"（`use_deepseek_prompt=True`）且 `source_lang` 无匹配的英文提示
- **THEN** `_build_short_english_hint()` 返回空字符串
- **AND** `user_text` 等于 `DEEPSEEK_OCR_PROMPT`（原生格式，不追加）

#### Scenario: DeepSeek-OCR 请求不再返回 500

- **WHEN** 使用 DeepSeek-OCR 模型调用 Qianfan API，且追加纯英文语言提示
- **THEN** API 请求 SHALL 成功返回（HTTP 200）
- **AND** 不再出现 `InternalServerError: Error code: 500`

### Requirement: `_build_short_english_hint` 方法

系统 SHALL 在 `LlmOcrExtractor` 类中新增 `_build_short_english_hint(self) -> str` 方法，根据 `source_lang` 返回简短纯英文语言提示。

#### Scenario: 藏文语言提示

- **WHEN** `self.source_lang == "bo"`
- **THEN** 返回 `"For Tibetan: keep full line bbox width, preserve Tibetan numerals and punctuation, retain ||| separators."`

#### Scenario: 未知语言

- **WHEN** `self.source_lang` 不在支持的映射中
- **THEN** 返回空字符串 `""`

### Requirement: VLM 模式保持现有 lang_hint 注入

系统 SHALL 在 VLM 模式（非 DeepSeek-OCR）下继续使用 `_build_lang_hint()` 加载中文语言专项规则。

#### Scenario: VLM 模式构建 user 消息

- **WHEN** 模型名称不包含 "deepseek-ocr"（`use_deepseek_prompt=False`）
- **THEN** 调用 `_build_lang_hint()` 获取中文语言专项规则
- **AND** user 消息文本格式为 `f"{lang_hint}请提取第{page_num}页PDF中的所有文字、表格和图表信息。"`
- **AND** system 消息为 `VLM_JSON_SYSTEM_PROMPT`

## MODIFIED Requirements

### Requirement: `_extract_page` DeepSeek-OCR 分支 prompt 构建

**原行为**（spec `fix-deepseek-ocr-lang-hint-500-error` 引入，仍然 500 错误）:
```python
if use_deepseek_prompt:
    lang_hint = self._build_lang_hint()
    if lang_hint:
        user_text = f"<image>\n{lang_hint}<|grounding|>Convert the document to markdown."
    else:
        user_text = DEEPSEEK_OCR_PROMPT
```

**新行为**:
```python
if use_deepseek_prompt:
    # DeepSeek-OCR 原生格式：在指令后追加简短纯英文语言提示
    # （不含藏文 Unicode 字符，避免服务端 tokenizer 解析失败）
    short_hint = self._build_short_english_hint()
    if short_hint:
        user_text = f"{DEEPSEEK_OCR_PROMPT} {short_hint}"
    else:
        user_text = DEEPSEEK_OCR_PROMPT
```

## Implementation Notes

- **根因**：DeepSeek-OCR 服务端 tokenizer 无法处理 prompt 中的藏文 Unicode 字符（། ༔ ༄༅ ༠-༩ 等），导致 500 错误。与位置无关（插入 `<|grounding|>` 之前也失败）。
- **解决方案**：使用纯英文提示（仅 ASCII 字符），避免藏文字符出现在 prompt 中。
- **旧版验证**：旧版 prompt `<image>\n<|grounding|>Convert the document to markdown. Only transcribe...` 成功（HTTP 200），证明在 `markdown.` 之后追加纯英文是安全的。
- **简短提示内容**：从 `bo_to_zh.py` 的 5 条藏文 OCR 规则中提取关键点，压缩成一句简短英文：
  - "keep full line bbox width" — 对应规则 1（bbox 行宽）
  - "preserve Tibetan numerals and punctuation" — 对应规则 3、4（藏文数字、标点）
  - "retain ||| separators" — 对应规则 5（分隔符）
  - 规则 2（易混淆字形）因涉及藏文字符示例，不包含在英文提示中
- **VLM 分支不变**：VLM 模型（如 Qwen3-VL）支持任意 Unicode 文本，继续使用中文 lang_hint
- `_build_lang_hint` 方法保留，VLM 分支仍在使用
