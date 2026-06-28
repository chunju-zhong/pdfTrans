# LLM OCR 追加原文档主要语言类型提示 Spec

## Why

LLM OCR 模块（DeepSeek-OCR 分支和 VLM 分支）的 prompt 中完全没有提示原文档的主要语言类型。模型不知道应该期待什么语言的文本，影响识别准确性——尤其对于藏文、日文、韩文等非拉丁字符集的文档，缺乏语言预期可能导致字形误判或编码丢失。

## What Changes

- `modules/ocr/llm_extractor.py` **新增模块级常量 `_SOURCE_LANG_ENGLISH_NAMES`**: 语言代码到英文名称的映射（zh→Chinese、en→English、bo→Tibetan 等 9 种语言）
- `modules/ocr/llm_extractor.py` **修改 `_build_short_english_hint()` 方法**: 在 `parts` 列表开头追加 `"The document is primarily in {english_name}."`（仅 ASCII，DeepSeek-OCR 安全）
- `modules/ocr/llm_extractor.py` **修改 VLM 分支 user_text**: 在 `lang_hint` 之后追加 `"该文档主要语言为{中文名称}。"`（来自 `config.SUPPORTED_LANGUAGES`）
- **不修改** DeepSeek-OCR 分支调用逻辑（仍为 `f"{DEEPSEEK_OCR_PROMPT} {short_hint}"`）
- **不修改** `_build_lang_hint()`、`bo_to_zh.py`、config.py

## Impact

- Affected specs:
  - `add-deepseek-ocr-no-repeat-hint` — 扩展其 `_build_short_english_hint()` 方法，在开头追加语言类型提示
  - `fix-deepseek-ocr-short-english-hint` — 同上
- Affected code:
  - `modules/ocr/llm_extractor.py` — 新增常量、修改 `_build_short_english_hint()`、修改 VLM 分支 user_text

## ADDED Requirements

### Requirement: DeepSeek-OCR 模式提示原文档主要语言类型（英文）

系统 SHALL 在 DeepSeek-OCR 模式下，根据 `source_lang` 在英文提示开头追加原文档主要语言类型提示 `"The document is primarily in {english_name}."`，其中 `{english_name}` 来自 `_SOURCE_LANG_ENGLISH_NAMES` 映射。

#### Scenario: source_lang 为藏文时构建提示

- **WHEN** 模型名称包含 "deepseek-ocr"（`use_deepseek_prompt=True`）且 `source_lang="bo"`
- **THEN** `_build_short_english_hint()` 返回 `"The document is primarily in Tibetan. For Tibetan: keep full line bbox width, preserve Tibetan numerals and punctuation, retain ||| separators. Do not repeat the same sentence."`
- **AND** 提示内容仅包含 ASCII 字符

#### Scenario: source_lang 为英文时构建提示

- **WHEN** 模型名称包含 "deepseek-ocr"（`use_deepseek_prompt=True`）且 `source_lang="en"`
- **THEN** `_build_short_english_hint()` 返回 `"The document is primarily in English. Do not repeat the same sentence."`

#### Scenario: source_lang 未知或为 None 时构建提示

- **WHEN** `source_lang` 不在 `_SOURCE_LANG_ENGLISH_NAMES` 中或为 None
- **THEN** 不追加语言类型提示，仅返回 `"Do not repeat the same sentence."`

### Requirement: VLM 模式提示原文档主要语言类型（中文）

系统 SHALL 在 VLM 模式下，根据 `source_lang` 在 user_text 中追加原文档主要语言类型提示 `"该文档主要语言为{中文名称}。"`，其中 `{中文名称}` 来自 `config.SUPPORTED_LANGUAGES`。

#### Scenario: VLM 模式 source_lang 为藏文

- **WHEN** 模型名称不包含 "deepseek-ocr"（`use_deepseek_prompt=False`）且 `source_lang="bo"`
- **THEN** user_text 格式为 `f"{lang_hint}该文档主要语言为藏文。请提取第{page_num}页PDF中的所有文字、表格和图表信息。"`

#### Scenario: VLM 模式 source_lang 未知或为 None

- **WHEN** `source_lang` 不在 `config.SUPPORTED_LANGUAGES` 中或为 None
- **THEN** 不追加语言前缀，user_text 保持原格式 `f"{lang_hint}请提取第{page_num}页PDF中的所有文字、表格和图表信息。"`

### Requirement: `_SOURCE_LANG_ENGLISH_NAMES` 常量

系统 SHALL 在 `modules/ocr/llm_extractor.py` 模块级新增 `_SOURCE_LANG_ENGLISH_NAMES` 字典，覆盖 `config.SUPPORTED_LANGUAGES` 中的所有 9 种语言。

#### Scenario: 映射覆盖所有支持语言

- **WHEN** 查询 `_SOURCE_LANG_ENGLISH_NAMES`
- **THEN** 包含以下键值对：`zh→Chinese`、`en→English`、`ja→Japanese`、`ko→Korean`、`fr→French`、`de→German`、`es→Spanish`、`ru→Russian`、`bo→Tibetan`

## MODIFIED Requirements

### Requirement: `_build_short_english_hint` 方法

**原行为**（spec `add-deepseek-ocr-no-repeat-hint` 引入）:
```python
def _build_short_english_hint(self) -> str:
    parts = []
    if self.source_lang == "bo":
        parts.append(
            "For Tibetan: keep full line bbox width, "
            "preserve Tibetan numerals and punctuation, "
            "retain ||| separators."
        )
    parts.append("Do not repeat the same sentence.")
    return " ".join(parts)
```

**新行为**:
```python
def _build_short_english_hint(self) -> str:
    parts = []
    # 提示原文档主要语言类型
    lang_name = _SOURCE_LANG_ENGLISH_NAMES.get(self.source_lang or '')
    if lang_name:
        parts.append(f"The document is primarily in {lang_name}.")
    if self.source_lang == "bo":
        parts.append(
            "For Tibetan: keep full line bbox width, "
            "preserve Tibetan numerals and punctuation, "
            "retain ||| separators."
        )
    parts.append("Do not repeat the same sentence.")
    return " ".join(parts)
```

### Requirement: VLM 分支 user_text 构建

**原行为**:
```python
else:
    lang_hint = self._build_lang_hint()
    user_text = f"{lang_hint}请提取第{page_num}页PDF中的所有文字、表格和图表信息。"
```

**新行为**:
```python
else:
    lang_hint = self._build_lang_hint()
    lang_name_zh = config.SUPPORTED_LANGUAGES.get(self.source_lang or '', '')
    lang_prefix = f"该文档主要语言为{lang_name_zh}。" if lang_name_zh else ''
    user_text = f"{lang_hint}{lang_prefix}请提取第{page_num}页PDF中的所有文字、表格和图表信息。"
```

## Implementation Notes

- **DeepSeek-OCR 安全性**：英文语言名称（Tibetan、Chinese、Japanese 等）均为 ASCII 字符，不会触发服务端 tokenizer 解析失败，与 `fix-deepseek-ocr-short-english-hint` 的纯 ASCII 约束一致。
- **VLM 分支用中文**：VLM 模型（如 Qwen3-VL）支持任意 Unicode，使用 `config.SUPPORTED_LANGUAGES` 的中文名称更自然。
- **`source_lang` 可能为 None**：使用 `self.source_lang or ''` 兜底，避免 KeyError。
- **常量位置**：`_SOURCE_LANG_ENGLISH_NAMES` 放在模块级，与 `DEEPSEEK_OCR_PROMPT`、`VLM_JSON_SYSTEM_PROMPT` 等常量一致。
