# CLI临时目录管理 Checklist

- [ ] Checkpoint 1: 使用 `-o` 指定目录时，tmp 子目录被正确创建
- [ ] Checkpoint 2: 未指定 `-o` 时，在默认 outputs 目录下创建 tmp 子目录
- [ ] Checkpoint 3: 提取的图片被存放到 tmp 目录
- [ ] Checkpoint 4: 中间生成文件被存放到 tmp 目录
- [ ] Checkpoint 5: 最终结果正确移动到 `-o` 指定的位置和文件名
- [ ] Checkpoint 6: tmp 目录已存在时能正确处理
- [ ] Checkpoint 7: 多格式输出（PDF、DOCX、Markdown）都能正常工作
- [ ] Checkpoint 8: 术语提取命令（glossary）也能正确使用 tmp 目录
- [ ] Checkpoint 9: 向后兼容，未使用 `-o` 时行为正常
- [ ] Checkpoint 10: 文档已更新说明 tmp 目录的使用
