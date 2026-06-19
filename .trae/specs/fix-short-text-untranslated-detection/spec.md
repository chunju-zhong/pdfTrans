# 修复短文本未翻译检测缺失 Spec

## Why（已验证的事实 + 根因分析）

### 日志事实
当 `semantic_merge=False` 时，日志证实（两次运行完全复现）：

1. 原始块 16 原文：`Effluent standard Separation option`（35字符，**不含** `|||`）
2. 翻译请求发送给 LLM 的内容：同上（无 `|||`）
3. LLM 返回：`Effluent standard ||| Separation option`（39字符，**LLM 自行添加**了 `|||`）
4. 英文内容完全未翻译
5. 现有检测（`translation_service.py:582`）仅做 `translated == original` → 因 `|||` 差异被绕过

### 对比分析：为什么只有 Block 16 出问题？

同一运行中其他短块均正常翻译：
- Block 8: `d. Temperature`（14字符）→ `d. 温度` ✅ 有列表前缀
- Block 10: `Design example:`（15字符）→ `设计示例：` ✅ 有冒号结尾
- Block 16: `Effluent standard Separation option`（35字符）→ `Effluent standard ||| Separation option` ❌ **两个裸名词短语，无标点、无列表标记**

### 根因分析：LLM 为何自行添加 `|||`？

经排查代码排除以下可能：
- ~~输入文本含 `|||`~~ → 日志确认原文无 `|||`
- ~~代码后处理添加~~ → 仅 `translate_table_row()` 中有 `|||` 拼接逻辑，但此走的是 `translate_original_block()` 路径
- ~~aiping extra_body 特殊配置~~ → `AIPING_EXTRA_BODY` 仅含 provider 路由参数，无 prompt 相关项

**三因素叠加：**

1. **系统提示词规则 16 的概念泄漏**：规则 16 向模型引入了 `|||` 作为"表格单元格分隔符"的概念。虽然触发条件是"输入包含 `|||`"，但模型在 high temperature 下可能过度泛化此模式——当看到两个独立名词短语（类似表格表头格式）时，主动套用 `|||` 格式。

2. **aiping 的 temperature=0.7 过高**：对比 siliconflow 使用 `temperature=0.1`（确定性输出），aiping 用 `0.7`（创造性输出）。高温度使模型更容易对输入做出"创造性解释"，包括自行添加格式符号。

3. **输入文本的特殊结构**：Block 16 是唯一一个"两个裸名词短语 + 空格分隔 + 无任何标点/列表标记"的文本。模型将其识别为类表格结构（如图表标签），于是用学到的 `|||` 格式化，同时因视为"专业术语"而保留英文不译。

## What Changes
### 变更 1：降低 aiping 翻译器温度
- 文件：`modules/aiping_translator.py:92`
- 将 `temperature` 从 `0.7` 降低到 `0.1`（与 siliconflow 一致）
- 将 `top_p` 从 `0.8` 降低到 `0.9`
- 目的：减少 LLM 创造性输出，降低自行添加 `|||` 等非预期格式的概率

### 变更 2：增强未翻译检测
- 新增 `_is_translation_unchanged(translated_text, original_text)` 辅助函数
- 修改 `translate_original_block()` （~L582）和 `translate_merged_block()` （~L360）调用新函数增强检测
- 检测到未翻译时记录 WARNING

## Impact
- Affected code:
  - `modules/aiping_translator.py` — temperature/top_p 参数
  - `services/translation_service.py` — 两处检测逻辑
- 不影响其他模块

## ADDED Requirements

### Requirement: 降低 aiping temperature
`aiping_translator.py` 中 `temperature` 从 `0.7` 改为 `0.1`，`top_p` 从 `0.8` 改为 `0.9`。

### Requirement: 未翻译智能检测函数
`_is_translation_unchanged(translated_text, original_text)` — 判断翻译结果是否实质上未翻译。

- 输入含 `|||` 但各分段均为原文 → True
- 正常翻译（目标语言）→ False
- 含 `|||` 的正常翻译 → False

### Requirement: 两处检测点升级
`translate_original_block()` 和 `translate_merged_block()` 的翻译后验证从简单 `==` 升级为新函数调用。
