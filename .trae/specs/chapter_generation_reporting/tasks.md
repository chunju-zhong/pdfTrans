# PDF翻译工具 - 章节生成结果上报功能 - 实现计划

## \[x] Task 1: 分析任务对象接口

* **Priority**: P0

* **Depends On**: None

* **Description**:

  * 分析任务对象是否具有添加警告或错误信息的方法

  * 了解现有的任务状态更新机制

* **Acceptance Criteria Addressed**: AC-1, AC-3

* **Test Requirements**:

  * `programmatic` TR-1.1: 确认任务对象的接口方法

  * `human-judgment` TR-1.2: 理解现有任务状态更新机制

## \[x] Task 2: 定义新的结果类

* **Priority**: P0

* **Depends On**: Task 1

* **Description**:

  * 在 `result_types.py` 中定义新的结果类，用于 `generate_markdown` 返回汇总的批量处理结果

  * 包含章节生成的成功/失败信息和 MarkdownResult 中的截断警告

* **Acceptance Criteria Addressed**: AC-1, AC-3

* **Test Requirements**:

  * `programmatic` TR-2.1: 验证新结果类定义正确

  * `programmatic` TR-2.2: 验证类包含所有必要的字段

## \[x] Task 3: 修改 \_generate\_chapter\_markdowns 方法

* **Priority**: P0

* **Depends On**: Task 2

* **Description**:

  * 修改 `_generate_chapter_markdowns` 方法，返回新的结果类实例

  * 收集章节生成的成功/失败信息和 MarkdownResult 中的截断警告

* **Acceptance Criteria Addressed**: AC-1, AC-3

* **Test Requirements**:

  * `programmatic` TR-3.1: 验证方法返回新的结果类实例

  * `programmatic` TR-3.2: 验证结果收集逻辑实现

## \[x] Task 4: 修改 generate\_markdown 方法

* **Priority**: P0

* **Depends On**: Task 3

* **Description**:

  * 修改 `generate_markdown` 方法，返回新的结果类实例

  * 确保单 Markdown 和章节 Markdown 都返回新的结果类实例

  * 汇总所有章节的生成结果和 MarkdownResult 中的截断警告

* **Acceptance Criteria Addressed**: AC-1, AC-3

* **Test Requirements**:

  * `programmatic` TR-4.1: 验证方法返回新的结果类实例

  * `programmatic` TR-4.2: 验证单 Markdown 生成也返回新的结果类实例

## \[x] Task 5: 修改 translation\_service.py 中的调用

* **Priority**: P0

* **Depends On**: Task 4

* **Description**:

  * 修改 `translation_service.py` 中调用 `generate_markdown` 的代码

  * 处理返回的新结果类实例，在任务中添加警告

* **Acceptance Criteria Addressed**: AC-1, AC-3

* **Test Requirements**:

  * `programmatic` TR-5.1: 验证调用修改正确

  * `programmatic` TR-5.2: 验证警告添加逻辑实现

## \[x] Task 6: 测试和验证

* **Priority**: P1

* **Depends On**: Task 5

* **Description**:

  * 测试章节生成结果上报功能

  * 验证错误信息是否正确上报到前端

* **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3

* **Test Requirements**:

  * `programmatic` TR-6.1: 运行测试，验证功能正常

  * `human-judgment` TR-6.2: 检查错误信息是否清晰可见

