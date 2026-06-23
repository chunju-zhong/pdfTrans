# 生成项目架构与技术文档 Spec

## Why
项目经过长期迭代，积累了大量功能和复杂逻辑，但缺少一份能让 AI 或新开发人员快速理解项目全貌的综合性文档。现有 docs/ 下的 requirement.md 仅覆盖产品需求，OCR-requiremnt.md 仅覆盖 OCR 规划，缺少架构、技术方案、数据流、开发指南等关键信息。

## What Changes
- 在 `/Users/chunju/work/pdfTrans/docs/` 下新增 `ARCHITECTURE.md` — 项目架构文档，涵盖整体架构、模块职责、数据流、关键类关系、配置系统、外部依赖
- 在 `/Users/chunju/work/pdfTrans/docs/` 下新增 `TECHNICAL_GUIDE.md` — 技术方案文档，涵盖 OCR 管线、翻译管线、语义合并、输出生成、公式处理、表格处理、错误处理等核心技术细节
- 在 `/Users/chunju/work/pdfTrans/docs/` 下新增 `DEVELOPMENT_GUIDE.md` — 开发指南文档，涵盖环境搭建、运行方式、CLI/Web/Skill 三种使用方式、测试方法、常见开发任务、代码规范

## Impact
- Affected specs: 无（纯文档新增）
- Affected code: 无代码变更，仅新增文档文件

## ADDED Requirements

### Requirement: 项目架构文档
系统 SHALL 在 `docs/ARCHITECTURE.md` 中提供完整的项目架构说明，包含以下内容：

#### Scenario: 新开发人员阅读架构文档
- **WHEN** 新开发人员或 AI 阅读 `docs/ARCHITECTURE.md`
- **THEN** 能理解项目的整体架构、模块划分、数据流向、关键类关系、配置系统和外部依赖

文档 SHALL 包含：
1. 项目定位与核心功能概述
2. 目录结构说明（每个目录和关键文件的职责）
3. 系统架构图（文本形式描述的三层架构：入口层、服务编排层、核心模块层）
4. 核心数据流（从 PDF 输入到多格式输出的完整流程，含 7 阶段进度模型）
5. 关键数据模型及关系（TextBlock、PdfPage、PdfTable、PdfCell、PdfImage、PdfExtraction、MergedBlock、Task 等）
6. 配置系统说明（Config 类、.env 变量、各配置项含义和默认值）
7. 外部服务依赖（aiping、硅基流动、PaddleOCR）

### Requirement: 技术方案文档
系统 SHALL 在 `docs/TECHNICAL_GUIDE.md` 中提供核心技术方案的详细说明，包含以下内容：

#### Scenario: 开发人员需要理解某子系统实现
- **WHEN** 开发人员需要修改或扩展 OCR、翻译、生成等子系统
- **THEN** 能在 `docs/TECHNICAL_GUIDE.md` 中找到该子系统的技术方案、设计决策和实现细节

文档 SHALL 包含：
1. OCR 管线架构（双引擎：PaddleOCR 本地引擎 + LLM 云端引擎，工厂模式、子进程隔离、系统自适应）
2. 翻译管线架构（双翻译器、System Prompt 规则、并行翻译、截断检测、回退策略）
3. 语义合并策略（规则合并、LLM 合并、两阶段并行合并）
4. PDF 生成技术（两遍绘制、字体选择链、公式渲染降级、文本溢出处理、表格绘制）
5. DOCX 生成技术（LaTeX→MathML→OMML 转换链、合并单元格、图表位置定位）
6. Markdown 生成技术（LLM 驱动排版、公式保护占位符、章节拆分并行生成）
7. 表格处理管线（双引擎提取、精确字符分配、合并单元格推断、网格布局计算）
8. 公式检测与渲染（检测规则、LaTeX 清理、多级渲染降级）
9. 术语表提取与章节识别
10. 错误处理与重试机制（OCR 三层保护、翻译重试、语义分析容错、生成降级）
11. 进度管理模型（7 阶段进度配置、Task 状态机）

### Requirement: 开发指南文档
系统 SHALL 在 `docs/DEVELOPMENT_GUIDE.md` 中提供完整的开发指南，包含以下内容：

#### Scenario: 新开发人员搭建环境并开始开发
- **WHEN** 新开发人员加入项目
- **THEN** 能按照 `docs/DEVELOPMENT_GUIDE.md` 完成环境搭建、运行项目、执行测试，并了解常见开发任务

文档 SHALL 包含：
1. 环境要求与搭建（Python 版本、conda 环境、系统依赖、PaddlePaddle 安装）
2. 配置说明（.env 文件配置、各环境变量含义）
3. 运行方式（Web 服务启动、CLI 命令使用、AI IDE Skill 调用）
4. CLI 完整命令参考（translate、glossary、list-languages 子命令及所有参数）
5. Web API 接口参考（所有路由、请求参数、响应格式）
6. 测试方法（pytest 运行、测试目录结构、关键测试文件说明）
7. 常见开发任务指南（添加新翻译 API、添加新 OCR 引擎、添加新输出格式、修改翻译 Prompt）
8. 代码规范与约定（工厂模式、策略模式、子进程隔离、并行处理、优雅降级等设计模式）
9. 支持语言列表
