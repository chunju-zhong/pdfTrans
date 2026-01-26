# PDF翻译工具

## 项目简介
PDF翻译工具是一个支持多种翻译API的PDF文档翻译工具，能够准确提取PDF文本和表格内容，使用多种翻译服务进行翻译，并生成格式良好的翻译后PDF文档。

## 功能特点

### 核心功能
- **PDF文本提取**：支持提取普通文本和表格内容，保留位置信息
- **多翻译API支持**：
  - 百度翻译API
  - aiping 模型调用API
  - 硅基流动 模型调用API
- **PDF生成**：基于原始PDF生成翻译后的PDF，保留原始布局和格式
- **Web界面**：提供简洁易用的Web界面，支持文件上传、翻译服务选择和结果下载
- **指定页码翻译**：支持翻译指定页码或页码范围，提高翻译效率

### 技术特点
- **虚拟环境管理**：支持conda虚拟环境
- **模块化设计**：清晰的代码结构，便于维护和扩展
- **API密钥安全**：使用环境变量管理API密钥，避免硬编码
- **错误处理**：友好的错误提示和处理机制

## 技术栈

- **开发语言**：Python 3.9+
- **虚拟环境**：conda
- **Web框架**：Flask 3.0+
- **PDF处理**：
  - PyMuPDF (fitz) 1.23+：用于PDF文本提取和生成
  - pdfplumber 0.10+：用于表格提取
- **翻译API**：百度翻译API、aiping翻译API、硅基流动翻译API
- **版本控制**：Git + Gitee

## 安装步骤

### 1. 克隆仓库
```bash
git clone https://gitee.com/chunju/pdfTrans.git
cd pdfTrans
```

### 2. 创建并激活conda环境
```bash
conda env create -f environment.yml
conda activate pdfTrans
```

### 3. 配置环境变量
- 复制`.env.example`文件为`.env`
- 在`.env`文件中配置各翻译或模型调用API的密钥

```bash
cp .env.example .env
# 编辑.env文件，添加API密钥
```

### 4. 安装依赖
```bash
pip install -r requirements.txt
```

## 使用方法

### 启动Web服务
```bash
python app.py
```

### 访问Web界面
- 打开浏览器，访问 `http://localhost:5000`
- 上传PDF文件
- 系统自动检测并显示PDF总页数
- 选择翻译页码范围（可选，默认全选所有页）
  - 支持单个页码（如：1,3,5）
  - 支持页码范围（如：1-5,7-10）
  - 可以混合使用（如：1-3,5,7-9）
- 选择翻译服务和目标语言
- 点击"翻译"按钮
- 等待翻译完成，下载翻译后的PDF文件

### 命令行使用（可选）
目前暂不支持命令行直接使用，后续将添加该功能。

## 项目结构

```
pdfTrans/
├── .trae/
│   ├── documents/           # 文档目录
│   │   └── ai_dev_progress.md # 开发进度记录文件
│   └── rules/
│       └── project_rules.md # 项目规则文件
├── .git/                    # Git仓库目录
├── .gitignore               # Git忽略文件
├── app.py                   # Flask应用入口
├── requirements.txt         # 依赖库列表
├── environment.yml          # conda环境配置
├── config.py                # 配置文件
├── .env.example             # 环境变量示例文件
├── doc/                     # 项目文档目录
│   └── project_requirements.md # 项目需求文档
├── modules/                 # 核心功能模块
│   ├── aiping_translator.py      # aiping翻译API实现
│   ├── baidu_translator.py       # 百度翻译API实现
│   ├── pdf_extractor.py          # PDF文本提取模块
│   ├── pdf_generator.py          # PDF生成模块
│   ├── silicon_flow_translator.py # 硅基流动翻译API实现
│   └── translator.py             # 翻译基类
├── static/                  # 静态资源
│   ├── css/
│   │   └── style.css        # 样式文件
│   └── js/
│       └── main.js          # JavaScript文件
├── templates/               # 模板文件
│   └── index.html           # 主页面模板
├── tests/                   # 测试脚本目录
│   └── test_pdf_extractor.py # PDF提取测试脚本
├── uploads/                 # 上传文件目录
└── outputs/                 # 输出文件目录
```

## 开发流程

### 分支管理
- **main**：主分支，仅用于发布稳定版本
- **develop**：开发分支，整合各功能分支
- **feature/xxx**：功能分支，用于开发新功能
- **bugfix/xxx**：bug修复分支
- **release/xxx**：发布分支，用于准备发布

### 代码提交规范
- 提交信息格式：`[类型] 简短描述`
- 类型包括：feat（新功能）、fix（bug修复）、docs（文档）、style（代码风格）、refactor（重构）、test（测试）、chore（构建/工具）
- 示例：`feat: 添加百度翻译API封装`

### 测试规范
- 所有测试脚本必须放在`tests/`目录下，命名格式为`test_*.py`
- 使用pytest框架进行测试
- 单元测试覆盖率不低于80%

### 运行测试
#### 安装依赖
pytest已包含在requirements.txt中，执行安装依赖命令即可：
```bash
pip install -r requirements.txt
```

#### 运行测试命令
- 运行所有测试：
  ```bash
  pytest
  ```

- 运行特定模块测试：
  ```bash
  pytest tests/test_pdf_extractor.py
  ```

- 运行测试并生成覆盖率报告：
  ```bash
  pytest --cov=modules/ tests/
  ```

#### 测试文件列表
- `test_pdf_extractor.py`：PDF提取模块测试
- `test_translator.py`：翻译基类测试
- `test_baidu_translator.py`：百度翻译测试
- `test_aiping_translator.py`：aiping翻译测试
- `test_silicon_flow_translator.py`：硅基流动翻译测试
- `test_pdf_generator.py`：PDF生成模块测试
- `conftest.py`：测试配置文件

## 贡献指南

1. Fork仓库
2. 创建功能分支：`git checkout -b feature/xxx`
3. 提交代码：`git commit -m "feat: 添加xxx功能"`
4. 推送分支：`git push origin feature/xxx`
5. 提交Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，欢迎提交Issue或Pull Request。

## 更新日志

### 2026-01-26
- 修复文本块丢失问题：
  - 修复merge_semantic_blocks函数中合并条件的括号位置错误
  - 原条件逻辑错误导致正文块被错误处理和丢失
  - 修正括号位置后，所有正文块都能正确合并和翻译
- 简化PDF翻译工具工作流程：
  - 在提取文本后直接过滤所有非正文块
  - 简化merge_semantic_blocks函数，移除所有处理非正文块的逻辑
  - 后续合并、拆分和翻译流程只需处理正文块，无需考虑非正文块
  - 提高代码可读性和维护性
- 添加13个新的语义合并扩展测试用例：
  - test_merge_consecutive_body_blocks - 测试连续正文块合并
  - test_merge_blocks_with_sentence_continuation_lowercase - 测试小写字母开头句子延续
  - test_merge_blocks_with_sentence_continuation_punctuation - 测试标点开头句子延续
  - test_no_merge_when_sentence_ends - 测试完整句子结尾不合并
  - test_no_merge_when_vertical_distance_large - 测试垂直距离过大不合并
  - test_merge_multiple_sequential_blocks - 测试多个连续块合并
  - test_empty_blocks_list - 测试空列表输入
  - test_single_block - 测试单个块
  - test_is_sentence_continuation - 测试句子延续检测函数
  - test_split_with_english_words - 测试英文单词完整性保护
  - test_split_with_punctuation_adjustment - 测试标点位置调整
  - test_split_empty_translation - 测试空翻译结果处理
  - test_filter_non_body_blocks - 测试非正文块过滤
- 修复4个失败的测试用例：
  - test_progress.py - 导入错误修复
  - test_font_rendering - PDF生成器格式错误修复
  - test_process_translation_with_page_range - 临时文件问题修复
  - test_translate_api - 测试数据文件路径和patch路径错误修复
- 实现100%测试通过率：
  - 测试总数：98个
  - 通过：98个
  - 失败：0个

### 2026-01-24
- 优化文本拆分逻辑，确保左引号、括号、书名号等成对出现的字符不出现在句尾
- 改进了adjust_split_position函数，添加了对左成对字符的检查
- 增强了split_translated_result函数，确保最终的拆分结果中没有左成对字符出现在块尾
- 添加了辅助函数is_left_pair_character来识别不应该出现在句尾的左成对字符
- 更新了测试脚本，验证了优化效果

### 2026-01-18
- 初始版本发布
- 实现PDF文本提取功能
- 支持百度、aiping、硅基流动翻译API
- 实现PDF生成功能
- 提供Web界面

## 注意事项

1. 本工具仅支持非扫描版PDF文档，不支持OCR功能
2. 翻译质量取决于所选翻译API的质量
3. 处理大型PDF文档可能需要较长时间，可使用指定翻译页功能分次翻译
4. 请确保正确配置API密钥，否则翻译功能将无法使用

## 后续计划

### 短期计划
- [ ] 优化翻译质量
- [ ] 支持翻译成Word格式
- [ ] 支持表格翻译

### 中期计划
- [ ] 支持更多翻译API

### 长期计划
- [ ] 实现文档批量翻译
- [ ] 支持OCR功能（扫描版PDF）
