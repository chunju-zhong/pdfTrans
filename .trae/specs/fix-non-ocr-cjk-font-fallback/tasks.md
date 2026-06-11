# Tasks

- [x] Task 1: 扩展 `_check_font_support()` 为所有语言统一检测
  - [x] SubTask 1.1: 移除 `if target_lang not in ['zh', 'ja', 'ko']: return True` 的短路逻辑
  - [x] SubTask 1.2: 在 `test_chars` 字典中为所有语言添加测试字符：en(含基本拉丁)、de(äöüß)、fr(éèêàç)、es(ñ¿¡)、pt(ãç)、it(àèì)、zh(你好世界)、ja(こんにちは)、ko(안녕하세요)、th(สวัสดี)、vi(Xin chào)、ru(Привет)、ar(مرحبا)、hi(नमस्ते)、he(שלום) 等
  - [x] SubTask 1.3: 对于 `test_chars` 中未列出的语言，使用英文测试字符作为回退

- [x] Task 2: 在 `_get_suitable_font()` 第1步中增加原始字体目标语言支持检测
  - [x] SubTask 2.1: 添加 `_check_embedded_font_support()` 方法，尝试从系统字体中查找内嵌字体的文件路径，调用 `_check_font_support()` 检测其是否支持目标语言字符
  - [x] SubTask 2.2: 若原始字体不支持目标语言字符，跳过该字体，继续执行后续的系统字体搜索逻辑
  - [x] SubTask 2.3: 对于无法获取字体文件路径的PDF内嵌字体，拉丁语言默认支持，非拉丁语言默认跳过

# Task Dependencies

- [Task 1] 先于 [Task 2] 完成
