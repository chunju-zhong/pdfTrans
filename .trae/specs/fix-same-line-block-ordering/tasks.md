# Tasks

- [x] Task 1: 为 TextBlock 增加 alignment 属性
  - [x] SubTask 1.1: 在 `models/text_block.py` 的 `__init__` 中增加 `self.alignment = 0`
  - [x] SubTask 1.2: 在 `from_dict` 和 `to_dict` 方法中包含 `alignment` 属性

- [x] Task 2: 新增文本块对齐方式检测函数
  - [x] SubTask 2.1: 在 `modules/extractors/coordinate_utils.py` 中新增 `detect_text_block_alignment(bbox, page_width)` 函数

- [x] Task 3: 提取阶段检测文本块对齐方式（非OCR路径）
  - [x] SubTask 3.1: 在 `modules/pdf_extractor.py` 的 `_extract_text_blocks` 中，创建 TextBlock 后调用 `detect_text_block_alignment` 设置 alignment
  - [x] SubTask 3.2: 确保页面宽度信息可传递到 TextBlock 创建处

- [x] Task 4: 提取阶段检测文本块对齐方式（OCR路径）
  - [x] SubTask 4.1: 在 `modules/ocr/paddle_extractor.py` 的 `_process_page_layout` 中，创建 TextBlock 后调用 `detect_text_block_alignment` 设置 alignment

- [x] Task 5: 语义合并逻辑增加对齐方式检查
  - [x] SubTask 5.1: 在 `merge_semantic_blocks` 中增加对齐方式检查
  - [x] SubTask 5.2: 在 `merge_semantic_blocks_with_llm` 中增加同样的对齐方式检查
  - [x] SubTask 5.3: 在 `merge_semantic_blocks_with_llm_two_phase` 中增加同样的对齐方式检查
  - [x] SubTask 5.4: 添加日志记录对齐方式检查结果

- [x] Task 6: PDF 生成使用检测到的对齐方式
  - [x] SubTask 6.1: 在 `modules/pdf_generator.py` 中，将硬编码的 `alignment = 0` 替换为从 TextBlock 获取的 alignment 值

- [x] Task 7: 修复对齐检测逻辑——左/右对齐优先于居中
  - [x] SubTask 7.1: 修改 `detect_text_block_alignment` 函数，将检测顺序从"居中→右对齐→左对齐"改为"左对齐→右对齐→居中"
  - [x] SubTask 7.2: 将左对齐阈值从 10% 调整为 15%（与右对齐一致）
  - [x] SubTask 7.3: 居中检测增加前提条件：不满足左/右对齐条件时才判定居中

# Task Dependencies

- Task 7 依赖 Task 2（需要修改已创建的 detect_text_block_alignment 函数）
- Task 7 修复后，Task 3-6 的对齐检测将自动使用修正后的逻辑

- [x] Task 8: 重写 LLM 语义分析提示词——增加边界识别能力
  - [x] SubTask 8.1: 重写 `_generate_batch_semantic_analysis_prompt`：新增语义角色判断（正文/标题/签名行/列表项）、合并决策矩阵、5个边界场景 few-shot 示例（签名行边界、引用内合并、列表项边界、列表续行、标题边界）
  - [x] SubTask 8.2: 重写 `_generate_semantic_analysis_prompt`（单对版本）：应用同样的语义角色判断逻辑和示例
  - [x] SubTask 8.3: 确认 `AipingSemanticAnalyzer` 继承基类提示词（已确认：未重写提示词方法，修改基类即可自动生效）

- [ ] Task 9: 验证 LLM 提示词改进效果
  - [ ] SubTask 9.1: 使用第3页 Praise 页面的文本块数据验证：签名行不与下一引用正文合并
  - [ ] SubTask 9.2: 验证同一引用内的句子延续仍正确合并
  - [ ] SubTask 9.3: 验证列表项、标题等边界的识别正确性
  - [ ] SubTask 9.4: 运行完整翻译流程检查第3页输出语序是否正确

- [x] Task 10: 修复拆分后文本块 bbox 越界问题
  - [x] SubTask 10.1: 在 `services/translation_service.py` 的拆分块 bbox 重算逻辑（第415-417行）中，增加 x1 上限保护：`min(original_bbox[0] + max_width, original_bbox[2])`，确保不超过原始块的 x1
  - [ ] SubTask 10.2: 验证修复后 Madhav 引用末句 "涵盖了该领域所有重要的理念与实用知识。" 不再超出页面右边界

- [ ] Task 11: 修复 LLM 提示词缺少"正文段落边界"检测场景（第22页 Acknowledgments 语序混乱）
  - [x] SubTask 11.1: 在 `_generate_batch_semantic_analysis_prompt` 中新增 **示例F：段落边界** few-shot 示例——展示两个完整正文段落之间不应合并的模式（前段以句号结尾 + 后段以大写字母开头新句子 + 话题转换）
  - [x] SubTask 11.2: 强化"进一步判断"标准——在决策矩阵的 `[进一步判断]` 说明中增加明确的段落边界检测规则：① 前块以句号/感叹号/问号等终结标点结尾；② 后块以大写字母开头的新句子；③ 后块引入全新话题或主语
  - [x] SubTask 11.3: 在 `_generate_semantic_analysis_prompt`（单对版本）中同步添加相同的段落边界示例和规则
  - [ ] SubTask 11.4: 运行翻译验证第22页 Acknowledgments 各段落独立不被合并

- [x] Task 12: 移除 split_translated_result 的"分段长度平衡调整"步骤——该步骤破坏文本顺序
  - [x] SubTask 12.1: 移除 `split_translated_result()` 中 L660-709 的"分段长度平衡调整"代码块，该逻辑从最后一个块尾部提取文本均匀分配到前面各块，直接导致语序混乱
  - [ ] SubTask 12.2: 运行翻译验证第22页拆分结果不再出现语序错乱

- [x] Task 13: 优化 LLM 提示词为语言无关——使用通用示例 + 语言无关规则描述
  - [x] SubTask 13.1: 签名行/列表项特征描述改为语言无关（不再依赖 `—`/`•`/`-` 等特定符号）
  - [x] SubTask 13.2: few-shot 示例理由改为通用描述（不再引用"大写字母/小写字母"等英文特有概念）
  - [x] SubTask 13.3: [进一步判断]规则描述改为语言无关（"独立的新主语/新话题"替代"大写字母开头"）

# Task Dependencies (续)

- Task 9 依赖 Task 8（需要先完成提示词重写才能验证效果）
- Task 10 可独立实施，不依赖其他任务
- Task 11 依赖 Task 8（在 Task 8 的提示词框架上补充缺失场景）
- Task 12 可独立实施，不依赖其他任务（防御性修复，即使合并正确也应在句子边界断开）
- Task 13 依赖 Task 8（在 Task 8 的提示词框架上优化语言无关性）
