# 代码审查问题修复总计划 Spec

## Why
代码审查发现 1 个 CRITICAL、2 个 HIGH、7 个 MEDIUM、5 个 LOW 级别问题，需要系统性修复以确保应用安全性和数据完整性。

## What Changes
- 修复 CRITICAL：下载路由无认证 + 文件名未校验
- 修复 HIGH：硬编码回退密钥、DEBUG+0.0.0.0 默认组合
- 修复 MEDIUM：子进程竞态、资源泄漏、字体估算偏差、翻译失败静默丢数据、页码范围忽略等
- 修复 LOW：日志重复 handler、临时文件清理、输入长度限制等

## Impact
- Affected code: `app.py`, `config.py`, `modules/ocr/ocr_worker.py`, `modules/ocr/paddle_extractor.py`, `modules/pdf_generator.py`, `services/translation_service.py`

## 问题清单与优先级

### CRITICAL (1)

| # | 文件 | 问题 | ECC 技能 |
|---|------|------|----------|
| 1 | app.py:152 | `download_file` 路由无认证，filename 未校验 | security-review |

### HIGH (2)

| # | 文件 | 问题 | ECC 技能 |
|---|------|------|----------|
| 2 | config.py:12 | SECRET_KEY 回退硬编码 'dev-secret-key' | security-review |
| 3 | config.py:13 + app.py:326 | DEBUG=True 默认 + 0.0.0.0 绑定 | security-review |

### MEDIUM (7)

| # | 文件 | 问题 | ECC 技能 |
|---|------|------|----------|
| 4 | ocr_worker.py:27-40 vs 69 | 环境变量强制 CPU 但 use_gpu 参数仍传入 | python-patterns |
| 5 | ocr_worker.py:116-125 | get_nowait() 竞态条件 | python-patterns |
| 6 | ocr_worker.py:74 | ocr_worker logger 未显式配置 handler | python-patterns |
| 7 | pdf_generator.py:81-137 | 异常路径 new_doc 未关闭 | python-patterns |
| 8 | paddle_extractor.py:436-438 | 回退算法 bbox_height*0.75 假设单行，多行块偏大 | - |
| 9 | pdf_generator.py:88-100 | 忽略页码范围，始终输出全部页面 | python-patterns |
| 10 | translation_service.py:490-493 | 翻译失败时静默丢弃数据 | python-patterns |

### LOW (5)

| # | 文件 | 问题 | ECC 技能 |
|---|------|------|----------|
| 11 | paddle_extractor.py:366 | numpy 数组真值检查 | 已修复 |
| 12 | paddle_extractor.py:232-235 | 日志恢复可能创建重复 handler | python-patterns |
| 13 | paddle_extractor.py:615-617 | 临时图像目录未清理 | python-patterns |
| 14 | translation_service.py:36-74 | parse_page_range 无输入长度限制 | security-review |
| 15 | app.py:167-177 | 临时文件异常路径泄漏 | python-patterns |

## 验证策略 — 使用 ECC 技能

### security-review 技能（阶段1验证）
用于验证安全相关修复：
- 下载路由路径遍历防护
- SECRET_KEY 配置安全性
- DEBUG 默认值安全性
- 输入长度限制

### python-testing 技能（阶段2-3验证）
为每个修复编写单元测试：
- 翻译失败回退原文测试
- 字体大小回退算法测试
- PDF 生成器页码范围测试
- OCR 子进程健壮性测试
- 资源泄漏防护测试

### verification-loop 技能（阶段4验证）
系统性验证所有修复：
- 逐项检查 checklist.md 中的每个检查点
- 运行完整测试套件
- 验证应用可正常启动

## ADDED Requirements

### Requirement: 下载路由安全性
`download_file` 路由 SHALL 校验文件名格式（仅允许字母数字、下划线、连字符、点号），拒绝路径遍历尝试。

#### Scenario: 恶意文件名被拒绝
- **WHEN** 用户请求下载文件名为 `../../etc/passwd` 或包含非法字符
- **THEN** 系统 SHALL 返回 400 错误

### Requirement: 安全配置默认值
系统 SHALL 在缺少安全相关环境变量时明确报错，而非回退到不安全的默认值。

#### Scenario: SECRET_KEY 未设置
- **WHEN** `SECRET_KEY` 环境变量未设置
- **THEN** 系统 SHALL 在启动时抛出 RuntimeError

#### Scenario: DEBUG 默认关闭
- **WHEN** `DEBUG` 环境变量未设置
- **THEN** DEBUG SHALL 默认为 False

### Requirement: 翻译失败回退原文
当翻译某个文本块失败时，系统 SHALL 回退到原文而非静默丢弃。

#### Scenario: 翻译 API 异常
- **WHEN** 翻译某个文本块时抛出异常
- **THEN** 系统 SHALL 保留原文文本，避免 PDF 出现空白段落

### Requirement: 资源安全释放
PDF 文档和临时文件 SHALL 在异常路径也被正确关闭和清理。

#### Scenario: PDF 生成异常
- **WHEN** PDF 生成过程中抛出异常
- **THEN** new_doc SHALL 在 finally 块中关闭

### Requirement: 字体大小回退算法改进
当 textline 信息不可用时，回退算法 SHALL 基于典型行高估算行数，而非假设单行。

#### Scenario: 多行文本块无 textline 信息
- **WHEN** 回退算法处理一个 120pt 高的多行文本块
- **THEN** 系统 SHALL 假设典型行高 12pt，估算约 10 行，字体大小约 9pt

### Requirement: OCR 子进程结果获取健壮性
OCR 子进程结果获取 SHALL 使用带超时的 get() 替代 get_nowait()，避免竞态条件。

#### Scenario: 子进程退出但结果未入队
- **WHEN** 子进程 exitcode=0 但结果尚未入队
- **THEN** 系统 SHALL 等待最多 5 秒获取结果，而非立即报错

## MODIFIED Requirements

### Requirement: OCR 子进程 GPU 参数一致性
OCR 子进程工作函数 SHALL 忽略 use_gpu 参数，始终使用 CPU 模式（因为环境变量已强制 CPU）。

### Requirement: PDF 生成器页码范围支持
`generate_pdf` 方法 SHALL 接受可选的 `target_pages` 参数，仅输出指定页面。

## REMOVED Requirements
无

## 验证 Requirements — 使用 ECC 技能

### Requirement: 安全修复验证（security-review 技能）
每个安全修复 SHALL 通过 security-review 技能进行验证，确保修复有效且未引入新问题。

#### Scenario: 下载路由路径遍历防护验证
- **WHEN** 使用 security-review 技能审查 `app.py` 的 `download_file` 路由
- **THEN** SHALL 确认文件名校验逻辑正确拒绝 `../../etc/passwd` 等恶意文件名
- **AND** SHALL 确认正常文件名仍可下载

#### Scenario: 安全配置验证
- **WHEN** 使用 security-review 技能审查 `config.py`
- **THEN** SHALL 确认无硬编码密钥
- **AND** SHALL 确认 DEBUG 默认为 False

### Requirement: 单元测试覆盖（python-testing 技能）
每个修复 SHALL 有对应的单元测试，使用 python-testing 技能编写。

#### Scenario: 翻译失败回退原文测试
- **WHEN** 模拟翻译 API 抛出异常
- **THEN** 测试 SHALL 验证输出包含原文文本而非空白

#### Scenario: 字体大小回退算法测试
- **WHEN** 传入一个 120pt 高的多行文本块（无 textline 信息）
- **THEN** 测试 SHALL 验证估算字体大小 < 20pt（非 bbox_height*0.75=90pt）

#### Scenario: 资源释放测试
- **WHEN** 模拟 PDF 生成过程抛出异常
- **THEN** 测试 SHALL 验证 fitz.Document 被正确关闭

### Requirement: 系统性验证（verification-loop 技能）
所有修复完成后 SHALL 使用 verification-loop 技能逐项验证 checklist.md 中的每个检查点。

#### Scenario: 全部检查点通过
- **WHEN** verification-loop 技能完成验证
- **THEN** checklist.md 中的所有检查点 SHALL 被勾选
- **AND** `pytest tests/ -v` SHALL 通过
