# Tasks

- [x] Task 1: 统一 format_blocks 输入块标记格式
  - [x] SubTask 1.1: 在 [modules/translator.py](file:///Users/chunju/work/pdfTrans/modules/translator.py) 的 `format_blocks` 方法中，把输入块构造从 `f"--- 块{i+1} ---\n{text}\n\n"` 改为 `f"---块{i+1}---\n{text}\n\n"`（移除 `块` 与数字两侧空格）
  - [x] SubTask 1.2: 确认新格式 `---块N---` 与 `_FORMAT_SYSTEM_PROMPT` 中指示的输出标记格式字符完全相同
  - [x] SubTask 1.3: 不改动 `blocks_text = "".join(parts)` 拼接逻辑与 user prompt 的其余部分（user prompt 文本在 Task 3 修改）

- [x] Task 2: 重写 _FORMAT_SYSTEM_PROMPT 消除指令矛盾并增加 few-shot 样例
  - [x] SubTask 2.1: 把"输出每个块前必须以 `---块N---` 标记开头"作为靠前的、独立的硬性输出格式要求
  - [x] SubTask 2.2: 移除"不要输出任何解释、元标记或格式标记"中"格式标记"一词，改为"不要输出解释、注释、备注、思考过程"
  - [x] SubTask 2.3: 在输出格式说明后追加一个简短的 few-shot 输入→输出样例，展示 `---块N---` 标记在输出中的正确位置与回显语义
  - [x] SubTask 2.4: 保留核心原则（只做格式排版优化、不新增内容、不修改正确文本、空块输出空字符串、不确定时保持不变）语义不变，仅调整措辞顺序与强度

- [x] Task 3: 在 format_blocks 的 user prompt 中明确输入标记语义
  - [x] SubTask 3.1: 修改 `format_blocks` 的 user_prompt，在请求文本之前或之中增加说明："输入中的 `---块N---` 标记是结构分隔符，输出时必须为每个块保留对应编号的标记，不得剥离"
  - [x] SubTask 3.2: 保持 user_prompt 的请求主体（输入块文本）结构不变

- [x] Task 4: 为 _parse_format_result 增加缺标记时的行级回退
  - [x] SubTask 4.1: 在 [modules/translator.py](file:///Users/chunju/work/pdfTrans/modules/translator.py) 的 `_parse_format_result` 方法中，当 `len(parts) < 3`（缺标记）时，先按非空行分割 `result_text`，取前 `expected_count` 行作为回退结果
  - [x] SubTask 4.2: 仅当行级回退后行数与 `expected_count` 不符时，才输出"缺少 ---块N--- 标记"警告并返回 `["fallback_invalid_format"]`
  - [x] SubTask 4.3: 行级回退成功时不输出警告（避免噪音），让 `format_blocks` 直接接受结果

- [x] Task 5: 更新与新增测试覆盖
  - [x] SubTask 5.1: 在 [tests/test_translator.py](file:///Users/chunju/work/pdfTrans/tests/test_translator.py) 中新增/更新 `_parse_format_result` 测试用例：缺标记但行数匹配时返回正确数量；缺标记且行数不匹配时返回长度 1 的回退标记
  - [x] SubTask 5.2: 新增 `format_blocks` 输入块构造的测试，断言输入标记格式为 `---块N---`（无空格）
  - [x] SubTask 5.3: 确认现有 `format_blocks` 流式调用、计数校验、异常回退相关测试仍通过

# Task Dependencies

- Task 3 依赖 Task 1（输入标记格式统一后，user prompt 的标记语义说明才有意义）
- Task 5 依赖 Task 1、Task 2、Task 3、Task 4 完成
- Task 1、Task 2、Task 4 相互独立，可并行
