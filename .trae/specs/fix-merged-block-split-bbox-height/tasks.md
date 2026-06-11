# Tasks

- [x] Task 1: 修复合并块拆分后的 bbox 高度计算
  - [x] SubTask 1.1: 修改 `services/translation_service.py` 第411-419行，将 `max_height` 替换为各拆分块自身的原始 bbox 高度
  - [x] SubTask 1.2: 保留 `max_width` 的使用（宽度扩展不会导致垂直遮挡问题）

- [x] Task 2: 修复 PDF 生成器字体大小计算
  - [x] SubTask 2.1: 修改 `modules/pdf_generator.py` 第272-274行的 `reduction_factor` 计算，使首次尝试使用原始字体大小
  - [x] SubTask 2.2: 调整尝试策略：attempt 1 = 原始大小，attempt 2 = 0.9x，attempt 3 = 0.8x，attempt 4 = 0.7x，attempt 5 = 0.7x（最小值）

- [x] Task 3: 添加/更新单元测试
  - [x] SubTask 3.1: 测试合并块拆分后各块使用原始 bbox 高度
  - [x] SubTask 3.2: 测试 PDF 生成器首次渲染使用原始字体大小

- [x] Task 4: 验证修复效果
  - [x] SubTask 4.1: 运行现有测试确保无回归

# Task Dependencies

- Task 3 依赖 Task 1、2 完成
- Task 4 依赖 Task 1、2、3 全部完成
- Task 1、2 之间无依赖，可并行执行
