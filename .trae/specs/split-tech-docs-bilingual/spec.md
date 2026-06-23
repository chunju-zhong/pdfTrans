# 技术文档区分中英文版 Spec

## Why
项目文档规范（`prompt/update_doc.md`）要求中文版使用 `.zh.md` 后缀、英文版使用原始文件名，但 `docs/ARCHITECTURE.md`、`docs/TECHNICAL_GUIDE.md`、`docs/DEVELOPMENT_GUIDE.md` 三份技术文档目前只有中文版，缺少英文版，不符合双语规范。

## What Changes
- 将现有三份中文文档重命名为 `.zh.md` 后缀
- 创建对应的英文版文档（原始文件名），内容为中文版的英文翻译
- 更新 `prompt/update_doc.md` 中引用这些文档的路径（如有）

## Impact
- Affected code: 仅文档文件，无代码变更
- Affected specs: 无

## ADDED Requirements

### Requirement: 中文版文档使用 .zh.md 后缀
三份技术文档的中文版 SHALL 使用 `.zh.md` 后缀命名：
- `docs/ARCHITECTURE.zh.md`
- `docs/TECHNICAL_GUIDE.zh.md`
- `docs/DEVELOPMENT_GUIDE.zh.md`

#### Scenario: 中文版文档命名
- **WHEN** 用户查看 docs 目录
- **THEN** 能看到 `.zh.md` 后缀的中文版技术文档

### Requirement: 英文版文档使用原始文件名
三份技术文档的英文版 SHALL 使用原始文件名（无后缀）：
- `docs/ARCHITECTURE.md`
- `docs/TECHNICAL_GUIDE.md`
- `docs/DEVELOPMENT_GUIDE.md`

英文版内容 SHALL 与中文版内容一致，术语翻译准确，避免中式英语。

#### Scenario: 英文版文档可用
- **WHEN** 用户打开 `docs/ARCHITECTURE.md`
- **THEN** 看到的是英文版内容
- **AND** 内容与 `docs/ARCHITECTURE.zh.md` 中文版一致

## MODIFIED Requirements
无

## REMOVED Requirements
无
