# TODO.md 移动到 docs 目录计划

## 任务概述
将项目根目录下的 `TODO.md` 文件移动到 `docs/` 目录下，并更新所有相关引用文档。

## 实施步骤

### 步骤1：移动 TODO.md 文件
- 将 `/Users/chunju/work/pdfTrans/TODO.md` 移动到 `/Users/chunju/work/pdfTrans/docs/TODO.md`

### 步骤2：更新 prompt/update_doc.md 引用
更新以下位置的 TODO.md 路径引用：
- 第149行：2.3 TODO.md 更新 -> `docs/TODO.md`
- 第153行：文件路径引用 -> `docs/TODO.md`
- 第198行：更新TODO.md步骤 -> `docs/TODO.md`
- 第206行：优先级检查 -> `docs/TODO.md`
- 第263行：5.3 TODO.md验证 -> `docs/TODO.md`

### 步骤3：更新 prompt/update_test_case.md 引用
更新以下位置的 TODO.md 路径引用：
- 第88行：添加到任务列表 -> `docs/TODO.md`
- 第156行：验证清单 -> `docs/TODO.md`

### 步骤4：更新 prompt/regression_testing.md 引用
更新以下位置的 TODO.md 路径引用：
- 第174行：创建TODO任务 -> `docs/TODO.md`
- 第239行：验证清单 -> `docs/TODO.md`

### 步骤5：验证更新
- 确认 TODO.md 文件已移动到 docs/ 目录
- 确认所有引用都已更新
- 确认没有遗漏的引用

## 预计变更文件
1. `/Users/chunju/work/pdfTrans/TODO.md` -> `/Users/chunju/work/pdfTrans/docs/TODO.md`（移动）
2. `/Users/chunju/work/pdfTrans/prompt/update_doc.md`（更新引用）
3. `/Users/chunju/work/pdfTrans/prompt/update_test_case.md`（更新引用）
4. `/Users/chunju/work/pdfTrans/prompt/regression_testing.md`（更新引用）
