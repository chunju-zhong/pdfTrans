# 文档更新指南

## 1. 代码变更分析

### 1.1 变更识别

- 使用 `git status` 查看所有未提交的文件
- 使用 `git diff` 查看具体的代码变更内容
- 使用 `git diff --name-only` 列出所有变更的文件路径

### 1.2 变更类型分析

- **新功能添加**：新增模块、函数或功能
- **现有功能修改**：修改现有代码逻辑或参数
- **错误修复**：修复bug或异常处理
- **代码重构**：优化代码结构，不改变功能
- **性能优化**：改进代码执行效率
- **UI/UX改进**：优化用户界面或交互体验
- **配置变更**：修改配置参数或环境变量
- **依赖更新**：更新或添加依赖库

### 1.3 变更影响评估

- **功能影响**：哪些功能模块受到影响
- **文档影响**：哪些文档需要相应更新
- **测试影响**：哪些测试用例需要修改或添加
- **兼容性影响**：是否影响现有功能的兼容性

## 2. 文档更新范围

### 2.1 文档命名规范

项目文档采用中英双语命名规范：
- **中文版**：使用 `.zh.md` 后缀（如：`README.zh.md`、`docs/CHANGELOG.zh.md`）
- **英文版**：使用原始文件名（如：`README.md`、`docs/CHANGELOG.md`）

### 2.2 README.md 更新

#### 2.2.1 更新内容
- **功能描述**：添加新功能说明或更新现有功能描述
- **技术栈**：更新使用的技术栈和依赖库版本
- **使用指南**：更新用户使用方法和注意事项
- **配置说明**：更新配置参数和环境变量设置
- **开发记录**：添加最新的开发记录到单独的 CHANGELOG.md

#### 2.2.2 中文版更新规则

- **时间顺序**：开发记录必须按时间逆序排列（最新记录在前）
- **内容结构**：每条记录应包含变更日期、变更内容、影响和重要性
- **格式一致**：保持与现有记录的Markdown格式一致
- **语言清晰**：使用简洁明了的语言，避免技术术语堆砌
- **版本关联**：重要变更应关联到相应的版本号

#### 2.2.3 英文版更新规则

- **时间顺序**：开发记录必须按时间逆序排列（最新记录在前）
- **内容结构**：每条记录应包含变更日期、变更内容、影响和重要性
- **格式一致**：保持与现有记录的Markdown格式一致
- **语言清晰**：使用简洁明了的英语，避免中式英语
- **版本关联**：重要变更应关联到相应的版本号
- **翻译准确**：确保英文版内容与中文版一致，术语翻译准确

### 2.3 CHANGELOG.md 更新（推荐）

#### 2.3.1 文件位置

- 中文版路径：`docs/CHANGELOG.zh.md`
- 英文版路径：`docs/CHANGELOG.md`
- 当更新日志内容较多时，推荐使用单独的 CHANGELOG.md 文件

#### 2.3.2 更新内容

- **开发记录**：所有开发记录都添加到 CHANGELOG

#### 2.3.3 更新规则

- **时间顺序**：开发记录必须按时间逆序排列（最新记录在前）
- **内容结构**：每条记录应包含变更日期、变更内容、影响和重要性
- **格式一致**：保持与现有记录的Markdown格式一致
- **双语更新**：同时更新中文版和英文版，确保内容一致

#### 2.3.4 README.md 引用

- 在 README.zh.md 中保留更新日志章节，添加指向 docs/CHANGELOG.zh.md 的链接
- 在 README.md 中保留更新日志章节，添加指向 docs/CHANGELOG.md 的链接
- 示例：
  - 中文版：`项目更新日志已移动到单独的 [docs/CHANGELOG.zh.md](docs/CHANGELOG.zh.md) 文件中。`
  - 英文版：`The project changelog has been moved to a separate [docs/CHANGELOG.md](docs/CHANGELOG.md) file.`

### 2.4 AI开发进度更新

#### 2.4.1 文件路径

`.trae/documents/ai_dev_progress.md`

#### 2.4.2 更新时机

- **开发开始前**：记录当前状态、计划目标和预期成果
- **开发完成后**：记录实际完成情况、遇到的问题和解决方案

#### 2.4.3 记录内容

- **当前状态**：项目的最新进展和整体状态
- **已完成任务**：详细描述已完成的工作，包括具体修改的文件和功能
- **技术实现**：记录关键技术点和实现方法
- **变更影响**：分析变更对项目各方面的影响
- **遇到的问题**：记录开发过程中遇到的问题和解决方案
- **后续计划**：明确下一步的工作计划和目标

#### 2.4.4 更新规则

- **时间顺序**：开发记录必须按时间逆序排列（最新记录在前）
- **历史保留**：保留所有历史记录，不要删除旧内容
- **详细程度**：提供足够详细的信息，便于后续参考和追溯
- **格式统一**：保持与现有记录的结构和格式一致
- **客观准确**：真实反映开发情况，避免夸大或遗漏

#### 2.4.5 记录示例

```markdown
### 2026-02-07
- **当前状态**：已完成文本连续判断提示词优化和标题识别功能实现
- **已完成任务**：
  - 优化文本连续判断提示词：
    - 修改 `translator.py` 中的 `_generate_semantic_analysis_prompt` 方法
    - 添加明确的标题识别规则和语义特征描述
    - 提供详细的标题示例和非标题示例
  - 完善测试用例：
    - 在 `test_semantic_merge_extended.py` 中添加 `TestTitleRecognition` 类
    - 编写三个测试用例验证标题识别功能
- **技术实现**：
  - 使用语义分析方法识别标题
  - 通过详细的提示词指导LLM正确判断文本连续性
  - 采用对比示例帮助LLM理解标题特征
- **影响**：
  - 提高文本块合并准确性，特别是标题与正文的区分
  - 改善Markdown生成质量，确保标题格式正确
  - 增强用户体验，减少手动调整格式的需要
- **遇到的问题**：
  - 无重大问题，开发过程顺利
- **后续计划**：
  - 优化其他提示词，如测试用例更新和文档更新提示词
  - 完善更多测试场景，提高代码覆盖率
  - 改进用户界面，提升整体使用体验
```

### 2.5 TODO.md 更新

#### 2.5.1 文件路径

- 中文版路径：`docs/TODO.zh.md`
- 英文版路径：`docs/TODO.md`

#### 2.5.2 更新内容

- **任务添加**：为新功能或未完成的工作添加详细任务
- **任务更新**：更新现有任务的状态和描述
- **双语更新**：同时更新中文版和英文版

#### 2.5.3 更新规则

- **优先级排序**：按优先级高、中、低排序
- **状态标记**：使用适当的标记（如 \[ ]、\[x]）表示任务状态
- **任务描述**：清晰描述任务内容和目标
- **双语一致**：确保中英文版本的任务状态和描述一致

#### 2.5.4 更新示例

```markdown
# TODO List

## High Priority
- [x] Optimize text continuity judgment prompts
- [ ] Improve test coverage

## Medium Priority
- [ ] Improve user interface

## Low Priority
- [ ] Documentation improvement
```

### 2.6 项目技术文档更新

项目技术文档是 AI 和新开发人员理解项目全貌的核心参考资料，代码变更时必须同步更新。

#### 2.6.1 文件路径

| 文档 | 中文版路径 | 英文版路径 | 用途 |
|------|-----------|-----------|------|
| 架构文档 | `docs/ARCHITECTURE.zh.md` | `docs/ARCHITECTURE.md` | 项目整体架构、模块职责、数据流、数据模型、配置系统、外部依赖 |
| 技术方案文档 | `docs/TECHNICAL_GUIDE.zh.md` | `docs/TECHNICAL_GUIDE.md` | OCR 管线、翻译管线、语义合并、输出生成、公式处理、表格处理、错误处理等核心技术细节 |
| 开发指南文档 | `docs/DEVELOPMENT_GUIDE.zh.md` | `docs/DEVELOPMENT_GUIDE.md` | 环境搭建、配置说明、运行方式、CLI/Web API 参考、测试方法、开发任务指南、代码规范 |

#### 2.6.2 更新触发条件

以下代码变更必须同步更新对应的技术文档：

| 变更类型 | 需更新的文档 | 更新内容 |
|----------|-------------|---------|
| 新增/删除模块或文件 | ARCHITECTURE.zh.md / ARCHITECTURE.md | 目录结构说明、系统架构图 |
| 新增/修改数据模型字段 | ARCHITECTURE.zh.md / ARCHITECTURE.md | 关键数据模型及关系章节 |
| 新增/修改配置项 | ARCHITECTURE.zh.md / ARCHITECTURE.md、DEVELOPMENT_GUIDE.zh.md / DEVELOPMENT_GUIDE.md | 配置系统说明、.env 配置说明 |
| 新增/更换外部服务 | ARCHITECTURE.zh.md / ARCHITECTURE.md | 外部服务依赖章节 |
| OCR 管线变更 | TECHNICAL_GUIDE.zh.md / TECHNICAL_GUIDE.md | OCR 管线架构章节 |
| 翻译管线变更 | TECHNICAL_GUIDE.zh.md / TECHNICAL_GUIDE.md | 翻译管线架构章节 |
| 语义合并逻辑变更 | TECHNICAL_GUIDE.zh.md / TECHNICAL_GUIDE.md | 语义合并策略章节 |
| PDF/DOCX/Markdown 生成逻辑变更 | TECHNICAL_GUIDE.zh.md / TECHNICAL_GUIDE.md | 对应输出生成章节 |
| 表格处理逻辑变更 | TECHNICAL_GUIDE.zh.md / TECHNICAL_GUIDE.md | 表格处理管线章节 |
| 公式检测/渲染逻辑变更 | TECHNICAL_GUIDE.zh.md / TECHNICAL_GUIDE.md | 公式检测与渲染章节 |
| 错误处理/重试机制变更 | TECHNICAL_GUIDE.zh.md / TECHNICAL_GUIDE.md | 错误处理与重试机制章节 |
| 进度模型变更 | TECHNICAL_GUIDE.zh.md / TECHNICAL_GUIDE.md | 进度管理模型章节 |
| 术语表/章节识别变更 | TECHNICAL_GUIDE.zh.md / TECHNICAL_GUIDE.md | 术语表提取与章节识别章节 |
| CLI 命令参数变更 | DEVELOPMENT_GUIDE.zh.md / DEVELOPMENT_GUIDE.md | CLI 完整命令参考章节 |
| Web API 路由变更 | DEVELOPMENT_GUIDE.zh.md / DEVELOPMENT_GUIDE.md | Web API 接口参考章节 |
| 环境依赖变更 | DEVELOPMENT_GUIDE.zh.md / DEVELOPMENT_GUIDE.md | 环境要求与搭建章节 |
| 测试结构变更 | DEVELOPMENT_GUIDE.zh.md / DEVELOPMENT_GUIDE.md | 测试方法章节 |
| 新增支持语言 | DEVELOPMENT_GUIDE.zh.md / DEVELOPMENT_GUIDE.md、ARCHITECTURE.zh.md / ARCHITECTURE.md | 支持语言列表章节 |
| 新增设计模式或代码约定 | DEVELOPMENT_GUIDE.zh.md / DEVELOPMENT_GUIDE.md | 代码规范与约定章节 |

#### 2.6.3 更新规则

- **准确性优先**：文档内容必须与实际代码完全一致，不得有虚构或过时的描述
- **增量更新**：只更新受变更影响的章节，不需要重写整篇文档
- **交叉引用**：三份文档之间存在概念引用关系，更新一处时检查其他文档是否需要同步
  - ARCHITECTURE.zh.md / ARCHITECTURE.md 提供全局视图，TECHNICAL_GUIDE.zh.md / TECHNICAL_GUIDE.md 和 DEVELOPMENT_GUIDE.zh.md / DEVELOPMENT_GUIDE.md 引用其中的概念
  - 配置项变更需同时更新 ARCHITECTURE.zh.md / ARCHITECTURE.md（配置系统章节）和 DEVELOPMENT_GUIDE.zh.md / DEVELOPMENT_GUIDE.md（.env 配置章节）
- **验证方法**：更新后通过阅读源代码交叉验证文档描述的准确性
- **双语更新**：三份技术文档均有中文版（.zh.md）和英文版，变更时需同时更新两个版本

#### 2.6.4 更新示例

```markdown
### 示例：新增 OCR 引擎后的文档更新

1. ARCHITECTURE.zh.md / ARCHITECTURE.md 更新：
   - 目录结构：添加新引擎文件说明
   - 系统架构图：在核心模块层添加新引擎
   - 外部服务依赖：添加新引擎依赖的服务

2. TECHNICAL_GUIDE.zh.md / TECHNICAL_GUIDE.md 更新：
   - OCR 管线架构：添加新引擎的技术方案描述
   - 错误处理：添加新引擎的错误处理和重试机制

3. DEVELOPMENT_GUIDE.zh.md / DEVELOPMENT_GUIDE.md 更新：
   - .env 配置说明：添加新引擎相关配置项
   - CLI 命令参考：更新 --ocr-engine 参数的 choices
   - 开发任务指南：无需变更（已有"添加新 OCR 引擎"指南）
```

## 3. 文档更新流程

### 3.1 准备阶段

1. **收集变更信息**：使用git命令获取所有未提交的代码变更
2. **分析变更影响**：评估变更对功能、文档和测试的影响
3. **确定更新范围**：根据变更影响确定需要更新的文档

### 3.2 执行阶段

1. **更新 CHANGELOG**：
   - 将开发记录添加到 `docs/CHANGELOG.zh.md`（中文版）
   - 将开发记录添加到 `docs/CHANGELOG.md`（英文版）
2. **更新 README**：
   - 在 `README.zh.md` 中添加中文版链接
   - 在 `README.md` 中添加英文版链接
3. **更新 TODO**：
   - 在 `docs/TODO.zh.md` 中更新中文版
   - 在 `docs/TODO.md` 中更新英文版
4. **更新 AI 开发进度**：记录当前状态、已完成任务和后续计划
5. **更新项目技术文档**：根据变更类型更新 ARCHITECTURE.zh.md / ARCHITECTURE.md、TECHNICAL_GUIDE.zh.md / TECHNICAL_GUIDE.md、DEVELOPMENT_GUIDE.zh.md / DEVELOPMENT_GUIDE.md（参见 2.6.2 更新触发条件）

### 3.3 验证阶段

1. **格式检查**：确保文档格式正确，无Markdown语法错误
2. **内容验证**：确保文档内容与代码变更一致，无遗漏或错误
3. **顺序检查**：确保开发记录按时间逆序排列
4. **链接验证**：确保文档中的链接和引用正确有效
5. **双语检查**：确保中文版和英文版内容一致

### 3.4 提交阶段

1. **预览变更**：使用 `git diff` 查看所有文档变更
2. **提交说明**：编写清晰的提交信息，说明文档更新内容
3. **提交变更**：将文档更新与代码变更一起提交

## 4. 文档更新最佳实践

### 4.1 内容原则

- **及时性**：代码变更后立即更新文档，避免文档与代码不同步
- **准确性**：确保文档内容与实际代码行为完全一致
- **完整性**：覆盖所有重要的代码变更，不遗漏关键信息
- **简洁性**：使用简洁明了的语言，避免冗长和复杂的描述
- **一致性**：保持文档风格、格式和术语的一致性

### 4.2 结构原则

- **层次清晰**：使用适当的标题层级，组织内容结构
- **逻辑连贯**：内容排列逻辑清晰，便于理解和阅读
- **重点突出**：突出重要信息，使用列表、粗体等格式强调
- **示例充分**：提供足够的示例，帮助理解具体实现

### 4.3 维护原则

- **历史保留**：保留所有历史记录，便于追溯和参考
- **版本关联**：重要变更应关联到相应的版本号
- **定期审查**：定期审查文档，确保内容持续有效
- **用户反馈**：根据用户反馈持续改进文档质量
- **双语同步**：确保中文版和英文版同步更新

## 5. 验证清单

### 5.1 README验证

- [ ] 中文版（README.zh.md）和英文版（README.md）都已更新
- [ ] 开发记录按时间逆序排列
- [ ] 变更内容描述清晰完整
- [ ] 技术栈和依赖信息准确
- [ ] 格式正确，无语法错误
- [ ] 如使用CHANGELOG，链接引用正确有效

### 5.2 CHANGELOG验证

- [ ] 中文版（docs/CHANGELOG.zh.md）和英文版（docs/CHANGELOG.md）都已更新
- [ ] 开发记录按时间逆序排列
- [ ] 变更内容描述清晰完整
- [ ] 格式正确，无语法错误
- [ ] 中文版和英文版内容一致

### 5.3 AI开发进度验证

- [ ] 记录按时间逆序排列
- [ ] 当前状态描述准确
- [ ] 已完成任务详细具体
- [ ] 影响分析全面客观
- [ ] 后续计划明确可行

### 5.4 TODO验证

- [ ] 中文版（docs/TODO.zh.md）和英文版（docs/TODO.md）都已更新
- [ ] 任务按优先级高、中、低排序
- [ ] 任务状态标记正确
- [ ] 任务描述清晰详细
- [ ] 中文版和英文版内容一致

### 5.5 项目技术文档验证

- [ ] 代码变更涉及模块/文件增删时，ARCHITECTURE.zh.md / ARCHITECTURE.md 目录结构和系统架构图已更新
- [ ] 代码变更涉及数据模型字段时，ARCHITECTURE.zh.md / ARCHITECTURE.md 关键数据模型章节已更新
- [ ] 代码变更涉及配置项时，ARCHITECTURE.zh.md / ARCHITECTURE.md 和 DEVELOPMENT_GUIDE.zh.md / DEVELOPMENT_GUIDE.md 配置章节已同步更新
- [ ] 代码变更涉及外部服务时，ARCHITECTURE.zh.md / ARCHITECTURE.md 外部服务依赖章节已更新
- [ ] 代码变更涉及 OCR/翻译/合并/生成/表格/公式/错误处理等核心逻辑时，TECHNICAL_GUIDE.zh.md / TECHNICAL_GUIDE.md 对应章节已更新
- [ ] 代码变更涉及 CLI 参数或 Web API 路由时，DEVELOPMENT_GUIDE.zh.md / DEVELOPMENT_GUIDE.md 对应章节已更新
- [ ] 代码变更涉及环境依赖或测试结构时，DEVELOPMENT_GUIDE.zh.md / DEVELOPMENT_GUIDE.md 对应章节已更新
- [ ] 文档描述与实际代码行为一致，无虚构或过时内容
- [ ] 三份文档间的交叉引用保持一致（如配置项在 ARCHITECTURE.zh.md / ARCHITECTURE.md 和 DEVELOPMENT_GUIDE.zh.md / DEVELOPMENT_GUIDE.md 中描述一致）
- [ ] 中文版（.zh.md）和英文版已同步更新

### 5.6 整体验证

- [ ] 所有文档变更与代码变更一致
- [ ] 文档格式统一规范
- [ ] 链接和引用正确有效
- [ ] 语言表达清晰准确
- [ ] 提交信息完整描述变更
- [ ] 中文版和英文版同步更新

### 5.7 文件命名验证

- [ ] 中文版文档使用 `.zh.md` 后缀
- [ ] 英文版文档使用原始文件名（无后缀）
- [ ] 文件路径正确，无遗漏
