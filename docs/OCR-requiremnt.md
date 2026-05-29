工具增加新功能：PDF OCR 提取内容并翻译

## 第一阶段 ：集成传统OCR提取内容
多引擎融合策略 ：根据源语言类型自动选择最优OCR引擎PaddleOCR
添加OCR模式，配置开关选择是否使用OCR提取PDF内容，否则使用原有文本模式提取

## 第二阶段 ：添加LLM-based OCR提取内容
使用OpenAI兼容API调用Qwen3-VL-30B-A3B-Instruct/Qwen2.5-VL/Qwen3-VL/DeepSeek OCR模型，实现内容提取
支持AIPing和Silicon Flow平台上的模型调用
增加LLM OCR模式及开关，如果OCR开关开启，且LLM OCR模式开关开启，使用LLM OCR模式提取内容，否则使用传统OCR

## 第三阶段 ：实现混合策略，自动选择最优方案
根据源语言和内容复杂程度，自动选择最优的OCR引擎还是LLM模型
