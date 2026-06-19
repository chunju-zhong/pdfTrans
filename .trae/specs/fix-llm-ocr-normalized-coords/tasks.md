# Tasks

- [ ] Task 1: 修改 `_pixel_to_pdf_coords` 方法支持归一化坐标
  - [ ] 添加 `is_normalized` 参数，默认为 False
  - [ ] 当 `is_normalized=True` 时，使用 `coord / 999 * page_size` 转换
  - [ ] 当 `is_normalized=False` 时，保持原有像素坐标转换逻辑
  - [ ] 添加日志记录坐标转换过程

- [ ] Task 2: 在 `_parse_ref_tags_response` 中使用归一化坐标转换
  - [ ] 调用 `_pixel_to_pdf_coords` 时传入 `is_normalized=True`
  - [ ] 更新相关日志

- [ ] Task 3: 更新测试用例
  - [ ] 添加归一化坐标转换测试
  - [ ] 更新现有测试中的期望值（因为坐标转换逻辑变更）

- [ ] Task 4: 重启服务器并验证
  - [ ] 重启 python app.py 加载新代码
  - [ ] 重新翻译第 5 页验证问题是否修复

# Task Dependencies
- Task 1 是 Task 2 的前置条件
- Task 2 是 Task 3 的前置条件（测试需要与代码一致）
- Task 4 依赖 Task 1-3 全部完成
