# Tasks

- [ ] Task 1: 新增 `_compute_tight_bbox` 静态方法
  - [ ] SubTask 1.1: 在 `paddle_extractor.py` 的 `PaddleOcrExtractor` 类中新增 `_compute_tight_bbox` 方法
  - [ ] SubTask 1.2: 实现 textline 中心点匹配逻辑（与 `_build_text_from_textlines` 一致）
  - [ ] SubTask 1.3: 实现 bbox 并集计算 + 宽度异常截断（>30% 超出回退）

- [ ] Task 2: 在文本块处理中集成 tight bbox
  - [ ] SubTask 2.1: 在文本块处理循环（第603行附近）中，调用 `_compute_tight_bbox` 并替代原始 `pixel_bbox`
  - [ ] SubTask 2.2: 回退逻辑：当 tight_bbox 为 None 时使用原始 `block.bbox`
  - [ ] SubTask 2.3: 添加诊断日志：记录 tight_bbox vs layout_bbox 的差异

- [ ] Task 3: 为表格单元格计算精确 bbox
  - [ ] SubTask 3.1: 分析表格数据和 textline 对应关系，设计单元格 bbox 计算方案
  - [ ] SubTask 3.2: 实现单元格近似区域划分（按行列比例）
  - [ ] SubTask 3.3: 在近似区域内匹配 textline，计算并集 bbox
  - [ ] SubTask 3.4: 无匹配 textline 时回退到近似区域 bbox

- [ ] Task 4: 运行验证
  - [ ] SubTask 4.1: 运行程序，检查 `[TIGHT_BBOX]` 日志中的坐标差异
  - [ ] SubTask 4.2: 检查 PDF 输出中文本框和表格框的覆盖情况
  - [ ] SubTask 4.3: 验证右侧和底部残影是否消除

# Task Dependencies

- Task 3 依赖 Task 1
- Task 4 依赖 Task 2, Task 3
