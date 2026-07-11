# 动态 max_tokens 优化 Spec

## Why
项目中 LLM API 调用的 max_tokens 全部使用固定值，不随输入长度调整。当输入仅 208 字符时，翻译 API 仍有 8192 tokens 输出空间，导致 LLM 可生成 11 分钟的垃圾重复输出。按输入动态限定 max_tokens 可以从源头防止垃圾输出、节省 API 费用、加速响应。

## What Changes
- 在翻译器基类中添加 `_calculate_max_tokens` 方法，按输入长度动态计算
- 翻译（3 个子类）、format_blocks、Markdown 生成三个场景使用动态 max_tokens
- format_blocks 的硬编码 4096 改为走配置+动态计算
- 语义分析、术语提取、LLM OCR 保持固定 max_tokens（输出为固定格式或输入为图像，不适合动态计算）

## Impact
- Affected code: `modules/translator.py`（基类添加动态计算方法）
- Affected code: `modules/aiping_translator.py`、`modules/silicon_flow_translator.py`、`modules/qianfan_translator.py`（translate 方法）
- Affected code: `modules/markdown_generator.py`（两个 _generate_markdown 方法）
- Affected specs: `fix-translation-garbage-output-fallback`（互补：本 spec 是预防，那个 spec 是兜底检测）

## 不做动态计算的场景及原因

| 模块 | 当前值 | 原因 |
|------|--------|------|
| 语义分析（单条） | 1024 | 输出是固定格式 JSON `{"merge": true/false}`，1024 已是合理天花板 |
| 语义分析（批量） | 2048 | 输出是布尔数组 JSON，2048 已有充足余量 |
| 术语提取 | 4096 | 输入已截断为 5000 字符，输出量可预期 |
| LLM OCR | 8000 | 输入是图像而非文本，无法用字符数估算 tokens |

## ADDED Requirements

### Requirement: 动态 max_tokens 计算方法
系统 SHALL 在翻译器基类中提供 `_calculate_max_tokens(input_text, max_ceiling=None)` 方法，根据输入文本长度动态计算合理的 max_tokens。

计算规则：
- 估算输入 token 数：`estimated_tokens = len(input_text) / CHARS_PER_TOKEN`
- `CHARS_PER_TOKEN = 3`（英文约 4 字符/token，中文约 2 字符/token，取中值 3）
- 动态值：`dynamic = max(MIN_OUTPUT_TOKENS, int(estimated_tokens × EXPANSION_FACTOR))`
- `MIN_OUTPUT_TOKENS = 256`（确保短文本也有足够输出空间）
- `EXPANSION_FACTOR = 3`（允许译文最多为输入的 3 倍 token 数，覆盖翻译膨胀场景）
- 上限：`min(dynamic, max_ceiling or self.max_tokens)`

#### Scenario: 短输入（208 字符，如分词器示例代码）
- **WHEN** 输入 208 字符，估算约 69 tokens
- **THEN** dynamic_max_tokens = max(256, 69×3) = max(256, 207) = 256
- **THEN** LLM 最多输出 256 tokens，而非 8192

#### Scenario: 中等输入（2000 字符）
- **WHEN** 输入 2000 字符，估算约 667 tokens
- **THEN** dynamic_max_tokens = max(256, 667×3) = max(256, 2001) = 2001

#### Scenario: 长输入（10000 字符）
- **WHEN** 输入 10000 字符，估算约 3333 tokens
- **THEN** dynamic_max_tokens = min(max(256, 3333×3), 8192) = min(9999, 8192) = 8192
- **THEN** 达到全局上限，行为与当前一致

### Requirement: 翻译 translate 方法使用动态 max_tokens
系统 SHALL 在三个翻译器子类（AipingTranslator、SiliconFlowTranslator、QianfanTranslator）的 translate 方法中，使用 `self._calculate_max_tokens(text)` 替代固定的 `self.max_tokens`。

#### Scenario: 翻译短文本块
- **WHEN** 翻译 208 字符的文本块
- **THEN** API 调用使用 max_tokens=256

#### Scenario: 翻译长文本块
- **WHEN** 翻译 8000+ 字符的文本块
- **THEN** API 调用使用 max_tokens=8192（全局上限）

### Requirement: format_blocks 使用动态 max_tokens
系统 SHALL 在 format_blocks 方法中使用动态计算的 max_tokens，替代当前硬编码的 4096。动态值上限为 `config.LAYOUT_MAX_TOKENS`（默认 8192），不再硬编码。

#### Scenario: format_blocks 短输入
- **WHEN** format_blocks 输入文本估算 tokens × 3 < 8192
- **THEN** 使用动态计算的较小值

#### Scenario: format_blocks 长输入
- **WHEN** format_blocks 输入文本估算 tokens × 3 ≥ 8192
- **THEN** 使用 8192 作为上限

### Requirement: Markdown 生成使用动态 max_tokens
系统 SHALL 在 MarkdownGenerator 的两个 _generate_markdown 方法中，使用动态计算的 max_tokens，替代固定的 `self.max_tokens`。

#### Scenario: Markdown 生成短页内容
- **WHEN** 一页翻译块内容较短
- **THEN** 使用动态计算的较小 max_tokens

#### Scenario: Markdown 生成长页内容
- **WHEN** 一页翻译块内容较长
- **THEN** 使用 8192 作为上限

## MODIFIED Requirements

### Requirement: 翻译器 max_tokens 使用方式
将翻译器 `__init__` 中 `self.max_tokens = config.TRANSLATION_MAX_TOKENS` 的用法从"直接用于每次调用"改为"仅作为上限"，每次翻译调用时通过 `self._calculate_max_tokens(input_text)` 动态计算实际值。
