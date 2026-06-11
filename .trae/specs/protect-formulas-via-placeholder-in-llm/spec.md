# 通过占位符替换保护 MD 公式不被 LLM 损坏 Spec

## Why

即使公式已正确用 `$$...$$` 包裹，`_format_with_layout_model` 将包含公式的完整文本送入 LLM 进行布局格式化。LLM 可能在处理过程中修改、拆分、重排或损坏公式的 LaTeX 内容（如剥离 `\mathsf`、`\mathrm`、`\frac` 等命令，或添加多余空格/格式），导致公式在 Markdown 渲染器中无法正确显示。

## What Changes

在 `_format_with_layout_model` 中增加占位符替换机制：

1. **发送前**：从文本中提取所有 `$$...$$`（独立行）和 `$...$`（行内）公式块，替换为唯一占位符（如 `__FORMULA_0__`、`__FORMULA_1__`）
2. **发送**：将替换后的文本（不含真实 LaTeX）送入 LLM 格式化
3. **接收后**：在 LLM 返回结果中，将占位符替换回原始公式内容

## Impact

- Affected code: `modules/markdown_generator.py`（`_format_with_layout_model` 方法）
- 行为变更：LLM 完全不会接触到公式 LaTeX 内容，无法损坏公式

## ADDED Requirements

### Requirement: 占位符替换保护

系统 SHALL 在将文本送入 LLM 布局格式化前，提取所有公式内容并替换为唯一占位符，格式化完成后恢复。

#### Scenario: 独立行公式（`$$...$$`）

- **WHEN** 输入文本包含 `$$E=mc^2$$`
- **THEN** 提取为 `__FORMULA_N__`，LLM 收到的是占位符
- **THEN** LLM 返回后，`__FORMULA_N__` 恢复为 `$$E=mc^2$$`

#### Scenario: 行内公式（`$...$`）

- **WHEN** 输入文本包含 `这是 $E=mc^2$ 公式`
- **THEN** 提取为 `这是 __FORMULA_N__ 公式`
- **THEN** LLM 返回后恢复

#### Scenario: 无公式

- **WHEN** 输入文本不含任何 `$...$` 或 `$$...$$`
- **THEN** 行为不变，不进行替换操作

#### Scenario: 嵌套/regex 边界

- **WHEN** 文本包含 `$$...$$` 内部的 `$` 或 `\$$`
- **THEN** 优先匹配最外层 `$$...$$`，再匹配 `$...$`

## MODIFIED Requirements

### Requirement: `_format_with_layout_model` 增加占位符替换

```python
def _format_with_layout_model(self, text):
    import re
    logger.info("使用布局模型格式化文本为Markdown")
    
    # 1. 提取并替换公式占位符
    formula_placeholders = {}
    placeholder_idx = 0
    
    # 先替换独立行公式 $$...$$，再替换行内公式 $...$
    def replace_display_formula(m):
        nonlocal placeholder_idx
        key = f'__FORMULA_{placeholder_idx}__'
        formula_placeholders[key] = m.group(0)
        placeholder_idx += 1
        return key
    
    def replace_inline_formula(m):
        nonlocal placeholder_idx
        key = f'__FORMULA_{placeholder_idx}__'
        formula_placeholders[key] = m.group(0)
        placeholder_idx += 1
        return key
    
    # 独立行公式优先（避免被行内公式误匹配）
    text_with_placeholders = re.sub(r'\$\$(.+?)\$\$', replace_display_formula, text, flags=re.DOTALL)
    text_with_placeholders = re.sub(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', replace_inline_formula, text_with_placeholders)
    
    # 2. 构建含占位符的用户提示词
    system_prompt = self._load_layout_prompt()
    user_prompt = f"请将以下内容转换为Markdown格式：\n\n{text_with_placeholders}"
    
    # 3. 调用 LLM（原有重试逻辑）
    ...
    
    # 4. 恢复公式内容
    formatted_text = markdown_result.content
    for placeholder, original_formula in formula_placeholders.items():
        formatted_text = formatted_text.replace(placeholder, original_formula)
    
    # 更新 markdown_result.content
    markdown_result.content = formatted_text
    return markdown_result
```

## REMOVED Requirements

无
