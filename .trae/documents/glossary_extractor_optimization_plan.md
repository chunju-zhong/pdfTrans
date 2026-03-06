# 术语提取器优化计划

## 任务分解和优先级

### [x] 任务1：修改AipingGlossaryExtractor提示词
- **优先级**：P0
- **依赖**：无
- **描述**：
  - 修改AipingGlossaryExtractor类中的提示词，将原来的空字符串要求改为返回"NO_GLOSSARY"标识
  - 确保提示词清晰明确，强调在没有专业术语时返回"NO_GLOSSARY"

- **成功标准**：
  - 提示词中明确要求在没有专业术语时返回"NO_GLOSSARY"标识

- **测试要求**：
  - `programmatic` TR-1.1: 提示词中包含"NO_GLOSSARY"标识的要求

### [x] 任务2：修改SiliconFlowGlossaryExtractor提示词
- **优先级**：P0
- **依赖**：无
- **描述**：
  - 修改SiliconFlowGlossaryExtractor类中的提示词，将原来的空字符串要求改为返回"NO_GLOSSARY"标识
  - 确保提示词与AipingGlossaryExtractor保持一致

- **成功标准**：
  - 提示词中明确要求在没有专业术语时返回"NO_GLOSSARY"标识

- **测试要求**：
  - `programmatic` TR-2.1: 提示词中包含"NO_GLOSSARY"标识的要求

### [x] 任务3：修改AipingGlossaryExtractor的_format_glossary方法
- **优先级**：P0
- **依赖**：任务1
- **描述**：
  - 修改AipingGlossaryExtractor类的_format_glossary方法，添加对"NO_GLOSSARY"标识的处理
  - 当检测到"NO_GLOSSARY"标识时，返回空字符串

- **成功标准**：
  - 当输入包含"NO_GLOSSARY"时，方法返回空字符串

- **测试要求**：
  - `programmatic` TR-3.1: 输入"NO_GLOSSARY"时返回空字符串
  - `programmatic` TR-3.2: 输入正常术语时返回格式化后的术语表

### [x] 任务4：修改SiliconFlowGlossaryExtractor的_format_glossary方法
- **优先级**：P0
- **依赖**：任务2
- **描述**：
  - 修改SiliconFlowGlossaryExtractor类的_format_glossary方法，添加对"NO_GLOSSARY"标识的处理
  - 当检测到"NO_GLOSSARY"标识时，返回空字符串

- **成功标准**：
  - 当输入包含"NO_GLOSSARY"时，方法返回空字符串

- **测试要求**：
  - `programmatic` TR-4.1: 输入"NO_GLOSSARY"时返回空字符串
  - `programmatic` TR-4.2: 输入正常术语时返回格式化后的术语表

### [x] 任务5：创建测试脚本验证修改
- **优先级**：P1
- **依赖**：任务3、任务4
- **描述**：
  - 创建测试脚本，验证修改后的术语提取器在没有专业术语时返回空字符串
  - 测试不同场景：无专业术语、只有普通词汇、有专业术语

- **成功标准**：
  - 测试脚本能够正确验证修改后的功能
  - 无专业术语时返回空字符串
  - 有专业术语时正确提取术语

- **测试要求**：
  - `programmatic` TR-5.1: 无专业术语时返回空字符串 - 已通过
  - `programmatic` TR-5.2: 只有普通词汇时返回空字符串 - 已通过
  - `programmatic` TR-5.3: 有专业术语时正确提取术语 - 已通过

## 实施步骤

1. 修改AipingGlossaryExtractor的提示词
2. 修改SiliconFlowGlossaryExtractor的提示词
3. 修改AipingGlossaryExtractor的_format_glossary方法
4. 修改SiliconFlowGlossaryExtractor的_format_glossary方法
5. 创建并运行测试脚本验证修改

## 预期结果

- 当文本中没有专业术语时，术语提取器返回空字符串
- 当文本中有专业术语时，术语提取器正确提取并返回术语表
- 提示词清晰明确，强调在没有专业术语时返回"NO_GLOSSARY"标识
- 处理结果时正确去掉"NO_GLOSSARY"标识，返回空字符串
