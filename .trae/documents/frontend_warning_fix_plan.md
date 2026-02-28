# PDF翻译工具 - 前端警告显示问题修复计划

## 问题分析
从日志中可以看到，Aiping API 响应被检测为截断（truncated=True），但前端没有显示警告。需要找出原因并修复。

## [x] 任务 1: 检查 markdown_generator.py 中的截断检测逻辑
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 检查 AipingMarkdownGenerator._call_api 方法中的截断检测逻辑
  - 验证 truncated 标志是否正确设置
- **Success Criteria**:
  - 截断检测逻辑正确，当 finish_reason 为 "length" 或 "stop" 时，truncated 为 True
- **Test Requirements**:
  - `programmatic` TR-1.1: 当 finish_reason 为 "length" 时，truncated 为 True
  - `programmatic` TR-1.2: 当 finish_reason 为 "stop" 时，truncated 为 True

## [x] 任务 2: 检查 translation_service.py 中的警告添加逻辑
- **Priority**: P0
- **Depends On**: 任务 1
- **Description**:
  - 检查 generate_output_files 方法中的警告添加逻辑
  - 验证当 markdown_result.truncation_info.truncated 为 True 时，警告是否被正确添加到任务对象
- **Success Criteria**:
  - 当 markdown_result.truncation_info.truncated 为 True 时，警告被添加到任务对象
- **Test Requirements**:
  - `programmatic` TR-2.1: 当 markdown_result.truncation_info.truncated 为 True 时，task.add_warning 被调用

## [x] 任务 3: 检查 app.py 中的 /progress 路由
- **Priority**: P1
- **Depends On**: 任务 2
- **Description**:
  - 检查 /progress 路由是否正确返回任务的警告信息
- **Success Criteria**:
  - /progress 路由返回的 JSON 包含 warnings 字段，且内容正确
- **Test Requirements**:
  - `programmatic` TR-3.1: /progress 路由返回的 JSON 包含 warnings 字段
  - `programmatic` TR-3.2: warnings 字段包含任务的警告信息

## [x] 任务 4: 检查前端 main.js 中的警告显示逻辑
- **Priority**: P1
- **Depends On**: 任务 3
- **Description**:
  - 检查 getTranslationProgress 函数中的警告处理逻辑
  - 验证当 progressData.warnings 存在时，警告是否被正确显示
- **Success Criteria**:
  - 当 progressData.warnings 存在且长度大于 0 时，警告被显示在前端
- **Test Requirements**:
  - `programmatic` TR-4.1: 当 progressData.warnings 存在且长度大于 0 时，showProgressWarnings 函数被调用
  - `human-judgement` TR-4.2: 警告信息在前端正确显示

## [x] 任务 5: 测试修复效果
- **Priority**: P0
- **Depends On**: 任务 1-4
- **Description**:
  - 运行翻译任务，生成截断的 Markdown 结果
  - 验证前端是否显示截断警告
- **Success Criteria**:
  - 前端显示 Markdown 生成被截断的警告
- **Test Requirements**:
  - `human-judgement` TR-5.1: 前端显示 Markdown 生成被截断的警告
  - `programmatic` TR-5.2: 警告信息包含正确的 token 使用情况和结束原因

## 预期修复步骤
1. 修复 markdown_generator.py 中的截断检测逻辑（如果有问题）
2. 确保 translation_service.py 中的警告添加逻辑正确
3. 验证 app.py 中的 /progress 路由正确返回警告
4. 确保前端 main.js 中的警告显示逻辑正确
5. 测试修复效果

## 可能的问题原因
1. markdown_generator.py 中的截断检测逻辑有误
2. translation_service.py 中的警告添加逻辑有误
3. app.py 中的 /progress 路由没有正确返回警告
4. 前端 main.js 中的警告显示逻辑有误