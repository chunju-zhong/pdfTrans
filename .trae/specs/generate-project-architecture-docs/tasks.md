# Tasks

- [x] Task 1: 创建 `docs/ARCHITECTURE.md` — 项目架构文档
  - [x] SubTask 1.1: 编写项目定位与核心功能概述
  - [x] SubTask 1.2: 编写目录结构说明
  - [x] SubTask 1.3: 编写系统架构图（三层架构文本描述）
  - [x] SubTask 1.4: 编写核心数据流（7 阶段进度模型）
  - [x] SubTask 1.5: 编写关键数据模型及关系
  - [x] SubTask 1.6: 编写配置系统说明
  - [x] SubTask 1.7: 编写外部服务依赖

- [x] Task 2: 创建 `docs/TECHNICAL_GUIDE.md` — 技术方案文档
  - [x] SubTask 2.1: 编写 OCR 管线架构（双引擎、工厂模式、子进程隔离、系统自适应）
  - [x] SubTask 2.2: 编写翻译管线架构（双翻译器、Prompt 规则、并行翻译、截断检测、回退策略）
  - [x] SubTask 2.3: 编写语义合并策略（规则合并、LLM 合并、两阶段并行合并）
  - [x] SubTask 2.4: 编写 PDF 生成技术（两遍绘制、字体选择、公式渲染降级、溢出处理、表格绘制）
  - [x] SubTask 2.5: 编写 DOCX 生成技术（OMML 转换链、合并单元格、图表定位）
  - [x] SubTask 2.6: 编写 Markdown 生成技术（LLM 排版、公式保护、章节拆分）
  - [x] SubTask 2.7: 编写表格处理管线（双引擎提取、字符分配、合并单元格、网格布局）
  - [x] SubTask 2.8: 编写公式检测与渲染（检测规则、LaTeX 清理、多级降级）
  - [x] SubTask 2.9: 编写术语表提取与章节识别
  - [x] SubTask 2.10: 编写错误处理与重试机制（OCR 三层保护、翻译重试、语义分析容错、生成降级）
  - [x] SubTask 2.11: 编写进度管理模型（7 阶段进度配置、Task 状态机）

- [x] Task 3: 创建 `docs/DEVELOPMENT_GUIDE.md` — 开发指南文档
  - [x] SubTask 3.1: 编写环境要求与搭建
  - [x] SubTask 3.2: 编写配置说明（.env 文件）
  - [x] SubTask 3.3: 编写运行方式（Web / CLI / Skill）
  - [x] SubTask 3.4: 编写 CLI 完整命令参考
  - [x] SubTask 3.5: 编写 Web API 接口参考
  - [x] SubTask 3.6: 编写测试方法
  - [x] SubTask 3.7: 编写常见开发任务指南
  - [x] SubTask 3.8: 编写代码规范与约定
  - [x] SubTask 3.9: 编写支持语言列表

# Task Dependencies
- Task 2 和 Task 3 依赖 Task 1（架构文档提供全局视图，技术方案和开发指南引用其中的概念）
- Task 2 和 Task 3 可并行执行
