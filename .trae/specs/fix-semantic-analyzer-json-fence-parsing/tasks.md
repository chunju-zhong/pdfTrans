# Tasks

- [x] Task 1: 在基类 `SemanticAnalyzer` 中新增 `_extract_json_from_response(text)` 辅助方法
  - [x] SubTask 1.1: 在 `modules/semantic_analyzer.py` 的 `SemanticAnalyzer` 类中新增方法，实现三级容错提取（直接解析 / ```` ```json ````栅栏正则 / 首`{`尾`}`回退），全部失败返回 `None`。参考 `modules/ocr/llm_response_parser.py:LlmOcrResponseParser._extract_json`（行 135-169）的实现，但适配语义分析器的返回结构（`{"merge": ...}`）
  - [x] SubTask 1.2: 在文件顶部导入 `re` 模块（当前未导入）

- [x] Task 2: 修改 `SemanticAnalyzer.analyze_semantic_relationship`（`modules/semantic_analyzer.py`，非流式单次）的 JSON 解析处
  - [x] SubTask 2.1: 将第 92 行 `analysis_json = json.loads(analysis_result)` 替换为 `analysis_json = self._extract_json_from_response(analysis_result)`
  - [x] SubTask 2.2: 在解析后增加 `if analysis_json is None: raise json.JSONDecodeError("无法从响应中提取JSON", analysis_result, 0)`，使其走原有 except 分支（保持重试/默认值逻辑不变）

- [x] Task 3: 修改 `SemanticAnalyzer.batch_analyze_semantic_relationship`（`modules/semantic_analyzer.py`，非流式批量）的 JSON 解析处
  - [x] SubTask 3.1: 将第 177 行 `analysis_json = json.loads(analysis_result)` 替换为 `analysis_json = self._extract_json_from_response(analysis_result)`
  - [x] SubTask 3.2: 在解析后增加 `if analysis_json is None: raise json.JSONDecodeError("无法从响应中提取JSON", analysis_result, 0)`，使其走原有 `except json.JSONDecodeError` 分支

- [x] Task 4: 修改 `AipingSemanticAnalyzer.analyze_semantic_relationship`（`modules/aiping_semantic_analyzer.py`，流式单次）的 JSON 解析处
  - [x] SubTask 4.1: 将第 91 行 `analysis_json = json.loads(analysis_result)` 替换为 `analysis_json = self._extract_json_from_response(analysis_result)`（继承自基类）
  - [x] SubTask 4.2: 在解析后增加 `if analysis_json is None: raise json.JSONDecodeError("无法从响应中提取JSON", analysis_result, 0)`，使其走原有 except 分支

- [x] Task 5: 修改 `AipingSemanticAnalyzer.batch_analyze_semantic_relationship`（`modules/aiping_semantic_analyzer.py`，流式批量）的 JSON 解析处
  - [x] SubTask 5.1: 将第 188 行 `analysis_json = json.loads(analysis_result)` 替换为 `analysis_json = self._extract_json_from_response(analysis_result)`（继承自基类）
  - [x] SubTask 5.2: 在解析后增加 `if analysis_json is None: raise json.JSONDecodeError("无法从响应中提取JSON", analysis_result, 0)`，使其走原有 `except json.JSONDecodeError` 分支

- [x] Task 6: 验证修复效果
  - [x] SubTask 6.1: 编写单元测试覆盖三种场景：纯 JSON、```` ```json ````栅栏包裹、混合文本含 JSON
  - [x] SubTask 6.2: 运行现有语义分析器相关测试（如存在），确保无回归

# Task Dependencies

- Task 2、3、4、5 均依赖 Task 1（需要基类新方法）
- Task 6 依赖 Task 1-5 全部完成
