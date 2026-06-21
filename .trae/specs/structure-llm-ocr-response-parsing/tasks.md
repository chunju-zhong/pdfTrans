# Tasks

- [x] Task 1: 定义 OcrBlock 中间数据类
  - [x] 在 `llm_extractor.py` 中定义 `OcrBlock` dataclass，包含字段：text(str)、bbox(tuple)、block_type(str)、is_image(bool)、table_html(str|None)、bboxes(list[tuple])
  - [x] 定义 block_type 到 TextBlock 属性的映射常量（TITLE/SUB_TITLE/TEXT/HEADER/FOOTER/FOOTNOTE → is_body_text + block_type）

- [x] Task 2: 提取公共 `_create_text_block` 方法
  - [x] 从 `_parse_json_response` 和 `_parse_ref_tags_response` 中提取重复的 TextBlock 创建逻辑（公式检测、字体估算、is_body_text 标记、坐标转换）
  - [x] 实现 `_create_text_block(ocr_block, page_num, page_info) -> TextBlock | None` 方法
  - [x] 实现 `_create_image(ocr_block, page_num) -> PdfImage` 方法（暂不裁剪，先保留接口）

- [x] Task 3: 重构格式检测逻辑，确保互斥
  - [x] 修改 `_parse_response` 的格式检测顺序：先检测 `<|ref|>` 标签，再检测 JSON（仅当文本以 `{` 开头或被 ```json``` 包裹时），最后回退 Markdown
  - [x] 移除 `_extract_json` 第三级容错（`{...}` 提取），避免从 ref 标签文本中误提取 JSON

- [x] Task 4: 重构 ref 标签解析为分步解析
  - [x] 第一步：用正则提取所有 `<|ref|>...<|/ref|><|det|>...<|/det|>` 标注对及其在文本中的起止位置
  - [x] 第二步：根据标注对位置区间，提取相邻标注对之间的文本内容
  - [x] 第三步：将标注对+文本组合为 OcrBlock 列表
  - [x] 在 OcrBlock 中保留 block_type（title/sub_title/text/image/header/footer/footnote 等）

- [x] Task 5: 重构 JSON 解析器输出 OcrBlock
  - [x] 修改 `_parse_json_response` 输出 OcrBlock 列表而非直接创建 TextBlock
  - [x] 从 JSON 的 "type" 字段映射 block_type

- [x] Task 6: 重构 Markdown 解析器输出 OcrBlock
  - [x] 修改 `_parse_markdown_response` 输出 OcrBlock 列表
  - [x] 检测 Markdown 标题层级（# / ## / ###）映射 block_type

- [x] Task 7: 实现统一的模型映射阶段
  - [x] 实现 `_map_ocr_blocks_to_models(ocr_blocks, page_num, page_info) -> (text_blocks, tables, images)` 方法
  - [x] 处理表格 OcrBlock：从 OcrBlock 直接取用 bbox，不再依赖 table_bbox_map 隐式索引对齐
  - [x] 处理图片 OcrBlock：创建 PdfImage
  - [x] 处理文本 OcrBlock：调用 `_create_text_block` 创建 TextBlock

- [x] Task 8: 归一化坐标越界钳位
  - [x] 在 `_pixel_to_pdf_coords` 中，对归一化坐标值钳位到 [0, 999] 后再转换
  - [x] 在 `_parse_det_bboxes` 中增加对负数和科学计数法的容错

- [x] Task 9: 实现图像裁剪保存功能
  - [x] 在 `extract_from_pdf` 中，将 `fitz.Page` 对象传递给 `_extract_page`（新增 `page` 参数）
  - [x] 实现 `_crop_and_save_image(page, pdf_bbox, page_num, image_idx, temp_images_dir) -> str` 方法，使用 `page.get_pixmap(clip=fitz.Rect(pdf_bbox))` 裁剪并保存为 PNG
  - [x] 在模型映射阶段，对 is_image 的 OcrBlock 调用裁剪方法，将返回路径设为 `PdfImage.image_path`
  - [x] 文件命名格式与 PaddleOCR 一致：`ocr_img_p{page_num}_{image_idx}.png`

- [x] Task 10: 更新测试
  - [x] 更新 `tests/test_llm_ocr.py` 适配新的三阶段管道
  - [x] 新增测试：格式检测互斥（ref 标签文本含 `{...}` 不误判为 JSON）
  - [x] 新增测试：block_type 映射（title → is_body_text=False）
  - [x] 新增测试：归一化坐标越界钳位
  - [x] 新增测试：表格坐标显式关联（不再依赖索引对齐）
  - [x] 新增测试：图像裁剪保存（PdfImage.image_path 非空且文件存在）

# Task Dependencies
- Task 1 无依赖，可先行
- Task 2 依赖 Task 1（需要 OcrBlock 定义）
- Task 4, 5, 6 依赖 Task 1（需要 OcrBlock 定义），三者可并行
- Task 7 依赖 Task 2, 4, 5, 6（需要所有解析器输出 OcrBlock）
- Task 3 可与 Task 4-6 并行
- Task 8 无依赖，可先行
- Task 9 依赖 Task 7（需要模型映射阶段完成，知道哪些 OcrBlock 是图像）
- Task 10 依赖 Task 7, 9（需要管道和图像功能完成）
