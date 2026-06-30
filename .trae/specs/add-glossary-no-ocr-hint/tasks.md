# Tasks

- [x] Task 1: 在术语提取入口的 `form-hint` 中补充不支持 OCR 的提示文案
  - [x] SubTask 1.1: 编辑 `templates/index.html`，在第 112 行附近的 `form-hint` div 中追加"仅支持 PDF 中的文本，不支持 OCR 识别图片中的文字"说明
  - [x] SubTask 1.2: 保持原有"使用当前选择的页码范围，从上传的PDF中提取术语表"说明不丢失，仅做拼接扩展
- [x] Task 2: 人工校验页面渲染与样式
  - [x] SubTask 2.1: 启动 Web 应用，目视确认术语提取区块的提示文案显示完整、换行/间距正常，未破坏既有布局

# Task Dependencies
- Task 2 依赖 Task 1 完成
