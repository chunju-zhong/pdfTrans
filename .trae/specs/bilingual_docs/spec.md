# 文档中英双语化规格

## Why
项目文档目前仅有中文版本，为了支持国际用户和开源社区，需要创建英文版本。同时需要更新文档生成流程，确保每次更新时自动生成中英两个版本。

## What Changes
- 将 `README.md` 重命名为 `README.zh.md`，作为中文版
- 将 `docs/CHANGELOG.md` 重命名为 `docs/CHANGELOG.zh.md`，作为中文版
- 将 `docs/TODO.md` 重命名为 `docs/TODO.zh.md`，作为中文版
- 创建 `README.md` 英文版文档
- 创建 `docs/CHANGELOG.md` 英文版文档
- 创建 `docs/TODO.md` 英文版文档
- 修改 `prompt/update_doc.md` 提示词，要求更新文档时生成中英两个版本

## Impact
- Affected specs: 文档管理
- Affected code: 
  - `README.md` → `README.zh.md`
  - `docs/CHANGELOG.md` → `docs/CHANGELOG.zh.md`
  - `docs/TODO.md` → `docs/TODO.zh.md`
  - `prompt/update_doc.md`

## ADDED Requirements
### Requirement: 文档中英双语支持
项目文档应同时提供中文和英文版本，方便不同语言背景的用户使用。

#### Scenario: 查看中文文档
- **WHEN** 用户访问 `README.zh.md`
- **THEN** 显示中文版本的README文档

#### Scenario: 查看英文文档
- **WHEN** 用户访问 `README.md`
- **THEN** 显示英文版本的README文档

#### Scenario: 更新文档
- **WHEN** 开发者在 `prompt/update_doc.md` 指导下更新文档
- **THEN** 自动生成中文版和英文版两个版本

## MODIFIED Requirements
### Requirement: 文档更新流程
修改文档更新流程，确保中英双语同步更新。

**原流程**: 更新单一语言版本文档
**新流程**: 同时更新中文版(.zh.md)和英文版(.md)文档

## REMOVED Requirements
### Requirement: 单语言文档
项目之前仅维护中文文档，现已升级为双语支持。

**Migration**: 无需迁移，现有中文内容将作为中文版本保存
