# Checklist

- [x] `modules/semantic_analyzer.py` 顶部已导入 `re` 模块
- [x] `SemanticAnalyzer` 类中新增了 `_extract_json_from_response(text)` 方法
- [x] `_extract_json_from_response` 实现三级容错：直接解析 → ```` ```json ````栅栏正则 → 首`{`尾`}`回退
- [x] `_extract_json_from_response` 全部失败时返回 `None`，不抛异常
- [x] `_extract_json_from_response` 正则同时匹配 ```` ```json ```` 和 ```` ``` ````（无语言标记的栅栏）
- [x] `SemanticAnalyzer.analyze_semantic_relationship` 使用 `_extract_json_from_response` 替代直接 `json.loads`
- [x] `SemanticAnalyzer.batch_analyze_semantic_relationship` 使用 `_extract_json_from_response` 替代直接 `json.loads`
- [x] `AipingSemanticAnalyzer.analyze_semantic_relationship` 使用继承的 `_extract_json_from_response` 替代直接 `json.loads`
- [x] `AipingSemanticAnalyzer.batch_analyze_semantic_relationship` 使用继承的 `_extract_json_from_response` 替代直接 `json.loads`
- [x] 4 处调用点在 `_extract_json_from_response` 返回 `None` 时，走原有重试/默认值逻辑（不抛未捕获异常）
- [x] 原有的重试次数（3次）、重试间隔（0.5秒）、默认返回值（单次 `False`、批量全 `False` 列表）保持不变
- [x] 原有的日志输出（INFO/ERROR 级别）保持不变
- [x] 单元测试覆盖三种场景：纯 JSON、```` ```json ````栅栏包裹、混合文本含 JSON
- [x] 单元测试验证 `_extract_json_from_response` 返回值与预期字典一致
- [x] 现有语义分析器相关测试无回归
