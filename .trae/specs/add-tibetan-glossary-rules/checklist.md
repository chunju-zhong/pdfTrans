# Checklist

- [x] `bo_to_zh.py` 中新增了 `task_type="glossary"` 的 `PromptRule`
- [x] glossary 规则包含藏文数字/编号处理规则
- [x] glossary 规则包含关键术语翻译对照表
- [x] glossary 规则包含复合词提取指导
- [x] glossary 规则包含过滤普通词汇的规则
- [x] glossary 规则正确设置 `source_lang="bo"`, `target_lang="*"`, `priority=200`
- [x] 当 `merge_into_prompt(prompt, "glossary", "bo", "zh")` 调用时，规则被正确追加
- [x] 当 `merge_into_prompt(prompt, "glossary", "en", "zh")` 调用时，藏文规则不被匹配（不影响其他语言）
- [x] glossary 提示词中使用语言名称（"藏文"）而非语言代码（"bo"）
- [x] `tests/test_tibetan_glossary.py` 测试文件存在且包含相关测试用例
- [x] 所有新增测试通过
