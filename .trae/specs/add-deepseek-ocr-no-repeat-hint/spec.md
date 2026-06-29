# DeepSeek-OCR 追加抑制重复输出提示 Spec

## Why

spec `fix-deepseek-ocr-short-english-hint` 已解决 500 错误（用户确认方案可行），但 DeepSeek-OCR 在某些页面会输出一大堆重复句子（如旧版日志第6页模型连续回显 "If the text is not visible, do not output. Output length must match the visible text amount." 多次）。需要在现有英文提示后追加一句简短英文指令，明确告诉模型不要输出重复句子。

## What Changes

- `modules/ocr/llm_extractor.py` **重构 `_build_short_english_hint()` 方法**：先构建语言专项提示（藏文等），再追加通用抑制重复提示
- 通用提示文案：`"Do not repeat the same sentence."`（仅 ASCII，简短陈述式）
- 藏文最终提示：`"For Tibetan: keep full line bbox width, preserve Tibetan numerals and punctuation, retain ||| separators. Do not repeat the same sentence."`
- 其他语言最终提示：`"Do not repeat the same sentence."`（通用提示对所有语言都追加）
- **不修改** DeepSeek-OCR 分支调用逻辑（仍为 `f"{DEEPSEEK_OCR_PROMPT} {short_hint}"`）
- **不修改** VLM 分支、`_build_lang_hint()`、`bo_to_zh.py`、config.py

## Impact

- Affected specs:
  - `fix-deepseek-ocr-short-english-hint` — 扩展其 `_build_short_english_hint()` 方法返回内容
- Affected code:
  - `modules/ocr/llm_extractor.py` — 仅修改 `_build_short_english_hint()` 方法体

## ADDED Requirements

### Requirement: DeepSeek-OCR 模式追加通用抑制重复输出提示

系统 SHALL 在 DeepSeek-OCR 模式下，无论 `source_lang` 为何值，都在英文提示末尾追加通用抑制重复输出指令 `"Do not repeat the same sentence."`。

#### Scenario: source_lang 为藏文时构建提示

- **WHEN** 模型名称包含 "deepseek-ocr"（`use_deepseek_prompt=True`）且 `source_lang="bo"`
- **THEN** `_build_short_english_hint()` 返回 `"For Tibetan: keep full line bbox width, preserve Tibetan numerals and punctuation, retain ||| separators. Do not repeat the same sentence."`
- **AND** 提示内容仅包含 ASCII 字符
- **AND** `user_text` 格式为 `f"{DEEPSEEK_OCR_PROMPT} {short_hint}"`

#### Scenario: source_lang 为其他值时构建提示

- **WHEN** 模型名称包含 "deepseek-ocr"（`use_deepseek_prompt=True`）且 `source_lang` 不是 `"bo"`
- **THEN** `_build_short_english_hint()` 返回 `"Do not repeat the same sentence."`
- **AND** `user_text` 格式为 `f"{DEEPSEEK_OCR_PROMPT} {short_hint}"`

#### Scenario: DeepSeek-OCR 输出不再包含大量重复句子

- **WHEN** 使用 DeepSeek-OCR 模型调用 Qianfan API，且 prompt 包含 `"Do not repeat the same sentence."` 提示
- **THEN** 模型输出 SHALL 不再出现同一句子连续重复多次的情况
- **AND** API 请求 SHALL 成功返回（HTTP 200，不因追加指令导致 500）

## MODIFIED Requirements

### Requirement: `_build_short_english_hint` 方法

**原行为**（spec `fix-deepseek-ocr-short-english-hint` 引入）:
```python
def _build_short_english_hint(self) -> str:
    if self.source_lang == "bo":
        return (
            "For Tibetan: keep full line bbox width, "
            "preserve Tibetan numerals and punctuation, "
            "retain ||| separators."
        )
    return ''
```

**新行为**:
```python
def _build_short_english_hint(self) -> str:
    parts = []
    if self.source_lang == "bo":
        parts.append(
            "For Tibetan: keep full line bbox width, "
            "preserve Tibetan numerals and punctuation, "
            "retain ||| separators."
        )
    # 通用提示：抑制模型输出大量重复句子
    parts.append("Do not repeat the same sentence.")
    return " ".join(parts)
```

## Implementation Notes

- **设计依据**：旧版日志（20:52 第6页）显示 DeepSeek-OCR 在 grounding 模式下可能将 prompt 中的指令当作生成模板回显，导致同一句子重复多次。追加明确的"Do not repeat"陈述式指令可抑制此行为。
- **通用追加**：`"Do not repeat the same sentence."` 对所有语言都是良性的 OCR 质量要求，不限于藏文，因此放在通用部分而非藏文分支内。
- **安全性**：当前 spec `fix-deepseek-ocr-short-english-hint` 已验证纯英文追加不会触发 500 错误；本 spec 仅在同一位置追加另一句纯英文，预期同样安全。
- **陈述式文案选择**：使用陈述式 `"Do not repeat the same sentence."` 而非条件式 `"If the text is not visible, do not output."`，避免模型把条件式指令当作生成模板回显（旧版日志的回显正源于条件式指令）。
- **不影响 VLM 分支**：VLM 模式继续使用 `_build_lang_hint()` 加载中文规则，不受本变更影响。
