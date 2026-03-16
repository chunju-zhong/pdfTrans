# 章节识别器优化 - 实施计划

## [ ] Task 1: 重命名 _find_title_position 函数
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 为 `_find_title_position` 函数选择一个更合适的名字
  - 更新所有调用该函数的地方
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `human-judgement` TR-1.1: 函数名应该清晰表达其功能，如 `_locate_title_blocks` 或 `_find_title_blocks`
  - `programmatic` TR-1.2: 所有调用该函数的地方都已更新
- **Notes**: 建议的新名字：`_locate_title_blocks` 或 `_find_title_blocks`

## [ ] Task 2: 移除 _extract_position 函数
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 移除 `_extract_position` 函数
  - 移除所有调用该函数的代码
- **Acceptance Criteria Addressed**: AC-2
- **Test Requirements**:
  - `programmatic` TR-2.1: 代码中不再存在 `_extract_position` 函数
  - `programmatic` TR-2.2: 所有调用该函数的地方都已被修改
- **Notes**: 确保移除后不会影响其他功能

## [ ] Task 3: 修改 _build_chapter_tree 方法，统一标题定位逻辑
- **Priority**: P0
- **Depends On**: Task 1, Task 2
- **Description**: 
  - 修改 `_build_chapter_tree` 方法
  - 不再调用 `_extract_position`，始终调用重命名后的函数来查找标题
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `programmatic` TR-3.1: `_build_chapter_tree` 方法不再调用 `_extract_position`
  - `programmatic` TR-3.2: `_build_chapter_tree` 方法始终调用重命名后的函数
- **Notes**: 确保修改后的逻辑能够正确处理所有书签情况

## [ ] Task 4: 验证章节识别功能
- **Priority**: P1
- **Depends On**: Task 1, Task 2, Task 3
- **Description**: 
  - 运行章节识别功能
  - 验证章节识别是否正常工作
- **Acceptance Criteria Addressed**: AC-4
- **Test Requirements**:
  - `programmatic` TR-4.1: 章节识别功能能够正常运行
  - `human-judgement` TR-4.2: 章节识别结果准确
- **Notes**: 可以使用之前的测试文件来验证功能