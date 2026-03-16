# 智能默认章节命名功能 - 实现计划（分解和优先级任务列表）

## [ ] 任务1: 修改ChapterIdentifier构造函数，添加智能命名配置参数
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 添加 `use_smart_naming` 参数（默认True），用于选择使用智能命名还是备选命名
  - 保持现有参数的向后兼容性
  - 添加 `max_title_length` 参数（默认20字符），用于限制标题长度
- **Acceptance Criteria Addressed**: [AC-3, AC-4]
- **Test Requirements**:
  - `programmatic` TR-1.1: 验证新的构造函数参数能够正确初始化
  - `programmatic` TR-1.2: 验证默认参数值符合预期（use_smart_naming=True, max_title_length=20）
- **Notes**: 保持与现有代码的兼容性

## [ ] 任务2: 修改extract_bookmarks方法，传递doc对象和pdf_path到_create_default_chapters
- **Priority**: P0
- **Depends On**: 任务1
- **Description**:
  - 在调用 _create_default_chapters 时，传递 PyMuPDF doc 对象和 pdf_path 作为参数
  - 修改 _create_default_chapters 方法签名，接收 doc 和 pdf_path 参数
- **Acceptance Criteria Addressed**: [AC-1, AC-2]
- **Test Requirements**:
  - `programmatic` TR-2.1: 验证 doc 对象和 pdf_path 能够正确传递到 _create_default_chapters 方法
  - `programmatic` TR-2.2: 验证现有功能在修改后仍然正常工作
- **Notes**: 不改变其他方法的调用方式

## [ ] 任务3: 实现获取页面第一个文本块的辅助方法
- **Priority**: P0
- **Depends On**: 任务2
- **Description**:
  - 创建 _get_first_text_block 方法，接收 doc 和 page_num 参数
  - 从指定页面提取第一个有效的文本块（跳过空文本）
  - 清理文本（去除首尾空白字符）
- **Acceptance Criteria Addressed**: [AC-1]
- **Test Requirements**:
  - `programmatic` TR-3.1: 验证方法能正确获取页面第一个文本块
  - `programmatic` TR-3.2: 验证空文本被正确跳过
  - `programmatic` TR-3.3: 验证无文本块时返回None
- **Notes**: 使用PyMuPDF的get_text('blocks')方法

## [ ] 任务4: 实现文本截断功能
- **Priority**: P1
- **Depends On**: 任务3
- **Description**:
  - 创建 _truncate_title 辅助方法，接收文本和最大长度
  - 当文本超过最大长度时截断并添加省略号
  - 处理中英文混合的情况
- **Acceptance Criteria Addressed**: [AC-5]
- **Test Requirements**:
  - `programmatic` TR-4.1: 验证短文本（<=20字符）不被截断
  - `programmatic` TR-4.2: 验证长文本（>20字符）被正确截断并添加省略号
  - `programmatic` TR-4.3: 验证中英文混合文本能正确处理
- **Notes**: 确保截断后的文本美观

## [ ] 任务5: 修改_create_default_chapters方法实现智能命名
- **Priority**: P0
- **Depends On**: 任务3, 任务4
- **Description**:
  - 根据 use_smart_naming 参数决定命名策略
  - 启用智能命名时：优先使用页面第一个文本块
  - 无文本块时：使用文件名和页号作为fallback（格式：{文件名}-第{页号}页）
  - 禁用智能命名时：使用原有的固定标题逻辑
- **Acceptance Criteria Addressed**: [AC-1, AC-2, AC-3, AC-4]
- **Test Requirements**:
  - `programmatic` TR-5.1: 验证启用智能命名时，使用页面第一个文本块
  - `programmatic` TR-5.2: 验证无文本块时，fallback到文件名和页号
  - `programmatic` TR-5.3: 验证禁用智能命名时，使用原有的固定标题逻辑
  - `programmatic` TR-5.4: 验证章节标题被正确截断
- **Notes**: 保持现有功能的完整性

## [ ] 任务6: 更新单元测试
- **Priority**: P0
- **Depends On**: 任务5
- **Description**:
  - 更新 test_default_chapter.py 测试文件
  - 添加智能命名功能的测试用例
  - 测试智能命名与备选命名的切换
  - 测试文本截断功能
  - 测试fallback逻辑（文件名和页号）
- **Acceptance Criteria Addressed**: [AC-1, AC-2, AC-3, AC-4, AC-5]
- **Test Requirements**:
  - `programmatic` TR-6.1: 所有新测试用例通过
  - `programmatic` TR-6.2: 所有现有测试用例仍然通过
  - `programmatic` TR-6.3: 测试覆盖率不降低
- **Notes**: 保持与现有测试风格一致

## [ ] 任务7: 运行完整测试并验证
- **Priority**: P0
- **Depends On**: 任务6
- **Description**:
  - 运行完整的测试套件
  - 验证所有测试通过
  - 检查没有引入新的错误
- **Acceptance Criteria Addressed**: [AC-1, AC-2, AC-3, AC-4, AC-5]
- **Test Requirements**:
  - `programmatic` TR-7.1: 完整测试套件通过
  - `programmatic` TR-7.2: 没有新的错误或警告
  - `programmatic` TR-7.3: 性能影响在可接受范围内（<50ms）
- **Notes**: 使用pytest运行所有测试
