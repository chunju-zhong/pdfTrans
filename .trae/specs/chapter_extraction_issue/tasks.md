# PDF翻译工具 - 章节提取功能问题分析 - 实现计划

## [x] 任务 1: 分析代码逻辑
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 分析 `services/translation_service.py` 中的 `extract_pdf_content` 方法
  - 确认 `chapter_split` 参数的传递和使用
  - 验证条件判断逻辑是否正确
- **Acceptance Criteria Addressed**: AC-1, AC-2
- **Test Requirements**:
  - `programmatic` TR-1.1: 验证当 `chapter_split` 为 `False` 时，不调用 `pdf_extractor.get_chapters()`
  - `programmatic` TR-1.2: 验证当 `chapter_split` 为 `True` 时，正常调用 `pdf_extractor.get_chapters()`
- **Notes**: 重点关注 `services/translation_service.py` 第 280-284 行的条件判断
- **Status**: 已完成

## [ ] 任务 2: 修复 `extract_pdf_content` 方法
- **Priority**: P0
- **Depends On**: 任务 1
- **Description**: 
  - 修复 `services/translation_service.py` 中的 `extract_pdf_content` 方法
  - 确保当 `chapter_split` 为 `False` 时，不调用 `pdf_extractor.get_chapters()`
  - 确保当 `chapter_split` 为 `True` 时，正常调用 `pdf_extractor.get_chapters()`
- **Acceptance Criteria Addressed**: AC-1, AC-2
- **Test Requirements**:
  - `programmatic` TR-2.1: 验证当 `chapter_split` 为 `False` 时，不调用 `pdf_extractor.get_chapters()`
  - `programmatic` TR-2.2: 验证当 `chapter_split` 为 `True` 时，正常调用 `pdf_extractor.get_chapters()`
- **Notes**: 重点关注条件判断逻辑

## [ ] 任务 3: 检查前端参数传递
- **Priority**: P1
- **Depends On**: 任务 1
- **Description**: 
  - 检查 `app.py` 中 `chapter_split` 参数的获取和传递
  - 确认前端表单提交的值是否正确传递到后端
- **Acceptance Criteria Addressed**: AC-1, AC-2
- **Test Requirements**:
  - `programmatic` TR-3.1: 验证前端关闭章节拆分时，`chapter_split` 参数为 `False`
  - `programmatic` TR-3.2: 验证前端开启章节拆分时，`chapter_split` 参数为 `True`
- **Notes**: 重点关注 `app.py` 第 62 行的参数获取

## [ ] 任务 4: 检查 `PdfExtractor` 类的实现
- **Priority**: P1
- **Depends On**: 任务 1
- **Description**: 
  - 检查 `modules/pdf_extractor.py` 中的 `get_chapters` 方法
  - 确认 `chapter_split` 参数在 `extract` 方法中的使用
  - 验证 `ChapterIdentifier` 类的 `get_chapters` 方法
- **Acceptance Criteria Addressed**: AC-1, AC-2
- **Test Requirements**:
  - `programmatic` TR-4.1: 验证当 `chapter_split` 为 `False` 时，不调用 `extract_bookmarks`
  - `programmatic` TR-4.2: 验证当 `chapter_split` 为 `True` 时，正常调用 `extract_bookmarks`
- **Notes**: 重点关注 `modules/pdf_extractor.py` 第 142-146 行的条件判断

## [ ] 任务 5: 验证日志输出
- **Priority**: P2
- **Depends On**: 任务 1
- **Description**: 
  - 验证当 `chapter_split` 为 `False` 时，日志是否显示 "未开启章节拆分，跳过章节提取"
  - 验证当 `chapter_split` 为 `True` 时，日志是否显示获取到的章节数量
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `human-judgment` TR-5.1: 检查日志输出是否准确反映执行流程
- **Notes**: 重点关注 `services/translation_service.py` 第 282 和 284 行的日志输出

## [ ] 任务 6: 验证解决方案
- **Priority**: P0
- **Depends On**: 任务 2, 任务 3, 任务 4
- **Description**: 
  - 验证解决方案是否解决了问题
  - 确保当 `chapter_split` 为 `False` 时，不调用 `pdf_extractor.get_chapters()`
  - 确保当 `chapter_split` 为 `True` 时，正常调用 `pdf_extractor.get_chapters()`
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3
- **Test Requirements**:
  - `programmatic` TR-6.1: 验证解决方案是否解决了问题
  - `human-judgment` TR-6.2: 检查代码是否清晰易懂
- **Notes**: 解决方案应该保持代码的可维护性，避免破坏现有功能