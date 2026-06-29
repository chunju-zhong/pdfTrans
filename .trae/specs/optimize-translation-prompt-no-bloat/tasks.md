# Tasks

- [x] Task 1: 优化 `_generate_system_prompt` 方法，添加"禁止膨胀"和"忠实直译"规则
  - [x] SubTask 1.1: 在提示词开头添加"忠实直译"规则，明确禁止脑补、添加原文不存在的细节
  - [x] SubTask 1.2: 添加"禁止膨胀"规则，约束翻译长度与原文相当
  - [x] SubTask 1.3: 调整规则顺序，将核心约束（忠实直译、禁止膨胀）前置
  - [x] SubTask 1.4: 整合现有规则到"保持格式"大类，减少规则条数
  - [x] SubTask 1.5: 保持多语言支持，确保 `{source_lang_name}`、`{target_lang_name}`、`{doc_type}`、`{glossary}` 参数正确注入

- [x] Task 2: 编写测试验证优化后的提示词效果
  - [x] SubTask 2.1: 创建测试脚本，对比优化前后提示词的翻译效果
  - [x] SubTask 2.2: 测试多种文本类型（目录句式、教法论述、仪轨文）
  - [x] SubTask 2.3: 验证"禁止膨胀"规则生效，无编造作者、虚构别名等问题

# Task Dependencies
- Task 2 depends on Task 1