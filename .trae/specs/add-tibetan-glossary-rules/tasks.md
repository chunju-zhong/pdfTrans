# Tasks

- [x] Task 1: 在 `bo_to_zh.py` 中新增 `task_type="glossary"` 的 `PromptRule`
  - SubTask 1.1: 编写藏文术语提取专项规则文本，包含：
    - 藏文数字与编号处理（`༠-༩` 在术语中的处理）
    - 关键术语翻译对照表（复用 translation 规则中的核心术语对照表）
    - 复合词提取规则
    - 区分专业术语与普通藏语词汇的过滤规则
  - SubTask 1.2: 设置正确的匹配参数 `source_lang="bo"`, `target_lang="*"`, `priority=200`

- [x] Task 2: 优化 glossary 提示词的语言名称可读性
  - SubTask 2.1: 当前 glossary prompt 使用原始 language code（如 "bo"），改为使用语言名称（如 "藏文"）
  - SubTask 2.2: 在 `glossary_extractor.py` 中添加语言代码→语言名称的映射，或从 config 读取

- [x] Task 3: 新增藏文术语提取测试用例
  - SubTask 3.1: 创建 `tests/test_tibetan_glossary.py`，包含：
    - 模拟 LLM 响应，验证规则被正确拼入提示词
    - 藏文佛教术语提取场景的 mock 测试（验证格式正确性）
    - 普通藏文文本（无术语）场景的 mock 测试
  - SubTask 3.2: 运行测试验证通过

# Task Dependencies
- Task 2 依赖于 Task 1（但逻辑独立，可并行）
- Task 3 依赖于 Task 1（需要规则就绪后才能测试）
