# PDF OCR 提取内容并翻译

## Problem Statement

需要翻译国外技术文档的技术人员，经常收到扫描版PDF文档，现有PDF翻译工具只能处理文本型PDF，无法识别扫描版PDF中的文字内容，导致这些文档无法被翻译。

## Evidence

- 现有工具在README中明确标注"本工具仅支持非扫描版PDF文档，不支持OCR功能"
- 大量国外技术文档（标准、规范、手册）仅以扫描版PDF形式分发
- 用户反馈：无法处理扫描版PDF是工具使用的主要限制之一

## Proposed Solution

为PDF翻译工具添加OCR功能，分三个阶段实现：第一阶段集成传统OCR引擎（PaddleOCR），第二阶段添加LLM-based OCR（DeepSeek OCR/Qwen3-VL），第三阶段实现混合策略自动选择最优方案。保留现有TextBlock管线，OCR输出映射为TextBlock对象，无缝接入下游翻译和文档生成流程。

## Key Hypothesis

我们相信OCR提取能力将解决扫描版PDF无法翻译的问题，对于需要翻译国外技术文档的技术人员。我们将通过OCR模式下的成功翻译率来验证这一点。

## What We're NOT Building

- 不改变现有文本型PDF的提取流程（OCR仅作为可选模式）
- 不实现PaddleOCR直接导出Markdown的简化管线（未来可考虑）
- 不实现手写体识别（传统OCR和LLM OCR均不专门优化手写体）
- 不实现实时OCR翻译（仅支持离线批量处理）

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|--------------|
| OCR模式翻译成功率 | >90% | 扫描版PDF能成功提取文本并完成翻译的比例 |
| OCR提取准确率 | >95%（印刷体） | 人工抽样对比OCR文本与原文 |
| 处理速度 | <5秒/页（PaddleOCR） | 计时测量 |
| 现有功能回归 | 0个回归bug | 运行现有235个测试用例 |

## Open Questions

- [ ] PaddleOCR PP-Structure版面分析输出的段落级bbox精度是否满足PDF回写需求？
- [ ] DeepSeek OCR的API调用成本和速率限制如何？
- [ ] Qwen3-VL在AIPing/Silicon Flow平台上的可用性和定价？
- [ ] OCR模式下`mark_non_body_text()`的样式依赖逻辑如何调整？

---

## Users & Context

**Primary User**
- **Who**: 需要翻译国外技术文档的技术人员（工程师、研究员、项目经理）
- **Current behavior**: 收到扫描版PDF后，需要手动使用OCR工具提取文字，再复制到翻译工具中翻译
- **Trigger**: 获得扫描版PDF文档需要翻译时
- **Success state**: 直接使用工具翻译扫描版PDF，无需手动OCR预处理

**Job to Be Done**
当我收到扫描版的技术文档PDF时，我想要直接使用工具提取文字并翻译，以便快速获取文档的中文版本。

**Non-Users**
- 需要手写体识别的用户（当前不支持）
- 需要实时OCR翻译的用户（仅支持离线批量处理）
- 仅处理文本型PDF的用户（不需要OCR功能）

---

## Solution Detail

### Core Capabilities (MoSCoW)

| Priority | Capability | Rationale |
|----------|------------|-----------|
| Must | OCR模式开关 | 用户可选择是否启用OCR提取，默认关闭不影响现有流程 |
| Must | PaddleOCR引擎集成 | 中文识别率最高，支持100+语言，本地推理无API成本 |
| Must | OCR输出映射为TextBlock | 无缝接入现有翻译管线，复用翻译和文档生成功能 |
| Must | CLI --ocr参数 | 命令行用户可启用OCR模式 |
| Should | Web界面OCR开关 | Web用户可启用OCR模式 |
| Should | OCR语言自动检测 | 根据源语言自动配置OCR识别语言 |
| Could | LLM-based OCR（DeepSeek OCR/Qwen3-VL） | 通过OpenAI兼容API调用，支持复杂布局理解 |
| Could | 混合策略自动选择 | 根据文档复杂度自动选择传统OCR或LLM OCR |
| Won't | PaddleOCR直接导出Markdown管线 | 当前保留TextBlock管线，未来可考虑简化 |

### MVP Scope

第一阶段：集成PaddleOCR引擎，添加OCR模式开关，实现扫描版PDF的文字提取和翻译。

### User Flow

1. 用户上传扫描版PDF / 命令行指定扫描版PDF
2. 启用OCR模式（--ocr参数或Web界面开关）
3. 系统检测页面文本量，使用OCR引擎提取文字
4. OCR结果映射为TextBlock，进入现有翻译管线
5. 翻译完成后生成PDF/Word/Markdown文档

---

## Technical Approach

**Feasibility**: HIGH

**Architecture Notes**
- OCR核心插入点：`PdfExtractor._extract_text_blocks()`（pdf_extractor.py:262）
- 新增`_extract_text_blocks_ocr()`方法，在OCR模式下替代PyMuPDF文本提取
- OCR输出映射为TextBlock对象（最小必填：block_no, text, bbox, page_num）
- PaddleOCR PP-StructureV3可区分文本/表格/图表/公式/印章区域，直接输出段落级结果，无需手动合并行级OCR
- PP-StructureV3表格识别输出HTML结构，可映射为现有`PdfTable`模型
- PP-StructureV3图表区域保存为图片，可映射为现有`PdfImage`模型
- 配置遵循现有`os.environ.get() + 默认值`模式
- CLI参数遵循现有`argparse`模式
- LLM-based OCR复用现有OpenAI兼容API客户端模式

**Technical Risks**

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| OCR模式下样式信息缺失影响非正文标记 | M | 对OCR模式的TextBlock简化mark_non_body_text逻辑 |
| PP-StructureV3表格识别精度不如PyMuPDF | M | 保留PyMuPDF表格提取作为备选，OCR模式仅对文本块使用OCR |
| LLM OCR坐标精度不如传统OCR | M | 第一阶段仅用传统OCR，LLM OCR作为备选 |
| PaddleOCR依赖安装复杂 | L | 提供详细安装文档，OCR功能为可选依赖 |

---

## Implementation Phases

| # | Phase | Description | Status | Parallel | Depends | PRP Plan |
|---|-------|-------------|--------|----------|---------|----------|
| 1 | 传统OCR集成 | 集成PaddleOCR，添加OCR模式开关 | done | 2026-05-21 | - | `.claude/PRPs/plans/pdf-ocr-extraction.plan.md` |
| 2 | LLM-based OCR | 集成DeepSeek OCR/Qwen3-VL，通过OpenAI兼容API调用 | pending | - | 1 | - |
| 3 | 混合策略 | 根据文档复杂度自动选择OCR引擎 | pending | - | 1, 2 | - |

### Phase Details

**Phase 1: 传统OCR集成**
- **Goal**: 实现扫描版PDF的文字、表格和图表提取和翻译
- **Scope**:
  - 新增`modules/ocr/`目录，包含OCR引擎基类和PaddleOCR PP-StructureV3实现
  - 使用PP-StructureV3版面分析，区分文本/表格/图表/公式区域
  - 文本区域：OCR识别文字 → 映射为TextBlock
  - 表格区域：PP-StructureV3表格识别 → 映射为PdfTable（HTML结构）
  - 图表区域：保存为图片 → 映射为PdfImage
  - 修改`PdfExtractor`，添加OCR模式分支
  - 修改`TranslationService`，传递OCR参数
  - 修改CLI，添加`--ocr`参数
  - 修改Config，添加OCR相关配置
  - 修改Web界面，添加OCR开关
  - 编写测试用例
- **Success signal**: 扫描版PDF可成功提取文字、表格和图表并翻译，现有测试全部通过

**Phase 2: LLM-based OCR**
- **Goal**: 支持通过LLM视觉模型提取扫描版PDF内容
- **Scope**:
  - 新增LLM OCR引擎类（DeepSeek OCR/Qwen3-VL），复用OpenAI兼容API模式
  - 支持AIPing和Silicon Flow平台上的视觉模型
  - 添加LLM OCR模式开关（OCR开关开启 + LLM OCR开关开启时使用LLM OCR）
  - 设计结构化输出prompt，要求返回JSON格式的文本块和坐标
- **Success signal**: LLM OCR模式可成功提取文字并翻译

**Phase 3: 混合策略**
- **Goal**: 根据文档特征自动选择最优OCR方案
- **Scope**:
  - 实现文档复杂度评估逻辑
  - 根据源语言和内容复杂度自动选择OCR引擎
  - 支持回退机制（LLM OCR失败时回退到传统OCR）
- **Success signal**: 系统可自动选择最优OCR方案，翻译质量优于单一引擎

### Parallelism Notes

阶段1和阶段2可以部分并行开发（OCR引擎基类和接口设计完成后，两个引擎的实现可以并行），但阶段2依赖阶段1的基础设施。阶段3依赖阶段1和阶段2的完成。

---

## Decisions Log

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|-----------|
| OCR输出格式 | TextBlock对象 | Markdown直出 | 保留现有管线，复用翻译和文档生成功能；PDF输出需要bbox坐标 |
| 传统OCR引擎 | PaddleOCR | Tesseract, EasyOCR | 中文识别率最高，支持100+语言，PP-Structure提供段落级输出 |
| LLM OCR模型 | DeepSeek OCR/Qwen3-VL | GPT-4o, Claude | DeepSeek OCR 3B参数96-97%准确率；Qwen3-VL MoE架构推理成本低，OCRBench 875分 |
| OCR模式 | 可选开关 | 默认开启 | 不影响现有文本型PDF处理流程，用户按需启用 |
| OCR插入点 | _extract_text_blocks() | extract()层面 | 最小侵入性，仅替换文本提取逻辑，不影响表格和图像提取 |

---

## Research Summary

**Market Context**
- PaddleOCR v3.5.0支持111种语言，新增PaddleOCR-VL-1.5（0.9B VLM），PP-StructureV3支持Markdown/DOCX导出
- DeepSeek OCR（3B参数）在OmniDocBench上达到96-97%准确率，10x文本压缩
- Qwen3-VL支持32种语言OCR，OCRBench 875分（开源最高），MoE架构推理成本低
- LLM-based OCR趋势：复杂布局理解能力强，但计算资源需求高

**Technical Context**
- TextBlock最小必填字段仅3个（block_no, text, bbox），OCR输出可轻松映射
- OCR插入点明确：`_extract_text_blocks()`方法开头做分支判断
- 配置和CLI扩展模式成熟，遵循现有模式即可
- PaddleOCR输出为行级，需使用PP-Structure获取段落级结果
- OCR模式下样式信息缺失，需调整`mark_non_body_text()`逻辑

---

*Generated: 2026-04-07*
*Status: DRAFT - needs validation*
