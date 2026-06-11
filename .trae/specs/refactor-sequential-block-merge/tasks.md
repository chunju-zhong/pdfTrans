# Tasks

- [x] Task 1: 重构 `_generate_batch_semantic_analysis_prompt` 为顺序块列表模式
  - [x] SubTask 1.1: 修改方法签名，接收 `blocks: list[str]` 而非 `text_pairs: list[tuple]`
  - [x] SubTask 1.2: 重写提示词模板：顺序列出所有块（块1, 块2, ..., 块N），要求 LLM 输出 N-1 个合并判断
  - [x] SubTask 1.3: 在提示词中增加上下文参考指引：判断块 i 与块 i+1 时参考前面块的语义角色和内容
  - [x] SubTask 1.4: 更新输出格式示例为 `{"merge": [true, false, ...]}`，长度为 N-1

- [x] Task 2: 重构 `batch_analyze_semantic_relationship` 接口
  - [x] SubTask 2.1: 修改 `SemanticAnalyzer.batch_analyze_semantic_relationship` 签名，接收 `blocks` 而非 `text_pairs`
  - [x] SubTask 2.2: 修改 `AipingSemanticAnalyzer.batch_analyze_semantic_relationship` 签名和实现
  - [x] SubTask 2.3: 处理边界情况：blocks 长度 ≤ 1 时返回空列表
  - [x] SubTask 2.4: 调整结果数量校验：期望 `len(blocks) - 1` 个结果

- [x] Task 3: 重构 `parallel_batch_analyze` 适配块列表输入与跨批次边界处理
  - [x] SubTask 3.1: 修改签名，接收 `blocks` 而非 `text_pairs`
  - [x] SubTask 3.2: 实现重叠块分批策略：每批（除第一批外）包含前一批最后 1 个块作为上下文重叠
  - [x] SubTask 3.3: 分批逻辑：批次0取 blocks[0:batch_size]，批次k取 blocks[prev_end-1 : prev_end-1+batch_size]（prev_end 为上一批次最后一块的索引+1）
  - [x] SubTask 3.4: 合并批次结果：直接拼接所有批次的判断结果（N块输出N-1个判断，重叠块不产生重复判断）
  - [x] SubTask 3.5: 验证合并后结果总数等于 `len(blocks) - 1`

- [x] Task 4: 重构 `merge_semantic_blocks_with_llm_two_phase` 调用逻辑
  - [x] SubTask 4.1: 将构建 `text_pairs` 改为构建 `block_texts` 列表
  - [x] SubTask 4.2: 调用 `parallel_batch_analyze` 时传入 `block_texts` 而非 `text_pairs`
  - [x] SubTask 4.3: 验证合并判断结果与块的对应关系正确（`merge_decisions[i]` 对应 `block[i]` 与 `block[i+1]`）

- [x] Task 5: 重构 `merge_semantic_blocks_with_llm` 调用逻辑
  - [x] SubTask 5.1: 将构建 `text_pairs` 改为构建 `block_texts` 列表
  - [x] SubTask 5.2: 调用 `batch_analyze_semantic_relationship` 时传入 `blocks` 而非 `text_pairs`
  - [x] SubTask 5.3: 验证合并判断结果与块的对应关系正确

- [x] Task 6: 更新测试
  - [x] SubTask 6.1: 更新 `tests/test_batch_semantic_analysis.py` 适配新接口
  - [x] SubTask 6.2: 更新 `tests/test_semantic_analyzer.py` 适配新接口
  - [x] SubTask 6.3: 更新 `tests/test_two_phase_merge.py` 适配新接口
  - [x] SubTask 6.4: 新增测试用例验证上下文感知合并判断
  - [x] SubTask 6.5: 新增测试用例验证跨批次边界重叠块策略的正确性

# Task Dependencies

- [Task 2] depends on [Task 1] — 接口变更依赖提示词重构
- [Task 3] depends on [Task 2] — 并行分析依赖新接口签名
- [Task 4] depends on [Task 3] — 两阶段合并依赖并行分析
- [Task 5] depends on [Task 2] — 单批次合并依赖新接口签名
- [Task 6] depends on [Task 4, Task 5] — 测试依赖实现完成
