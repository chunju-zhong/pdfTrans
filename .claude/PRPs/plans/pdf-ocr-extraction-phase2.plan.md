# Plan: LLM-based OCR（Phase 2）

## Summary

集成LLM视觉模型（DeepSeek OCR / Qwen3-VL）作为第二种OCR引擎，通过OpenAI兼容API调用，将PDF页面图像发送给视觉模型，获取结构化JSON输出（文本块+坐标+表格+图表），映射为现有TextBlock/PdfTable/PdfImage模型。LLM OCR擅长理解复杂布局、混合内容、低质量扫描，是PaddleOCR的互补方案。

## User Story

As a 需要翻译复杂排版扫描版PDF的技术人员,
I want 使用LLM视觉模型提取PDF内容,
So that 复杂排版、多栏、图文混排的扫描文档也能被准确提取和翻译。

## Problem → Solution

**Current (Phase 1)**: PaddleOCR对标准排版扫描PDF效果好，但对复杂布局（多栏、图文混排、倾斜扫描、低分辨率）识别率下降 → **Desired**: 添加LLM视觉模型作为备选OCR引擎，利用其强大的布局理解能力提升复杂文档的提取准确率

## Metadata
- **Complexity**: Medium
- **Source PRD**: `.claude/PRPs/prds/pdf-ocr-extraction.prd.md`
- **PRD Phase**: Phase 2 - LLM-based OCR
- **Depends on**: Phase 1（已完成）
- **Estimated Files**: 7

---

## UX Design

### CLI Usage
```
# 使用LLM OCR（通过--ocr-engine指定）
python cli.py translate input.pdf --ocr --ocr-engine llm --source en --target zh

# 指定LLM OCR提供商
python cli.py translate input.pdf --ocr --ocr-engine llm --ocr-llm-provider aiping --source en --target zh
```

### Web界面
```
勾选"启用OCR提取" → 显示引擎选择下拉框：
  ○ PaddleOCR（本地引擎，需安装）
  ○ LLM OCR（云端引擎，需API Key）
```

### Interaction Changes

| Touchpoint | Phase 1 | Phase 2 | Notes |
|---|---|---|---|
| `--ocr-engine` | 仅`paddleocr` | 新增`llm`选项 | choices列表扩展 |
| `--ocr-llm-provider` | 无 | 新增参数 | 选择aiping/silicon_flow |
| Web OCR引擎选择 | 无选择 | 下拉框 | 仅OCR开启时显示 |
| Config | 无LLM OCR配置 | 新增LLM OCR配置 | 复用现有API Key |

---

## Mandatory Reading

| Priority | File | Lines | Why |
|---|---|---|---|
| P0 (critical) | `modules/ocr/base.py` | all | OcrExtractor接口契约 |
| P0 (critical) | `modules/ocr/factory.py` | all | 工厂扩展点 |
| P0 (critical) | `modules/ocr/paddle_extractor.py` | 1-100 | 提取器实现模式参照 |
| P1 (important) | `modules/aiping_translator.py` | 1-80 | OpenAI兼容API调用模式 |
| P1 (important) | `modules/glossary_extractor.py` | 1-50, 338-360 | ABC+工厂+多提供商模式 |
| P1 (important) | `config.py` | 22-48 | API配置模式（AIPing/SiliconFlow） |
| P2 (reference) | `cli.py` | 186-200 | CLI参数定义模式 |
| P2 (reference) | `app.py` | 73-74, 104-105 | Web参数传递模式 |

## External Documentation

| Topic | Source | Key Takeaway |
|---|---|---|
| OpenAI Vision API | OpenAI docs | `messages[].content[].image_url.url` 支持 `data:image/png;base64,...` |
| DeepSeek OCR | DeepSeek docs | 3B参数，96-97%准确率，通过OpenAI兼容API调用 |
| Qwen3-VL | Qwen docs | MoE架构，32种语言OCR，OCRBench 875分 |
| AIPing视觉模型 | AIPing docs | 支持Qwen3-VL等视觉模型，OpenAI兼容接口 |
| Silicon Flow视觉模型 | SiliconFlow docs | 支持Qwen3-VL等，OpenAI兼容接口 |

---

## Patterns to Mirror

### OPENAI_VISION_API
// SOURCE: modules/aiping_translator.py (API调用模式)
```python
from openai import OpenAI
import base64

# 创建客户端（复用现有模式）
client = OpenAI(base_url=api_url, api_key=api_key, timeout=60.0)

# 发送图像+文本的多模态请求
response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                }
            ]
        }
    ],
    temperature=0.1,  # 低温度保证提取稳定性
    max_tokens=8192,
)
result_text = response.choices[0].message.content
```

### STRUCTURED_OUTPUT_PARSING
// SOURCE: modules/aiping_semantic_analyzer.py (JSON解析模式)
```python
import json

# LLM返回JSON字符串，需解析
result = json.loads(response_text)
# 容错：尝试从markdown代码块中提取JSON
if not result:
    match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    if match:
        result = json.loads(match.group(1))
```

### PROVIDER_PATTERN
// SOURCE: modules/glossary_extractor.py (多提供商模式)
```python
# 工厂函数根据provider创建不同实例
def create_ocr_extractor(ocr_type='paddleocr', **kwargs):
    if ocr_type == 'paddleocr':
        from modules.ocr.paddle_extractor import PaddleOcrExtractor
        return PaddleOcrExtractor(**kwargs)
    elif ocr_type == 'llm':
        from modules.ocr.llm_extractor import LlmOcrExtractor
        return LlmOcrExtractor(**kwargs)
    else:
        raise ValueError(...)
```

---

## Files to Change

| File | Action | Justification |
|---|---|---|
| `modules/ocr/llm_extractor.py` | CREATE | LlmOcrExtractor实现 |
| `modules/ocr/factory.py` | UPDATE | 添加'llm'引擎类型 |
| `modules/ocr/__init__.py` | UPDATE | 导出新类（可选） |
| `config.py` | UPDATE | 添加LLM OCR配置项 |
| `cli.py` | UPDATE | --ocr-engine添加'llm'，新增--ocr-llm-provider |
| `app.py` | UPDATE | Web端接收ocr_llm_provider参数 |
| `templates/index.html` | UPDATE | OCR引擎选择UI |
| `tests/test_llm_ocr.py` | CREATE | LLM OCR模块测试 |

## NOT Building

- 混合策略自动选择 — 属于Phase 3
- 本地LLM推理（如Ollama） — 仅支持云端API
- 自定义prompt模板UI — 使用内置prompt
- 多模型并行投票 — 单模型提取即可

---

## Step-by-Step Tasks

### Task 1: 扩展Config添加LLM OCR配置
- **ACTION**: 在 `config.py` 的 OCR配置区域添加LLM OCR专用配置
- **IMPLEMENT**: 在 `OCR_DYNAMIC_PARAMS` 之后添加：
  ```python
  # LLM OCR配置
  OCR_LLM_PROVIDER = os.environ.get('OCR_LLM_PROVIDER') or 'aiping'  # 默认提供商
  OCR_LLM_MODEL_AIPING = os.environ.get('OCR_LLM_MODEL_AIPING') or 'Qwen/Qwen3-VL-8B'
  OCR_LLM_MODEL_SILICON_FLOW = os.environ.get('OCR_LLM_MODEL_SILICON_FLOW') or 'Qwen/Qwen3-VL-8B'
  OCR_LLM_MAX_TOKENS = int(os.environ.get('OCR_LLM_MAX_TOKENS', '8192'))
  OCR_LLM_TEMPERATURE = float(os.environ.get('OCR_LLM_TEMPERATURE', '0.1'))
  OCR_LLM_DPI = int(os.environ.get('OCR_LLM_DPI', '150'))  # LLM OCR渲染DPI（比PaddleOCR略低，节省token）
  ```
- **MIRROR**: `AIPING_MODEL_GLOSSARY`、`SILICON_FLOW_MODEL_GLOSSARY` 的按提供商配置模式
- **IMPORTS**: 无新增
- **GOTCHA**:
  - LLM OCR复用现有AIPing/SiliconFlow的API Key和URL配置，无需单独配置API Key
  - 模型名称需包含提供商前缀（如 `Qwen/Qwen3-VL-8B`），这是SiliconFlow的命名约定
  - DPI设150而非200，因为LLM模型对图像分辨率的敏感度不同于传统OCR，且更低DPI减少base64传输量
- **VALIDATE**: `from config import config; print(config.OCR_LLM_PROVIDER)` 输出 `aiping`

### Task 2: 实现LlmOcrExtractor
- **ACTION**: 创建 `modules/ocr/llm_extractor.py`，实现LLM视觉模型OCR
- **IMPLEMENT**: 核心类 `LlmOcrExtractor(OcrExtractor)`
  - 构造函数：`__init__(self, provider='aiping', lang='ch', **kwargs)`
  - 延迟初始化OpenAI客户端（`@property client`），复用现有AIPing/SiliconFlow API配置
  - `extract_from_pdf()`: 逐页渲染→base64编码→调用API→解析结果
  - `_extract_page()`: 调用Vision API，发送system prompt + base64图像
  - `_parse_response()`: 解析JSON为TextBlock/PdfTable/PdfImage
  - `_extract_json()`: 三级容错JSON提取（直接→markdown→嵌入）
  - `_parse_html_table()`: 复用 `_TableHtmlParser` 解析HTML表格
  - OCR_SYSTEM_PROMPT: 要求输出JSON格式（text_blocks/tables/images + bbox坐标）
- **MIRROR**: `modules/aiping_translator.py` 的 OpenAI 客户端创建模式，`modules/glossary_extractor.py` 的多提供商模式
- **IMPORTS**: `openai.OpenAI`, `base64`, `json`, `re`, `fitz`, `models.text_block.TextBlock`, `models.extraction.*`
- **GOTCHA**:
  - LLM OCR不需要子进程隔离（API调用，非本地重计算）
  - base64编码的图像可能很大（150DPI的A4页约2-5MB base64），注意API的request size限制
  - JSON解析需要容错：LLM可能在JSON外包裹markdown代码块或额外文字
  - LLM返回的bbox是图像像素坐标，与PaddleOCR一致，下游管线已兼容
  - LLM OCR无法直接裁剪图片区域，图表的image_path为空
  - 复用 `_TableHtmlParser` 从 `paddle_extractor.py` 解析HTML表格
- **VALIDATE**: mock OpenAI API响应，验证 `_parse_response()` 正确解析为TextBlock/PdfTable/PdfImage

### Task 3: 更新OCR工厂函数
- **ACTION**: 在 `modules/ocr/factory.py` 中添加 `'llm'` 引擎类型
- **IMPLEMENT**:
  ```python
  SUPPORTED_OCR_ENGINES = ['paddleocr', 'llm']

  elif ocr_type == 'llm':
      from modules.ocr.llm_extractor import LlmOcrExtractor
      return LlmOcrExtractor(**kwargs)
  ```
- **MIRROR**: 现有 `paddleocr` 分支的延迟导入模式
- **GOTCHA**: `**kwargs` 会传递 `provider`、`lang` 等参数给 `LlmOcrExtractor`
- **VALIDATE**: `create_ocr_extractor('llm', provider='aiping')` 返回 `LlmOcrExtractor` 实例

### Task 4: 修改CLI添加LLM OCR参数
- **ACTION**: 在 `cli.py` 中扩展 `--ocr-engine` 和添加 `--ocr-llm-provider`
- **IMPLEMENT**:
  1. 修改 `--ocr-engine` 的 `choices=['paddleocr', 'llm']`
  2. 新增 `--ocr-llm-provider`（choices=['aiping', 'silicon_flow']）
  3. 在 `cli/translate_command.py` 中传递 provider 参数
- **VALIDATE**: `python cli.py translate test.pdf --ocr --ocr-engine llm --source en --target zh` 无报错

### Task 5: 修改Web界面添加LLM OCR引擎选择
- **ACTION**: 在 `app.py` 和 `templates/index.html` 中添加LLM OCR引擎选择
- **IMPLEMENT**:
  1. `app.py` 读取 `ocr_llm_provider` 表单参数
  2. `templates/index.html` 添加引擎选择下拉框（勾选OCR后显示）
  3. JavaScript联动：选择LLM → 显示提供商选择
- **VALIDATE**: Web界面勾选OCR → 选择LLM OCR → 选择提供商 → 提交翻译

### Task 6: 编写LLM OCR测试
- **ACTION**: 创建 `tests/test_llm_ocr.py`
- **IMPLEMENT**: 覆盖工厂创建、JSON解析（正常/markdown/嵌入/无效）、延迟初始化、API失败降级
- **GOTCHA**: 所有测试必须mock OpenAI客户端
- **VALIDATE**: `pytest tests/test_llm_ocr.py -v` 全部通过

### Task 7: 集成测试和回归验证
- **ACTION**: 运行完整测试套件，验证无回归
- **VALIDATE**: 全部测试通过，无回归

---

## Testing Strategy

### Unit Tests

| Test | Input | Expected Output | Edge Case? |
|---|---|---|---|
| create_ocr_extractor('llm') | llm类型 | LlmOcrExtractor实例 | No |
| LlmOcrExtractor(provider='aiping') | aiping提供商 | 实例创建成功 | No |
| LlmOcrExtractor(provider='silicon_flow') | silicon_flow提供商 | 实例创建成功 | No |
| _parse_response 正常JSON | 完整JSON | TextBlock列表 | No |
| _parse_response markdown包裹 | ```json...``` | TextBlock列表 | Yes |
| _parse_response 无效JSON | 非JSON文本 | None | Yes |
| _extract_json 直接解析 | `{"key":"val"}` | dict | No |
| _extract_json 嵌入文本 | `text {"key":"val"} text` | dict | Yes |
| client延迟初始化 | 新建实例 | _client初始为None | No |
| _extract_page API失败 | mock API异常 | None（优雅降级） | Yes |

### Edge Cases Checklist
- [x] LLM返回非JSON响应（容错解析）
- [x] LLM返回空text_blocks（空页面）
- [x] API调用超时（timeout=120s）
- [x] API Key未配置（OpenAI初始化报错）
- [x] 图像base64过大（DPI控制）
- [x] LLM返回的bbox格式异常（缺字段、非数字）
- [x] HTML表格解析失败（容错跳过）

---

## Validation Commands

### Static Analysis
```bash
python -m py_compile modules/ocr/llm_extractor.py
```
EXPECT: Zero compilation errors

### Unit Tests
```bash
pytest tests/test_llm_ocr.py -v
```
EXPECT: All tests pass

### Full Test Suite
```bash
pytest tests/ -v
```
EXPECT: No regressions

### Integration Test (requires API key)
```bash
python cli.py translate tests/data/scanned_test.pdf --ocr --ocr-engine llm --source en --target zh -f markdown
```
EXPECT: Translated markdown output with LLM-extracted content

---

## Acceptance Criteria
- [ ] All tasks completed
- [ ] All validation commands pass
- [ ] Tests written and passing
- [ ] LLM OCR模式可成功提取文字并翻译
- [ ] 现有PaddleOCR功能不受影响
- [ ] CLI --ocr-engine llm 参数正常工作
- [ ] Web界面LLM OCR引擎选择正常工作
- [ ] JSON解析容错覆盖各种LLM输出格式

## Completion Checklist
- [x] Code follows discovered patterns (OpenAI客户端、工厂模式、JSON容错解析)
- [x] Error handling matches codebase style (logger.error + 优雅降级)
- [x] Logging follows codebase conventions (logging.getLogger(__name__))
- [x] Tests follow test patterns (pytest + mock)
- [x] No hardcoded values (配置从config.py读取)
- [x] No unnecessary scope additions (混合策略留给Phase 3)
- [x] Self-contained — no questions needed during implementation

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| LLM OCR API调用成本高 | H | M | 默认DPI=150减少token消耗，提供模型选择 |
| LLM返回JSON格式不稳定 | H | M | 三级容错解析（直接→markdown→嵌入提取） |
| LLM OCR速度慢（vs PaddleOCR） | H | L | API调用延迟高但不占用本地资源，可接受 |
| 视觉模型不支持某些语言 | L | M | 选择多语言支持的模型（Qwen3-VL支持32种语言） |
| base64图像超过API限制 | L | H | 控制DPI=150，A4页约2-5MB，大多数API限制10MB+ |
