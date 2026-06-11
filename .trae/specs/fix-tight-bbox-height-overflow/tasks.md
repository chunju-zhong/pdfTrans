# Tasks

- [x] Task 1: 在 _compute_tight_bbox() 中增加高度容差限制
  - [x] SubTask 1.1: 在第 467 行后（宽度限制之后），增加高度容差检查：如果 theight / lheight > 1.1，则截断 tight_y1 和 tight_y2 到布局区域内

- [x] Task 2: 修复非 TEXT_LABELS 路径的 font_size 估算
  - [x] SubTask 2.1: 在 formula/formula_number 路径（约第 824 行），优先使用 textline 平均高度估算 font_size
  - [x] SubTask 2.2: 在 figure_caption 路径（约第 861 行），优先使用 textline 平均高度估算 font_size
  - [x] SubTask 2.3: 在 else 分支（约第 902 行），优先使用 textline 平均高度估算 font_size
  - [x] SubTask 2.4: 在 supplement 路径（约第 991 行），使用单个 textline 高度估算 font_size
  - [x] SubTask 2.5: 在 formula_res_list 路径（约第 1027 行），优先使用 textline 平均高度估算 font_size

- [x] Task 3: 验证修复效果
  - [x] SubTask 3.1: 运行现有测试确保无回归

# Task Dependencies
- [Task 1] 和 [Task 2] 独立，可并行执行
- [Task 3] 依赖 [Task 1] 和 [Task 2]
