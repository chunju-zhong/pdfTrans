# Checklist

- [x] `format_blocks` 输入块构造使用 `---块N---` 格式（无空格），与 prompt 指示的输出标记格式字符完全相同
- [x] `_FORMAT_SYSTEM_PROMPT` 把"输出每个块前必须以 `---块N---` 标记开头"作为靠前的、独立的硬性输出格式要求
- [x] `_FORMAT_SYSTEM_PROMPT` 不再包含"不要输出...格式标记...（除了 ---块N---）"这类自相矛盾的措辞
- [x] `_FORMAT_SYSTEM_PROMPT` 中"不要输出"的禁用项改为"解释、注释、备注、思考过程"，不再含"格式标记"
- [x] `_FORMAT_SYSTEM_PROMPT` 或 user prompt 包含一个 few-shot 输入→输出样例，展示 `---块N---` 标记在输出中的正确位置
- [x] `format_blocks` 的 user prompt 明确说明输入 `---块N---` 标记是结构分隔符，输出时必须为每个块保留对应编号的标记
- [x] `_parse_format_result` 在缺 `---块N---` 标记时先尝试按非空行分割回退，行数与期望匹配时返回正确数量且不输出警告
- [x] `_parse_format_result` 在缺标记且行级回退后行数仍不匹配时，才输出警告并返回 `["fallback_invalid_format"]`
- [x] `format_blocks` 的流式调用逻辑、计数校验位置、异常回退语义保持不变
- [x] `format_blocks` 的函数签名、返回值结构、`_get_format_api_kwargs` 钩子保持不变
- [x] 新增/更新的 `_parse_format_result` 测试用例通过（缺标记行数匹配 / 缺标记行数不匹配）
- [x] 新增的 `format_blocks` 输入块构造测试通过（断言 `---块N---` 无空格）
- [x] 现有 `format_blocks` 流式调用、计数校验、异常回退相关测试仍通过
- [x] 翻译主流程 `_generate_system_prompt` 未被改动（由 `fix-format-prompt-toc-line-collapse` spec 负责）
- [x] `services/translation_content.py` 调用方逻辑未被改动
