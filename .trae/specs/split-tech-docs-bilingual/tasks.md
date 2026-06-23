# Tasks

- [x] Task 1: 重命名中文版文档为 .zh.md 后缀
  - [x] 1.1: 将 `docs/ARCHITECTURE.md` 重命名为 `docs/ARCHITECTURE.zh.md`
  - [x] 1.2: 将 `docs/TECHNICAL_GUIDE.md` 重命名为 `docs/TECHNICAL_GUIDE.zh.md`
  - [x] 1.3: 将 `docs/DEVELOPMENT_GUIDE.md` 重命名为 `docs/DEVELOPMENT_GUIDE.zh.md`

- [x] Task 2: 创建 ARCHITECTURE.md 英文版
  - [x] 2.1: 翻译 `docs/ARCHITECTURE.zh.md` 为英文版，保存为 `docs/ARCHITECTURE.md`

- [x] Task 3: 创建 TECHNICAL_GUIDE.md 英文版
  - [x] 3.1: 翻译 `docs/TECHNICAL_GUIDE.zh.md` 为英文版，保存为 `docs/TECHNICAL_GUIDE.md`

- [x] Task 4: 创建 DEVELOPMENT_GUIDE.md 英文版
  - [x] 4.1: 翻译 `docs/DEVELOPMENT_GUIDE.zh.md` 为英文版，保存为 `docs/DEVELOPMENT_GUIDE.md`

- [x] Task 5: 更新 update_doc.md 中的文档路径引用
  - [x] 5.1: 检查 `prompt/update_doc.md` 中引用三份技术文档的路径，更新为双语路径格式

# Task Dependencies
- Task 2/3/4 依赖 Task 1（先重命名，再基于中文版翻译英文版）
- Task 2/3/4 可并行执行
- Task 5 可与 Task 2/3/4 并行
