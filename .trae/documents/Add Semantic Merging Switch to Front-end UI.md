## 实现步骤

### 1. 前端UI修改
- 在 `templates/index.html` 中添加语义合并开关控件
- 位置：在输出格式选择下方，开始翻译按钮上方
- 控件类型：复选框，默认勾选（启用语义合并）
- 标签文本："启用语义块合并"

### 2. JavaScript代码修改
- 在 `static/js/main.js` 中更新表单提交逻辑
- 确保语义合并开关的状态被包含在表单数据中
- 当表单提交时，将开关状态作为新参数 `semantic_merge` 发送到服务器

### 3. 后端路由修改
- 在 `app.py` 的 `/translate` 路由中添加对 `semantic_merge` 参数的处理
- 从表单中获取该参数值（默认为True）
- 将该参数传递给 `translation_service.process_translation` 方法

### 4. 翻译服务修改
- 在 `translation_service.py` 的 `process_translation` 方法中添加 `semantic_merge` 参数
- 修改语义块合并逻辑，使其仅在 `semantic_merge` 为 True 时执行
- 当 `semantic_merge` 为 False 时，直接使用原始文本块进行翻译，跳过合并步骤

### 5. 测试验证
- 启动应用并测试新添加的语义合并开关
- 验证启用语义合并时的翻译结果
- 验证禁用语义合并时的翻译结果
- 确保两种模式下都能正确生成PDF和Word文件

## 技术要点
- 前端使用HTML复选框和JavaScript处理表单数据
- 后端使用Flask接收表单参数并传递给翻译服务
- 翻译服务根据参数值条件执行语义块合并逻辑
- 保持代码风格一致，遵循项目规范