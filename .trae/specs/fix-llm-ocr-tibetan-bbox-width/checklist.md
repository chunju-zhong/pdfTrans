# Checklist

- [x] 藏文 PDF 的 VLM prompt 包含 bbox 覆盖完整行宽的引导指令
- [x] 英文等非藏文 PDF 的 VLM prompt 与修改前一致（无回归）
- [x] `fix-pixel-to-pdf-y-flip` spec 已标注废弃
- [x] Y 轴翻转代码已确认不存在于 `_pixel_to_pdf_coords` 中
