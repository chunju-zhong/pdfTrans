# Checklist

## 根因验证

- [x] 已通过 `app.log` 第 27、60-62 行确认：第 8 页 OCR 输出 completion=7399 tokens（命中 8192 上限），且输出含大量重复短语
- [x] 已通过 `app.log` 第 65、68-70 行确认：第 9 页同样 completion=7399 tokens，同样重复问题
- [x] 已通过 `app.log` 第 73、76-78 行确认：第 10 页 completion=797 tokens 正常，问题与窄页+藏文相关
- [x] 已确认根因 1：`modules/ocr/llm_extractor.py:383-388` 的 `chat.completions.create` 未传递 `frequency_penalty`、`presence_penalty`
- [x] 已确认根因 2：`config.OCR_LLM_TEMPERATURE=0.1` 过低，低资源语言陷入重复局部最优
- [x] 已确认根因 3：`config.OCR_LLM_MAX_TOKENS=8000` 过高，允许生成 7399 tokens 的重复内容
- [x] 已确认根因 4：`DEEPSEEK_OCR_PROMPT` 仅 5 个英文单词，无防重复指导
- [x] 已确认根因 5：藏文 OCR 专项规则（`prompts/language_rules/bo_to_zh.py:103-123`）无防重复条目
- [x] 已确认根因 6：`finish_reason=length` 日志建议"增大 max_tokens"是反方向建议
- [x] 已确认根因 7：无 OCR 响应后处理去重逻辑（用户明确要求暂不做，本次 spec 范围外）

## 代码实现

- [x] `config.py` 已新增 `OCR_LLM_FREQUENCY_PENALTY` 配置项，默认 `0.3`
- [x] `config.py` 已新增 `OCR_LLM_PRESENCE_PENALTY` 配置项，默认 `0.2`
- [x] `config.py` 已将 `OCR_LLM_MAX_TOKENS` 默认值从 `8000` 改为 `4096`
- [x] `config.py` 已将 `OCR_LLM_TEMPERATURE` 默认值从 `0.1` 改为 `0.3`
- [x] `.env.example` 已同步更新这 4 个环境变量的注释默认值
- [x] `modules/ocr/llm_extractor.py` 的 `chat.completions.create` 已传递 `frequency_penalty` 和 `presence_penalty`
- [x] `modules/ocr/llm_extractor.py` 的 `DEEPSEEK_OCR_PROMPT` 已追加防重复、防幻觉指导
- [x] `modules/ocr/llm_extractor.py` 的 `finish_reason=length` 日志建议方向已修正
- [x] `prompts/language_rules/bo_to_zh.py` 的 OCR 规则已新增防重复条目

## 行为验证

- [ ] 第 8 页 OCR token 使用 `completion` 显著降低（目标 < 2000 tokens，从 7399 降至合理范围）
  > 需真实 Qianfan API 凭证与原 PDF 复测，本次跳过
- [ ] 第 8 页 OCR 输出不再含数十次重复同一短语
  > 需真实 Qianfan API 凭证与原 PDF 复测，本次跳过
- [ ] 第 9 页同样改善
  > 需真实 Qianfan API 凭证与原 PDF 复测，本次跳过
- [ ] 第 10 页（原本正常）OCR 行为不受影响
  > 需真实 Qianfan API 凭证与原 PDF 复测，本次跳过
- [ ] 非藏文文档的 OCR 行为不受影响（防重复参数对英文/中文文档同样安全）
  > 需真实 Qianfan API 凭证与原 PDF 复测，本次跳过
- [x] `finish_reason=length` 日志不再建议增大 max_tokens（代码已确认改为建议检查重复短语或调高 frequency_penalty）
- [x] 防重复参数可通过环境变量自定义，用户可针对特定模型调优（`OCR_LLM_FREQUENCY_PENALTY`、`OCR_LLM_PRESENCE_PENALTY` 均从环境变量读取）

## 非目标确认

- [x] 未修改 OCR 调用的 `stream` 参数（保持 `stream=False`，OCR 超时已由 `diagnose-glm4v-tibetan-retry` spec 提升至 300s 解决）
- [x] 未修改 `OCR_LLM_DPI`（保持 150，图像分辨率与重复问题无关）
- [x] 未修改 `OCR_LLM_TIMEOUT`（保持 300s，由前一 spec 已优化）
- [x] 未实现 OCR 响应后处理去重逻辑（用户明确要求暂不做，留待后续独立 spec）
- [x] 未实现基于图像像素面积的输出长度合理性预检查（超出本次范围）
- [x] 未修改翻译主流程的超时和回退问题（已由 `fix-translation-timeout-silent-fallback` spec 单独覆盖）
