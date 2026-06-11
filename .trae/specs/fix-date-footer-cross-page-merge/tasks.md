# Tasks

- [x] Task 1: 修改 _add_similar_blocks() 短文本相似度阈值
  - [x] SubTask 1.1: 将 threshold 统一简化为 0.85
  - [x] SubTask 1.2: 更新注释说明
- [x] Task 2: 验证修复效果
  - [x] SubTask 2.1: 运行现有测试确保无回归
  - [x] SubTask 2.2: 验证 "2025年2月 8" 与 "2025年2月 9" 的 LCS 相似度计算结果（0.8889 > 0.85）

# Task Dependencies
- [Task 2] 依赖 [Task 1]
