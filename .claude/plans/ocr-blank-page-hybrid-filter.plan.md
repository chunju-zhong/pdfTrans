# Plan: 空白页OCR幻觉拦截（混合策略）

**Complexity**: Medium

## Summary

对 LLM OCR 流程增加两层防护：前置像素方差检测（跳过空白页，省 API 调用）+ 后置 OCR 输出质量检测（过滤幻觉/噪声文本块，不让其进入翻译管道）。

## 因果链回顾

```
第14页空白页 → OCR模型产生数字枚举幻觉
→ 解析出1个覆盖整页的巨大文本块(6506字符)
→ 送入翻译API → 输入5743 + 输出8193 → 顶满TRANSLATION_MAX_TOKENS → 翻译被截断
```

同样的模式在第16页也出现（`1.1.1.1.1...` 序列）。

## Patterns to Mirror

| Category | Source | Pattern |
|---|---|---|
| 日志格式 | `llm_extractor.py:210-211` | `logger.info(f"LLM OCR第{page_num}页尺寸: ...")` |
| 进度回调 | `llm_extractor.py:239-253` | 通过 `progress_callback('step_progress', {...})` |
| 跳过处理 | `llm_extractor.py:231-236` | 失败/空时追加 `PdfPage(page_num, [])` |
| 解析器扩展 | `llm_response_parser.py:429-501` | `_map_ocr_blocks_to_models` 中过滤块 |

## Files to Change

| File | Action | Why |
|---|---|---|
| `modules/ocr/llm_extractor.py` | UPDATE | 添加 `_is_blank_image()` 像素方差检测 |
| `modules/ocr/llm_response_parser.py` | UPDATE | 添加 `_is_noise_text()` 输出质量过滤 |
| `modules/ocr/llm_extractor.py` | UPDATE | 后处理中调用质量过滤 |

## Tasks

### Task 1: 前置像素方差检测（_is_blank_image）

**Action**: 在 `llm_extractor.py` 中添加静态方法 `_is_blank_image(img_base64, threshold=5.0)`，检测渲染后图像是否为空白。

**实现逻辑**：
1. `img_base64` → PIL Image → 转灰度图
2. 计算像素值的标准差（或方差）
3. 如果标准差 < threshold（默认 5.0），判断为空白页
4. 空白页时直接返回空结果 (`(None, None)`)，**不调用 OCR API**

**注意**：
- 纯白页标准差 ≈ 0；有文字的页面一般标准差 > 20-30
- threshold = 5.0 是保守值，只捕获真正的空白/纯色页
- 边距/页码（微小差异）不会误杀

**代码位置**：添加到 `_extract_page` 方法开头，`try` 块中第一行。

**改动量**：~20 行代码

### Task 2: 后置 OCR 输出质量过滤（_is_noise_text）

**Action**: 在 `llm_response_parser.py` 的 `_map_ocr_blocks_to_models` 中，添加对 `OcrBlock` 内容的质量检测，过滤明显幻觉文本。

**检测规则**（满足任意一条即过滤）：

| 规则 | 条件 | 匹配示例 |
|---|---|---|
| R1: 全页覆盖 + 枚举噪声 | bbox `[[0,0,997,997]` 附近 + 内容匹配 `\d+\.\s+\d+\.\s+...` 模式 | 第14页 `1. 2. 3. ... 111` |
| R2: 重复数字序列 | 内容匹配 `(1\.1\.)+` 或 `(\d+\.\s+){3,}` 占比 > 60% | 第16页 `1.1.1.1.1...` |
| R3: 纯符号/数字/标点占比 > 85% | 去掉空白后统计 | 正常文本通常数字+标点 < 30% |

**代码位置**：在 `_map_ocr_blocks_to_models` 方法中，`OcrBlock` → TextBlock 转换前插入过滤条件。

**改动量**：~30 行代码

### Task 3: 单元测试

**Action**: 验证检测逻辑的正确性。

**测试用例**：
1. 空白图像（白色/纯色）→ `_is_blank_image=True`
2. 正常文本图像 → `_is_blank_image=False`
3. `1. 2. 3. 4. ... 111` → `_is_noise_text=True`
4. `1.1.1.1.1...` → `_is_noise_text=True`
5. 正常英文/中文段落 → `_is_noise_text=False`
6. 第14页 OCR 响应完整流程 → 最终产出空文本块列表

## Validation

```bash
# 单元测试
python -m pytest tests/test_ocr_blank_page.py -v

# 手动验证：用已有的第14页图像跑OCR
python -c "from modules.ocr.llm_extractor import LlmOcrExtractor; ..."
```

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| 像素方差阈值对深色背景页误判 | 低 | 背景色方差也低，但阈值 5.0 已很保守 |
| 噪声格式超出当前3条规则 | 中 | 规则设计为可扩展，`_is_noise_text` 返回第一条匹配原因，便于调试添加新规则 |
| 误杀含大量数字的正常文本（如API文档） | 低 | 规则 R3 要求 >85%，AP文档通常数字占比 < 60% |

## Acceptance

- [ ] 空白页不调用 OCR API（节省费用 + 时间）
- [ ] OCR 产生幻觉文本时不进入翻译管道
- [ ] 正常内容不受影响
- [ ] 所有测试通过