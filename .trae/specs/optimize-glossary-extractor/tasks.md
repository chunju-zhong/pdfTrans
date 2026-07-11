# PDF翻译工具 - 术语提取器代码优化实现计划

## [x] Task 1: 拆分 extract_glossary() 函数
- **Priority**: high
- **Depends On**: None
- **Description**: 
  - 将 `extract_glossary()` 函数中的提示词构建逻辑提取为 `_build_prompt()` 方法
  - 将 API 调用逻辑提取为 `_call_api()` 方法
  - 将响应处理逻辑提取为 `_process_response()` 方法
  - 确保每个方法不超过50行
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `programmatic` TR-1.1: `extract_glossary()` 函数行数不超过50行
  - `programmatic` TR-1.2: `_build_prompt()`、`_call_api()`、`_process_response()` 方法各不超过50行
  - `programmatic` TR-1.3: 所有现有测试通过
- **Notes**: 保持原有逻辑不变，仅做代码结构优化

## [x] Task 2: 提取重复的提示词规则为常量
- **Priority**: high
- **Depends On**: Task 1
- **Description**: 
  - 将提示词模板中重复的"核心要求"规则提取为模块级常量
  - 将其他重复规则提取为常量
  - 修改 `_build_prompt()` 方法，通过拼接常量构建提示词
- **Acceptance Criteria Addressed**: AC-2
- **Test Requirements**:
  - `programmatic` TR-2.1: 提示词模板中不存在重复的"核心要求"文本
  - `programmatic` TR-2.2: 所有提示词常量定义在模块级别或类级别
  - `programmatic` TR-2.3: 所有现有测试通过
- **Notes**: 确保优化后的提示词内容与原提示词完全一致

## [x] Task 3: 提取藏文术语对照表为共享常量
- **Priority**: medium
- **Depends On**: None
- **Description**: 
  - 在 `prompts/language_rules/bo_to_zh.py` 中提取术语对照表为模块级常量 `TIBETAN_TERMINOLOGY_MAP`
  - 修改翻译规则和术语提取规则，复用该常量
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `programmatic` TR-3.1: `bo_to_zh.py` 中存在 `TIBETAN_TERMINOLOGY_MAP` 常量
  - `programmatic` TR-3.2: 翻译规则和术语提取规则均引用该常量
  - `programmatic` TR-3.3: 所有现有测试通过
- **Notes**: 确保术语对照表内容与原内容完全一致

## [x] Task 4: 运行测试验证
- **Priority**: high
- **Depends On**: Task 1, Task 2, Task 3
- **Description**: 
  - 运行术语提取器相关测试
  - 运行翻译器相关测试
  - 确认所有测试通过，无回归
- **Acceptance Criteria Addressed**: AC-4
- **Test Requirements**:
  - `programmatic` TR-4.1: `pytest tests/test_glossary_extractor.py` 通过
  - `programmatic` TR-4.2: `pytest tests/test_translator.py` 通过
  - `programmatic` TR-4.3: `pytest tests/test_bo_translate.py` 通过（如有）
- **Notes**: 确保优化后的代码行为与原代码完全一致
