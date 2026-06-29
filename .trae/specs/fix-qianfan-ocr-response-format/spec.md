# 调查 qianfan-ocr 响应格式解析降级原因 Spec

## Why

`qianfan-ocr` 模型返回的响应为 JSON 格式（`{"text_blocks": [...]}`），但系统在 `_parse_response` 中降级为 Markdown 段落格式解析，丢失了 bbox 坐标、type 等结构信息。具体表现为日志：

```
LLM OCR第6页原始响应(前500字): { 
   "text_blocks": [ 
     { 
       "id": 0, 
       "text": "གོ་མ་བཞིན་པ་དང་། ...
...
第6页LLM OCR使用Markdown段落格式解析
```

需要调查清楚降级的具体原因，为后续修复提供依据。

## Investigation Goals

1. 确认 `_extract_json` 返回 `None` 的具体原因
2. 分析 qianfan-ocr 完整原始响应中是否包含非 JSON 前缀内容（如 Layout-as-Thought 的 ` thinking` 标记、BOM 等）
3. 确认 qianfan-ocr JSON schema 与 `_parse_json_to_blocks` 期望的字段名是否一致
4. 确认是否存在响应因过长被截断或 `json.loads` 解析失败的情况

## Investigation Method

1. 在 `_extract_page` 中临时记录完整的原始响应（不截断 500 字符）到单独文件
2. 运行一次 qianfan-ocr 的 OCR 提取
3. 分析完整响应内容，定位 JSON 解析失败的根因
4. 清理调试代码

## Impact

- Affected code:
  - `modules/ocr/llm_extractor.py` — 仅添加调试日志（调查完毕后移除）
- 不修改任何业务逻辑