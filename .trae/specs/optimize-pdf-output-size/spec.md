# PDF 输出体积优化 Spec

## Why
翻译后的 PDF 体积严重膨胀：原文档 300+ 页仅 8MB，翻译后 1 页即达 23MB。根本原因是页面复制方式低效、原文未真正删除、字体重复嵌入、保存时未启用压缩。

## What Changes
- 用 `insert_pdf` 替代 `show_pdf_page` + `new_page` 复制原始页面，避免 XObject 包装导致资源重复嵌入
- 用 PyMuPDF redaction 机制真正删除原文文本，替代白色矩形遮盖
- 实现 `font_cache` 缓存机制，确保同一字体只嵌入一次
- `save()` 调用加上 `deflate=True, garbage=4, clean=True` 压缩优化参数

## Impact
- Affected code: `modules/pdf_generator.py` — 核心生成逻辑全部涉及
- Affected specs: 无直接关联的已有 spec
- 预期效果：1 页翻译 PDF 从 23MB 降至 3-5MB 以内

## ADDED Requirements

### Requirement: 使用 insert_pdf 替代 show_pdf_page 复制页面

系统 SHALL 使用 `fitz.Document.insert_pdf()` 将原始 PDF 页面复制到新文档，而非 `new_page()` + `show_pdf_page()` 的方式。

#### Scenario: 复制单页到新文档
- **WHEN** 需要将原始 PDF 的某一页复制到新文档
- **THEN** 使用 `new_doc.insert_pdf(original_doc, from_page=idx, to_page=idx)` 复制页面
- **AND** 通过 `new_doc[-1]` 获取刚插入的页面对象

#### Scenario: 无翻译内容的页面
- **WHEN** 某页没有翻译内容
- **THEN** 仍然使用 `insert_pdf` 复制原始页面，保持一致性

### Requirement: 使用 redaction 机制删除原文文本

系统 SHALL 使用 PyMuPDF 的 redaction 标注机制真正删除原文文本，而非用白色矩形遮盖。

#### Scenario: 文本块原文删除
- **WHEN** 需要覆盖某个文本块的原文
- **THEN** 先对该区域添加 redaction 标注 `page.add_redact_annot(rect, fill=(1, 1, 1))`
- **AND** 在所有标注添加完成后，一次性调用 `page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)` 执行删除
- **AND** `images=fitz.PDF_REDACT_IMAGE_NONE` 确保不误删页面图片资源

#### Scenario: 表格单元格原文删除
- **WHEN** 需要覆盖表格单元格的原文
- **THEN** 同样使用 redaction 标注替代 `page.draw_rect()` 白色矩形

#### Scenario: redaction 与翻译文本的执行顺序
- **WHEN** 页面有翻译内容需要绘制
- **THEN** 执行顺序为：1) 添加所有 redaction 标注 → 2) `apply_redactions()` 执行删除 → 3) 插入翻译文本
- **AND** 翻译文本必须在 redaction 执行后插入，否则会被误删

### Requirement: 实现字体缓存

系统 SHALL 利用已有的 `self.font_cache` 字典缓存字体选择结果，避免同一字体被重复插入。

#### Scenario: 首次查询字体
- **WHEN** `_get_suitable_font` 首次为某个 `(original_font, target_lang)` 组合查找字体
- **THEN** 正常执行字体查找逻辑
- **AND** 将结果 `(fontname, fontfile)` 存入 `self.font_cache`

#### Scenario: 重复查询字体
- **WHEN** `_get_suitable_font` 再次查询已缓存的 `(original_font, target_lang)` 组合
- **THEN** 直接从缓存返回字体名称
- **AND** 仍需调用 `page.insert_font()` 确保当前页面引用了该字体（PyMuPDF 要求每页引用字体）

#### Scenario: 跨页面字体缓存
- **WHEN** 不同页面使用相同字体
- **THEN** 缓存中的字体路径信息可复用，减少文件系统查找和字体兼容性检测

### Requirement: 保存时启用压缩优化

系统 SHALL 在保存 PDF 时启用 PyMuPDF 的压缩和垃圾回收参数。

#### Scenario: 保存 PDF 文件
- **WHEN** 调用 `new_doc.save()` 保存翻译后的 PDF
- **THEN** 使用 `new_doc.save(output_pdf_path, deflate=True, garbage=4, clean=True)`
- **AND** `deflate=True` 压缩所有 PDF 流
- **AND** `garbage=4` 清除未引用对象并合并重复资源
- **AND** `clean=True` 清理冗余内容流

## MODIFIED Requirements

### Requirement: _draw_translated_text 方法执行流程

原流程：遍历文本块 → 白色矩形遮盖 → 插入翻译文本

修改为：
1. 第一遍遍历：收集所有需要 redact 的区域，添加 redaction 标注
2. 执行 `apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)` 一次性删除原文
3. 第二遍遍历：插入翻译文本

### Requirement: _draw_translated_table 方法执行流程

原流程：遍历单元格 → 白色矩形遮盖 → 插入翻译文本 → 绘制网格线

修改为：
1. 第一遍遍历：收集所有需要 redact 的单元格区域，添加 redaction 标注
2. 执行 `apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)` 一次性删除原文
3. 第二遍遍历：插入翻译文本
4. 绘制网格线（不变）

### Requirement: generate_pdf 主流程

原流程：
```python
new_page = new_doc.new_page(...)
new_page.show_pdf_page(new_page.rect, original_doc, original_page_idx)
```

修改为：
```python
new_doc.insert_pdf(original_doc, from_page=original_page_idx, to_page=original_page_idx)
new_page = new_doc[-1]
```
