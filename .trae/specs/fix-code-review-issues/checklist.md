## 阶段1：安全问题

- [x] 下载路由文件名校验：仅允许字母数字、下划线、连字符、点号，拒绝路径遍历
- [x] SECRET_KEY 无硬编码回退值，缺少时抛出 RuntimeError
- [x] DEBUG 默认值为 False
- [x] app.run 默认绑定 127.0.0.1
- [x] parse_page_range 输入长度限制 ≤ 1000 字符

## 阶段2：数据完整性

- [x] 翻译失败时回退到原文，PDF 不出现空白段落
- [x] 字体大小回退算法基于典型行高估算行数，不假设单行
- [x] PDF 生成器支持 target_pages 参数，仅输出指定页面

## 阶段3：资源管理与健壮性

- [x] OCR 子进程强制 use_gpu=False，与环境变量一致
- [x] OCR 子进程结果获取使用 get(timeout=5) 替代 get_nowait()
- [x] ocr_worker logger 显式配置 handler
- [x] PDF 生成器 new_doc 在 finally 中关闭
- [x] 临时图像目录在 extract_from_pdf 完成后清理
- [x] get_pdf_pages 临时文件在 finally 中删除
- [x] 日志恢复逻辑保存原有 handler 引用直接恢复，不创建新 handler

## 阶段4：验证（ECC 技能）

### security-review 技能验证
- [x] 下载路由路径遍历防护：`../../etc/passwd` 被拒绝，正常文件名通过（28个参数化测试用例 + 路径遍历专项测试）
- [x] config.py 无硬编码密钥、DEBUG 默认 False（源码检查验证）
- [x] extract_glossary 路由添加 page_range 长度限制 + 整数范围验证
- [x] /download/<filename> 路由添加文件名正则验证
- [x] .env.example 中 DEBUG 改为 False

### python-testing 技能验证
- [x] 字体大小回退算法：120pt→10lines→9pt，14pt→1line→10.5pt（7个参数化行数测试 + 边界值测试）
- [x] parse_page_range 长度限制：1001字符被拒绝，1000字符通过（8个参数化解析测试）
- [x] 翻译失败回退原文：3种场景（合并块/原始块/表格单元格）均有测试
- [x] PDF 生成器资源释放：new_doc.close() 在 finally 中被调用
- [x] numpy 数组真值检查：正确使用 `is not None and len() > 0` 模式
- [x] 下载路由文件名验证：28个参数化测试覆盖各种恶意输入
- [x] 共 71 个测试全部通过

### verification-loop 技能验证
- [x] pytest 322 passed（8 failed 为预先存在的 OCR mock 问题）
- [x] 所有模块导入正常
- [x] 16/16 checklist 检查点全部 PASS
- [x] 无硬编码密钥（grep 扫描确认）
