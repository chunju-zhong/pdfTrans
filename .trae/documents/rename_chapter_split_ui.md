# 修改前端UI"按章节拆分Markdown"为"按章节翻译Markdown" - 实施计划

## 任务概述
将前端界面中的文案"按章节拆分Markdown"修改为"按章节翻译Markdown"，以更准确地描述功能含义。

## 影响范围
需要修改以下文件：

### 1. templates/index.html
- **位置**: 第129行
- **当前内容**: `按章节拆分Markdown`
- **修改为**: `按章节翻译Markdown`

- **位置**: 第131行
- **当前内容**: `启用后会按PDF章节结构拆分生成多个Markdown文件`
- **修改为**: `启用后按章节拆分翻译并生成多个Markdown文件`

### 2. static/js/main.js
- **位置**: 第539行（注释）
- **当前内容**: `// 按章节拆分Markdown选项的父容器`
- **修改为**: `// 按章节翻译Markdown选项的父容器`

- **位置**: 第541行（函数注释）
- **当前内容**: `// 更新按章节拆分选项的可见性`
- **修改为**: `// 更新按章节翻译选项的可见性`

### 3. services/translation_service.py
- **位置**: 第844行（注释）
- **当前内容**: `chapter_split: 是否按章节拆分Markdown (默认: True)`
- **修改为**: `chapter_split: 是否按章节翻译Markdown (默认: True)`

- **位置**: 第1044行（注释）
- **当前内容**: `chapter_split: 是否按章节拆分Markdown (默认: True)`
- **修改为**: `chapter_split: 是否按章节翻译Markdown (默认: True)`

## 实施步骤

1. **修改 templates/index.html**
   - 修改复选框标签文本
   - 修改提示文本

2. **修改 static/js/main.js**
   - 更新相关注释

3. **修改 services/translation_service.py**
   - 更新函数参数注释

## 验证步骤

1. 启动应用后，访问前端页面
2. 选择包含Markdown的输出格式（如"仅Markdown"或"PDF、Word和Markdown"）
3. 确认显示的文本为"按章节翻译Markdown"
4. 确认提示文本为"启用后按章节拆分翻译并生成多个Markdown文件"
