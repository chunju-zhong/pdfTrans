# 将app.py拆分为模块化结构

## 1. 项目结构优化

### 1.1 现有结构
```
pdfTrans/
├── app.py              # 主应用，包含所有功能
├── config.py           # 配置文件
├── modules/            # 核心功能模块
│   ├── pdf_extractor.py
│   ├── pdf_generator.py
│   ├── translator.py
│   └── 各翻译器实现
└── ...
```

### 1.2 优化后结构
```
pdfTrans/
├── app.py              # 主应用入口，仅包含Flask应用初始化和路由
├── config.py           # 配置文件
├── models/             # 数据模型
│   └── task.py         # 任务数据模型
├── services/           # 业务逻辑服务
│   ├── task_service.py # 任务管理服务
│   └── translation_service.py # 翻译业务服务
├── utils/              # 辅助工具
│   ├── text_processing.py # 文本处理工具
│   ├── logging_config.py   # 日志配置
│   └── file_utils.py       # 文件处理工具
├── modules/            # 核心功能模块（保持不变）
│   ├── pdf_extractor.py
│   ├── pdf_generator.py
│   ├── translator.py
│   └── 各翻译器实现
└── ...
```

## 2. 模块拆分方案

### 2.1 创建 models/task.py
- 移动 `Task` 类到该文件
- 包含任务状态枚举 `TASK_STATUS`
- 任务数据模型的完整实现

### 2.2 创建 services/task_service.py
- 任务管理服务
- 包含任务字典 `tasks` 的管理
- 提供任务创建、查询、更新、取消等功能

### 2.3 创建 services/translation_service.py
- 翻译业务服务
- 移动 `process_translation` 函数到该文件
- 包含翻译流程的完整实现
- 处理异步翻译任务

### 2.4 创建 utils/text_processing.py
- 文本处理工具
- 移动以下函数到该文件：
  - `merge_semantic_blocks`
  - `is_punctuation`
  - `is_word_boundary`
  - `adjust_split_position`
  - `fix_block_start_punctuation`
  - `split_translated_result`

### 2.5 创建 utils/logging_config.py
- 日志配置
- 移动日志配置代码到该文件

### 2.6 创建 utils/file_utils.py
- 文件处理工具
- 移动 `allowed_file` 函数到该文件
- 提供文件相关的辅助函数

### 2.7 修改 app.py
- 仅保留Flask应用初始化和路由定义
- 导入并使用其他模块的功能
- 简化代码，提高可读性

## 3. 实现步骤

1. 创建所需的目录结构
2. 按照上述方案，将代码从app.py迁移到各个模块文件
3. 修改app.py，导入并使用各个模块的功能
4. 确保所有导入和依赖关系正确
5. 测试应用功能是否正常

## 4. 预期效果

- 代码结构更加清晰，职责分明
- 便于维护和扩展
- 提高代码的可读性和可测试性
- 符合模块化设计原则
- 各模块之间低耦合，高内聚

## 5. 注意事项

- 确保模块之间的依赖关系正确
- 保持函数和类的接口兼容性
- 确保日志配置正确
- 测试所有功能是否正常工作
- 遵循PEP 8代码风格规范