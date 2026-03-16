# 默认章节创建功能 - 实现计划

## [x] Task 1: 在 ChapterIdentifier 中添加默认章节配置
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 在 `ChapterIdentifier` 类中添加默认章节标题配置
  - 默认章节标题：["封面", "目录", "前言", "引言"]
  - 添加可配置的默认章节层级（默认：1级）
- **Acceptance Criteria Addressed**: AC-5
- **Test Requirements**:
  - `programmatic` TR-1.1: 验证默认章节标题配置正确
  - `programmatic` TR-1.2: 验证默认章节层级配置正确
- **Notes**: 确保配置可以在初始化时自定义

## [ ] Task 2: 实现检测开头无章节页面的方法
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 添加 `_detect_pages_without_chapters` 方法
  - 方法接收总页数和现有章节列表
  - 返回开头连续的无章节页码列表
  - 检测到第一个有章节的页面时停止
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `programmatic` TR-2.1: 验证能正确检测到开头无章节的页面
  - `programmatic` TR-2.2: 验证在第一个有章节页面后停止检测
  - `programmatic` TR-2.3: 验证完全无章节的PDF返回所有页码
- **Notes**: 只检测PDF开头部分

## [ ] Task 3: 实现创建默认章节的方法
- **Priority**: P0
- **Depends On**: Task 2
- **Description**: 
  - 添加 `_create_default_chapters` 方法
  - 方法接收无章节页码列表和默认章节标题
  - 为每个无章节页面创建对应的默认章节
  - 如果无章节页码数量超过默认章节标题数量，复用标题（如"封面2"、"封面3"）
  - 默认章节的位置设为页面左上角 (0, 0)
  - 默认章节ID格式：default_chapter_{index}
- **Acceptance Criteria Addressed**: AC-2
- **Test Requirements**:
  - `programmatic` TR-3.1: 验证能为每个无章节页面创建默认章节
  - `programmatic` TR-3.2: 验证章节标题正确复用
  - `programmatic` TR-3.3: 验证章节位置和ID格式正确
  - `programmatic` TR-3.4: 验证默认章节层级正确
- **Notes**: 确保默认章节插入到章节列表的开头

## [x] Task 4: 集成默认章节创建到章节提取流程
- **Priority**: P0
- **Depends On**: Task 3
- **Description**: 
  - 修改 `extract_bookmarks` 方法
  - 在提取书签后调用默认章节创建逻辑
  - 确保默认章节添加到章节列表的开头
  - 重新构建章节缓存（sorted_chapters、chapters_by_page、chapter_mapping）
  - 保留原有的章节编号逻辑
- **Acceptance Criteria Addressed**: AC-4
- **Test Requirements**:
  - `programmatic` TR-4.1: 验证默认章节正确添加到章节列表
  - `programmatic` TR-4.2: 验证章节缓存正确重建
  - `programmatic` TR-4.3: 验证原有章节不受影响
  - `programmatic` TR-4.4: 验证章节编号正确分配
- **Notes**: 确保不破坏现有功能

## [ ] Task 5: 验证内容关联到默认章节
- **Priority**: P0
- **Depends On**: Task 4
- **Description**: 
  - 验证 `_find_best_chapter` 方法能正确找到默认章节
  - 验证 `associate_text_blocks` 方法能正确关联到默认章节
  - 验证 `associate_tables` 方法能正确关联到默认章节
  - 验证 `associate_images` 方法能正确关联到默认章节
  - 确保现有章节关联逻辑不受影响
- **Acceptance Criteria Addressed**: AC-3, AC-4
- **Test Requirements**:
  - `programmatic` TR-5.1: 验证文本块能正确关联到默认章节
  - `programmatic` TR-5.2: 验证表格能正确关联到默认章节
  - `programmatic` TR-5.3: 验证图像能正确关联到默认章节
  - `programmatic` TR-5.4: 验证现有章节关联不受影响
- **Notes**: 重点测试位置信息为 (0, 0) 的默认章节

## [ ] Task 6: 添加完整的单元测试
- **Priority**: P1
- **Depends On**: Task 5
- **Description**: 
  - 创建测试文件 `test_default_chapter.py`
  - 测试完全无章节的PDF
  - 测试开头部分无章节的PDF
  - 测试有完整章节的PDF
  - 测试默认章节标题复用
  - 测试自定义默认章节标题
  - 测试内容关联到默认章节
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4, AC-5
- **Test Requirements**:
  - `programmatic` TR-6.1: 所有单元测试通过
  - `programmatic` TR-6.2: 测试覆盖率不低于80%
- **Notes**: 使用 pytest 框架

## [x] Task 7: 集成测试和文档更新
- **Priority**: P1
- **Depends On**: Task 6
- **Description**: 
  - 运行完整的测试套件，确保没有回归
  - 更新相关文档（如果需要）
  - 验证性能影响在可接受范围内
- **Acceptance Criteria Addressed**: AC-4, NFR-2
- **Test Requirements**:
  - `programmatic` TR-7.1: 所有现有测试通过
  - `human-judgment` TR-7.2: 性能影响评估通过
- **Notes**: 确保不破坏现有功能
