# Blueprint: OCR 分批失败静默吞没修复 + 提取完整性保障

## Objective

修复 OCR 分批处理中部分批次失败时结果被静默丢弃的问题，确保用户能感知到页面缺失，并增加提取完整性校验。

## Problem Statement

当 PDF 超过 batch_size（默认5页）时分批 OCR，部分批次失败后：
1. `_merge_batch_results` 过滤掉 None（失败批次），只合并成功的结果
2. 翻译服务不检查提取页数是否与预期一致
3. 没有任何 `task.add_warning()` 通知用户页面缺失
4. 前端显示"翻译完成"，用户以为翻译了全部页面，实际只翻译了部分

## Steps

### Step 1: _merge_batch_results 返回缺失页码信息

**Context Brief**: `_merge_batch_results` 函数位于 `modules/pdf_extractor.py` L19-63，当前逻辑是过滤掉 None 后合并有效结果。需要修改为同时返回缺失的页码列表，供上层使用。

**Changes**:
- 修改 `_merge_batch_results` 函数签名，新增 `all_page_nums` 参数（所有预期页码列表）
- 函数返回值从 `PdfExtraction` 改为 `(PdfExtraction, list[int])` 元组，第二个元素是缺失页码列表
- 缺失页码 = all_page_nums 中不在任何 valid_result.pages 中的页码
- 当无缺失时返回空列表

**Verification**: 
- 确认 `_merge_batch_results` 返回类型变更
- 确认缺失页码计算正确

**Exit Criteria**: 函数返回 (PdfExtraction, missing_pages) 元组

**Model Tier**: default

---

### Step 2: pdf_extractor.extract 传递缺失页码信息

**Context Brief**: `PdfExtractor.extract` 方法在 OCR 分批路径（L250-282）调用 `_merge_batch_results`，需要适配新的返回值。同时需要将缺失页码信息向上层传递。

**Changes**:
- 在分批路径中，调用 `_merge_batch_results(all_results)` 改为 `_merge_batch_results(all_results, all_page_nums)`
- `extract` 方法返回值从 `PdfExtraction` 改为 `(PdfExtraction, list[int])` 元组
- 非 OCR 路径返回 `(result, [])` 保持一致
- OCR 单批路径返回 `(result, [])` 保持一致

**Verification**:
- 确认所有 `extract` 方法的返回路径都返回元组
- 确认非 OCR 路径不受影响

**Exit Criteria**: extract 方法统一返回 (PdfExtraction, missing_pages) 元组

**Depends on**: Step 1

**Model Tier**: default

---

### Step 3: translation_service 检查提取完整性并添加警告

**Context Brief**: `translation_service.py` 的 `extract_pdf_content` 方法（L206-370）调用 `pdf_extractor.extract()`，需要适配新的返回值，并在存在缺失页码时添加警告。

**Changes**:
- 适配 `extract()` 返回的元组：`extracted_content, missing_pages = pdf_extractor.extract(...)`
- 当 `missing_pages` 非空时：
  - 调用 `task.add_warning(f"OCR提取失败，以下页面内容缺失: {missing_pages}", context={"process": "extraction", "missing_pages": missing_pages})`
  - 日志记录警告
- 当 `missing_pages` 包含所有目标页面时（全部失败），按现有逻辑返回 None
- 在页面遍历循环中，当 `ocr_mode=True` 且存在缺失页码时，跳过缺失页面的进度更新

**Verification**:
- 确认 `task.add_warning()` 被正确调用
- 确认全部失败时仍返回 None
- 确认部分失败时继续翻译但带警告

**Exit Criteria**: 部分批次失败时，用户在前端看到警告信息

**Depends on**: Step 2

**Model Tier**: default

---

### Step 4: 非 OCR 路径的单页处理失败也添加警告

**Context Brief**: `pdf_extractor.py` 的 `_process_page` 方法（L347-391）在处理失败时返回 None，`extract` 方法中仅做 `if page_result` 判断就跳过。`translation_service` 中的"页面无正文块"警告（L353-355）也仅记录日志不通知前端。

**Changes**:
- 在 `extract` 方法的非 OCR 路径中，当 `_process_page` 返回 None 时，收集失败页码到 `failed_pages` 列表
- `extract` 方法返回时，将 `failed_pages` 作为缺失页码列表返回
- 在 `translation_service` 的页面遍历循环中，将"页面无正文块"的 `logger.warning` 改为同时调用 `task.add_warning()`

**Verification**:
- 确认非 OCR 路径的页面处理失败也产生警告
- 确认"页面无正文块"警告传递到前端

**Exit Criteria**: 所有提取阶段的失败都通过 task.add_warning() 通知用户

**Depends on**: Step 2, Step 3

**Model Tier**: default

---

### Step 5: 前端警告展示优化

**Context Brief**: 前端 `main.js` 已有 `showProgressWarnings` 和 `showDownloadLink` 中的警告展示逻辑，但当前警告样式主要针对翻译截断（显示 token_usage、finish_reason）。提取阶段的警告格式不同（包含 missing_pages），需要确保展示正确。

**Changes**:
- 检查前端警告展示代码，确认 `warning.context.missing_pages` 能正确展示
- 如果当前展示逻辑只显示 `message` 字段，则无需修改前端（因为 `message` 已包含缺失页码信息）
- 如果展示逻辑依赖特定 context 字段格式，则调整展示代码以兼容提取警告

**Verification**:
- 确认前端能正确展示提取阶段的警告

**Exit Criteria**: 前端能展示"OCR提取失败，以下页面内容缺失: [21, 22, ...]"的警告

**Depends on**: Step 3

**Model Tier**: default

---

## Dependency Graph

```
Step 1 (merge 返回缺失页码)
  └─→ Step 2 (extract 传递缺失页码)
        ├─→ Step 3 (translation_service 添加警告)
        │     └─→ Step 5 (前端展示优化)
        └─→ Step 4 (非 OCR 路径添加警告)
              └─→ Step 3 (共享警告逻辑)
```

## Parallelism

- Step 4 和 Step 5 可在 Step 2/3 完成后并行执行

## Anti-Pattern Check

- ✅ 不修改 `Task.add_warning()` 的接口
- ✅ 不引入新的全局状态
- ✅ 不修改前端轮询机制
- ✅ 返回值变更通过元组扩展，不破坏现有调用（需同步更新所有调用点）
- ⚠️ 注意：`extract()` 返回值从 `PdfExtraction` 变为 `(PdfExtraction, list[int])` 是**BREAKING CHANGE**，需确保所有调用点同步更新

## Rollback Strategy

每个 Step 独立可回滚。如果 Step 2 的返回值变更导致问题，可以回退到 Step 1 并将缺失页码信息改为通过其他方式传递（如 PdfExtraction 新增属性）。
