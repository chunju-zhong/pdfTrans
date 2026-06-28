# 修复 DeepSeek-OCR lang_hint 注入导致 500 错误 Spec

## Why

spec `fix-llm-ocr-tibetan-penalty-regression` 中新增的 `_build_lang_hint` 方法将藏文 OCR 规则（含藏文字符 །༔༄༅、特殊符号 `|||`、Unicode 数字 ༠༡༢ 等）追加到 DeepSeek-OCR 原生 prompt **末尾**（`DEEPSEEK_OCR_PROMPT + lang_hint`），破坏了 `<|grounding|>` 特殊 token 之后的固定指令格式，导致 Qianfan API 服务端解析失败，返回 `openai.InternalServerError: Error code: 500`。

日志证据：
- **第一次运行（20:52，旧版代码无 lang_hint）**：第 6-10 页全部 HTTP 200 成功
- **第二次运行（22:00，新版代码 lang_hint 追加到末尾）**：第 6-10 页全部 HTTP 500 错误（OpenAI 客户端自动重试 2 次仍失败）

`<|grounding|>` 是 DeepSeek-OCR 的特殊 token，用于触发 grounding 模式（输出 `<|ref|>...<|/ref|><|det|>...<|/det|>` 格式）。在其后追加任意额外文本会破坏服务端对 grounding 输出格式的预期，导致确定性 500 错误。

## What Changes

- `modules/ocr/llm_extractor.py` **DeepSeek-OCR 分支**: 重排 prompt 结构，将 `lang_hint` 插入 `<image>` 和 `<|grounding|>` **之间**（而非追加到末尾），保持 `<|grounding|>Convert the document to markdown.` 原生指令不被破坏
- `modules/ocr/llm_extractor.py` **VLM 分支**: 保持现有 `lang_hint` 注入逻辑不变
- `modules/ocr/llm_extractor.py` **`_build_lang_hint` 方法**: 保留（DeepSeek-OCR 和 VLM 分支都在使用）
- **不修改** 参数修改（`temperature=0.1`、`max_tokens=8000`、`frequency_penalty=0.0`、`presence_penalty=0.0`）
- **不修改** `DEEPSEEK_OCR_PROMPT` 常量（保持原生格式作为无 lang_hint 时的 fallback）
- **不修改** `bo_to_zh.py` OCR 规则内容

## Impact

- Affected specs:
  - `fix-llm-ocr-tibetan-penalty-regression` — 修改其 DeepSeek-OCR 分支的 lang_hint 注入位置
- Affected code:
  - `modules/ocr/llm_extractor.py` — `_extract_page` 方法的 DeepSeek-OCR 分支

## ADDED Requirements

### Requirement: DeepSeek-OCR 模式将 lang_hint 插入 `<|grounding|>` 之前

系统 SHALL 在 DeepSeek-OCR 模式下，将语言专项规则（lang_hint）插入到 `<image>` 和 `<|grounding|>` 之间，保持 `<|grounding|>Convert the document to markdown.` 原生指令完整不被破坏。

#### Scenario: 有 lang_hint 时构建 user 消息

- **WHEN** 模型名称包含 "deepseek-ocr"（`use_deepseek_prompt=True`）且 `_build_lang_hint()` 返回非空字符串
- **THEN** user 消息的文本部分格式 SHALL 为 `f"<image>\n{lang_hint}<|grounding|>Convert the document to markdown."`
- **AND** `lang_hint` 位于 `<image>` 之后、`<|grounding|>` 之前
- **AND** `<|grounding|>Convert the document to markdown.` 保持原生格式不变
- **AND** messages 结构为单一 user 消息（含 image_url + text），不包含 system 消息

#### Scenario: 无 lang_hint 时构建 user 消息

- **WHEN** 模型名称包含 "deepseek-ocr"（`use_deepseek_prompt=True`）且 `_build_lang_hint()` 返回空字符串
- **THEN** user 消息的文本部分 SHALL 为 `DEEPSEEK_OCR_PROMPT`（即 `"<image>\n<|grounding|>Convert the document to markdown."`）
- **AND** 不插入任何额外文本

#### Scenario: DeepSeek-OCR 请求不再返回 500

- **WHEN** 使用 DeepSeek-OCR 模型调用 Qianfan API，且 lang_hint 插入 `<|grounding|>` 之前
- **THEN** API 请求 SHALL 成功返回（HTTP 200）
- **AND** 不再出现 `InternalServerError: Error code: 500`

### Requirement: VLM 模式保留现有 lang_hint 注入逻辑

系统 SHALL 在 VLM 模式（非 DeepSeek-OCR）下继续通过 `_build_lang_hint()` 加载语言专项规则并注入到 user 消息文本中（追加到 user 文本开头）。

#### Scenario: VLM 模式构建 user 消息

- **WHEN** 模型名称不包含 "deepseek-ocr"（`use_deepseek_prompt=False`）
- **THEN** 调用 `_build_lang_hint()` 获取语言专项规则
- **AND** user 消息文本格式为 `f"{lang_hint}请提取第{page_num}页PDF中的所有文字、表格和图表信息。"`
- **AND** system 消息为 `VLM_JSON_SYSTEM_PROMPT`

## MODIFIED Requirements

### Requirement: `_extract_page` DeepSeek-OCR 分支 prompt 构建

**原行为**（spec `fix-llm-ocr-tibetan-penalty-regression` 引入，导致 500 错误）:
```python
if use_deepseek_prompt:
    lang_hint = self._build_lang_hint()
    user_text = DEEPSEEK_OCR_PROMPT + lang_hint  # 追加到末尾，破坏 <|grounding|> 后的指令格式
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}},
                {"type": "text", "text": user_text}
            ]
        }
    ]
```

**新行为**:
```python
if use_deepseek_prompt:
    lang_hint = self._build_lang_hint()
    if lang_hint:
        # 将 lang_hint 插入 <image> 和 <|grounding|> 之间，保持
        # <|grounding|>Convert the document to markdown. 原生指令不被破坏
        user_text = f"<image>\n{lang_hint}<|grounding|>Convert the document to markdown."
    else:
        user_text = DEEPSEEK_OCR_PROMPT
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}},
                {"type": "text", "text": user_text}
            ]
        }
    ]
```

## Implementation Notes

- DeepSeek-OCR 的 prompt 格式 `<image>\n<|grounding|>Convert the document to markdown.` 中：
  - `<image>` 是图像占位符 token，标记图像位置
  - `<|grounding|>` 是特殊 token，触发 grounding 模式（输出带 `<|ref|>...<|/ref|><|det|>...<|/det|>` 坐标的格式）
  - `Convert the document to markdown.` 是固定指令
- **追加到末尾会 500**：在 `Convert the document to markdown.` 之后追加文本，破坏了服务端对 grounding 输出格式的预期
- **插入 `<|grounding|>` 之前应安全**：`<|grounding|>` 之前的文本被当作上下文/描述，不会被 grounding 解析器处理
- `lang_hint` 末尾自带 `\n\n`（由 `_build_lang_hint` 方法的 `return "\n".join(hint_parts) + "\n\n"` 保证），所以最终格式为：
  ```
  <image>\n【藏文OCR提取专项规则】\n\n1. ...\n2. ...\n...\n## 通用 OCR 规则...\n\n<|grounding|>Convert the document to markdown.
  ```
- VLM 模式（如 Qwen3-VL）使用标准 chat 格式，支持任意 user 文本和 system prompt，lang_hint 注入方式不变
- 参数修改和 DEEPSEEK_OCR_PROMPT 简化保持不变
