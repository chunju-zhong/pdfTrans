# 任务清单 - 进度系统重构

## 任务依赖关系
- 任务1（创建阶段配置模块）完成后，才能进行任务2（扩展Task类）
- 任务2完成后，才能进行任务3和任务4（更新进度调用）
- 任务3和任务4可以并行执行

## 任务列表

### Task 1: 创建阶段配置模块
- [x] 1.1: 创建 models/phase_config.py 文件，定义 PHASE_CONFIG 常量
- [x] 1.2: 添加阶段配置验证函数 validate_phase_config()
- [x] 1.3: 添加获取阶段信息的辅助函数 get_phase_info()

### Task 2: 扩展Task类
- [ ] 2.1: 在 models/task.py 中导入 PHASE_CONFIG
- [ ] 2.2: 添加 current_phase 属性到 Task 类
- [ ] 2.3: 添加 phase_config 属性到 Task 类
- [ ] 2.4: 实现 update_phase_progress(phase, phase_percent, message) 方法
- [ ] 2.5: 运行现有测试确保向后兼容

### Task 3: 更新translation_service.py进度调用
- [ ] 3.1: 更新初始化阶段进度调用（0, 5, 10 → init阶段0-100%）
- [ ] 3.2: 更新文本提取阶段进度调用（20, 30 → extraction阶段）
- [ ] 3.3: 更新语义合并阶段进度调用（45, 50 → semantic_merge阶段）
- [ ] 3.4: 更新翻译阶段进度调用（40, 50 → translation阶段）
- [ ] 3.5: 更新表格翻译阶段进度调用（75, 80 → table_translation阶段）
- [ ] 3.6: 更新生成输出阶段进度调用（80, 90, 95, 100 → generation阶段）
- [ ] 3.7: 移除所有硬编码的进度数值

### Task 4: 更新app.py进度调用
- [ ] 4.1: 更新翻译任务的文件保存进度调用 → init 阶段
- [ ] 4.2: 更新术语提取任务的进度调用 → 使用 glossary 任务类型
- [ ] 4.3: 在术语提取任务中调用 task.set_task_type('glossary')
- [ ] 4.4: 移除所有硬编码的进度数值

### Task 5: 更新glossary_service.py进度调用
- [ ] 5.1: 更新开始阶段进度调用 → init 阶段
- [ ] 5.2: 更新PDF文本提取阶段进度调用 → pdf_extraction 阶段
- [ ] 5.3: 更新术语提取循环进度调用 → term_extraction 阶段
- [ ] 5.4: 移除所有硬编码的进度数值

### Task 6: 测试验证
- [ ] 6.1: 编写新功能测试用例
- [ ] 6.2: 运行所有测试确保通过
- [ ] 6.3: 手动验证进度显示正常

### Task 7: 代码清理
- [ ] 7.1: 检查是否有遗漏的硬编码进度值
- [ ] 7.2: 确保代码风格符合项目规范
