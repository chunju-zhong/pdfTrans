# PDF翻译工具实现计划（含Gitee仓库配置）

## 1. 项目概述
创建一个基于Python的PDF翻译工具，支持从普通PDF中提取文本，同时调用百度翻译API、aiping API和硅基流动API进行翻译，并将项目托管到Gitee仓库。

## 2. 技术栈选择

### 2.1 最终技术栈
- **后端语言**：Python 3.9+
- **虚拟环境**：conda
- **PDF处理库**：PyMuPDF（高效文本提取）+ pdfplumber（表格处理）
- **翻译服务**：百度翻译API + aiping API + 硅基流动API
- **Web框架**：Flask
- **前端**：HTML/CSS/JavaScript
- **版本控制**：Git + Gitee

## 3. Gitee仓库配置（重点）

### 3.1 仓库信息
- **仓库地址**：https://gitee.com/chunju/pdfTrans
- **仓库名称**：pdfTrans
- **仓库类型**：公开/私有（根据需求选择）

### 3.2 Git配置
1. **本地Git初始化**：
   ```bash
   git init
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```
2. **添加远程仓库**：
   ```bash
   git remote add origin https://gitee.com/chunju/pdfTrans.git
   ```
3. **创建.gitignore文件**：
   ```
   # 虚拟环境
   venv/
   .conda/
   
   # 配置文件
   .env
   
   # 依赖目录
   __pycache__/
   *.pyc
   
   # 输出文件
   outputs/
   uploads/
   
   # 日志文件
   *.log
   
   # IDE配置
   .vscode/
   .idea/
   *.swp
   *.swo
   ```

### 3.3 分支管理策略
- **main**：主分支，仅用于发布稳定版本
- **develop**：开发分支，整合各功能分支
- **feature/xxx**：功能分支，用于开发新功能
- **bugfix/xxx**：bug修复分支
- **release/xxx**：发布分支，用于准备发布

### 3.4 代码提交规范
- **提交信息格式**：`[类型] 简短描述`
- **类型包括**：feat（新功能）、fix（bug修复）、docs（文档）、style（代码风格）、refactor（重构）、test（测试）、chore（构建/工具）
- **示例**：`feat: 添加百度翻译API封装`

## 4. 项目规则文件创建

### 4.1 项目规则文件路径
- 路径：`/Users/chunju/work/pdfTrans/.trae/rules/project_rules.md`

### 4.2 项目规则文件内容
1. 项目概述
2. 技术栈规范
3. 代码风格
4. 目录结构
5. 开发流程
6. 测试规范
7. 部署规范
8. 安全规范
9. 文档规范
10. Git/Gitee使用规范

## 5. 核心功能模块

### 5.1 PDF文本提取模块
- 使用PyMuPDF提取PDF中的文本内容
- 保留文本位置信息
- 处理复杂格式：列表、标题、脚注等
- 使用pdfplumber专门处理表格内容

### 5.2 多翻译API模块
- 封装百度翻译API
- 封装aiping API
- 封装硅基流动API
- 支持多语言对
- 文本预处理和后处理
- 提供翻译服务选择接口

### 5.3 PDF生成模块
- 基于提取的位置信息生成新PDF
- 保留原始布局和格式
- 支持自定义字体
- 处理文本长度变化导致的布局调整

### 5.4 Web界面模块
- 简洁的文件上传界面
- 翻译服务选择
- 实时翻译进度显示
- 多语言选择支持
- 翻译后的PDF下载功能

## 6. 项目结构
```
pdfTrans/
├── .trae/
│   └── rules/
│       └── project_rules.md # 项目规则文件
├── .git/                    # Git仓库目录
├── .gitignore               # Git忽略文件
├── app.py                   # Flask应用入口
├── requirements.txt         # 依赖库列表
├── environment.yml          # conda环境配置
├── config.py                # 配置文件
├── .env                     # 环境变量文件（git忽略）
├── modules/
│   ├── pdf_extractor.py     # PDF文本提取
│   ├── translator.py        # 翻译API基类
│   ├── baidu_translator.py  # 百度翻译API实现
│   ├── aiping_translator.py # aiping翻译API实现
│   ├── silicon_flow_translator.py # 硅基流动翻译API实现
│   └── pdf_generator.py     # PDF生成
├── static/
│   ├── css/
│   │   └── style.css        # 样式文件
│   └── js/
│       └── main.js          # JavaScript逻辑
├── templates/
│   └── index.html           # 主页面
├── uploads/                 # 上传文件目录（git忽略）
└── outputs/                 # 输出文件目录（git忽略）
```

## 7. 实现步骤

### 步骤1：Gitee仓库配置（重点）
1. 在Gitee上创建仓库：https://gitee.com/chunju/pdfTrans
2. 本地初始化Git仓库
3. 创建.gitignore文件
4. 配置Git用户信息
5. 添加远程仓库

### 步骤2：创建项目规则文件
1. 创建目录结构：`mkdir -p /Users/chunju/work/pdfTrans/.trae/rules`
2. 编写`project_rules.md`文件
3. 提交规则文件到Git仓库：
   ```bash
   git add .trae/rules/project_rules.md
   git commit -m "docs: add project rules file"
   git push -u origin main
   ```

### 步骤3：环境搭建与依赖安装
1. 创建conda环境
2. 安装核心依赖
3. 配置环境变量
4. 初始化项目结构
5. 提交初始项目结构：
   ```bash
   git add .
   git commit -m "feat: initialize project structure"
   git push
   ```

### 步骤4：PDF文本提取模块开发
1. 实现基础文本提取功能
2. 添加位置信息提取
3. 集成表格处理
4. 处理复杂格式
5. 测试不同类型PDF的提取效果
6. 提交代码：
   ```bash
   git add modules/pdf_extractor.py
   git commit -m "feat: implement PDF text extraction module"
   git push
   ```

### 步骤5：多翻译API模块开发
1. 创建翻译基类
2. 实现各翻译API封装
3. 实现翻译服务选择工厂
4. 测试各翻译API的效果
5. 提交代码

### 步骤6：PDF生成模块开发
1. 实现基于位置的PDF生成
2. 添加字体支持
3. 处理文本长度变化导致的布局调整
4. 测试生成PDF的格式还原效果
5. 提交代码

### 步骤7：Web界面开发
1. 创建主页面，添加翻译服务选择功能
2. 实现文件上传功能
3. 添加进度显示
4. 实现下载功能
5. 测试完整流程
6. 提交代码

### 步骤8：测试与优化
1. 测试不同类型PDF文件
2. 测试不同翻译API的效果
3. 优化翻译速度和准确性
4. 修复bug和边界情况
5. 性能优化
6. 提交代码

## 8. Gitee仓库使用规范

### 8.1 分支操作规范
- 从main分支创建develop分支
- 开发新功能时，从develop分支创建feature分支
- 修复bug时，从develop分支创建bugfix分支
- 合并分支前必须进行代码审查
- 合并后及时删除临时分支

### 8.2 代码审查规范
- 所有代码必须通过至少一人审查才能合并
- 审查重点：代码质量、功能完整性、安全性、测试覆盖
- 使用Gitee的Pull Request功能进行代码审查

### 8.3 标签管理规范
- 使用语义化版本号：v1.0.0
- 发布稳定版本时创建标签
- 标签必须包含版本描述

## 9. 预期效果
- 项目成功托管到Gitee仓库
- 建立了规范的Git工作流程
- 支持三种翻译API：百度翻译、aiping、硅基流动
- 准确提取PDF中的文本内容
- 高质量的翻译结果
- 生成的PDF格式清晰，保留原始布局
- 简单易用的Web界面

## 10. 开发注意事项
- 严格遵守项目规则文件中的所有规范
- 定期更新依赖库，确保安全性
- 处理大文件时添加进度显示
- 实现适当的错误处理和日志记录
- 确保上传文件的安全性检查
- 定期提交代码，保持仓库更新

通过以上计划，我们可以将PDF翻译工具项目正确地托管到Gitee仓库，并建立规范的开发流程。