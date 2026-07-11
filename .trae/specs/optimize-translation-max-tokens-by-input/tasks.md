# Tasks

- [x] Task 1: 在 `modules/translator.py` 基类中添加 `_calculate_max_tokens` 方法
  - [x] SubTask 1.1: 定义类常量 `CHARS_PER_TOKEN=3`, `EXPANSION_FACTOR=3`, `MIN_OUTPUT_TOKENS=256`
  - [x] SubTask 1.2: 实现 `_calculate_max_tokens(self, input_text, max_ceiling=None)`：估算输入 tokens，计算 `max(MIN_OUTPUT_TOKENS, int(estimated_tokens × EXPANSION_FACTOR))`，不超过 `max_ceiling or self.max_tokens`
  - [x] SubTask 1.3: 添加 DEBUG 日志记录估算 tokens 和计算出的 max_tokens

- [x] Task 2: 修改三个翻译器子类的 translate 方法
  - [x] SubTask 2.1: `modules/aiping_translator.py`：`max_tokens=self.max_tokens` → `max_tokens=self._calculate_max_tokens(text)`
  - [x] SubTask 2.2: `modules/silicon_flow_translator.py`：同样替换
  - [x] SubTask 2.3: `modules/qianfan_translator.py`：同样替换

- [x] Task 3: 修改 `format_blocks` 方法
  - [x] SubTask 3.1: `modules/translator.py`：`max_tokens=4096` → `max_tokens=self._calculate_max_tokens(blocks_text, max_ceiling=config.LAYOUT_MAX_TOKENS)`

- [x] Task 4: 修改 MarkdownGenerator 的两个 _generate_markdown 方法
  - [x] SubTask 4.1: 将 `_calculate_max_tokens` 方法提取为独立函数 `calculate_max_tokens`（供 MarkdownGenerator 使用）
  - [x] SubTask 4.2: 基类 `MarkdownGenerator._call_api`：使用动态 max_tokens
  - [x] SubTask 4.3: `AipingMarkdownGenerator._call_api`：同样使用动态 max_tokens

# Task Dependencies

- Task 2, 3, 4 依赖 Task 1
- Task 4.2, 4.3 依赖 Task 4.1
