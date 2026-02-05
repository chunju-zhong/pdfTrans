## 1. 扩展 TextBlock 类
- 在 `models/text_block.py` 中为 TextBlock 类添加 `page_num` 属性
- 更新 `__init__` 方法以接受 `page_num` 参数，默认值为 0
- 更新 `to_dict` 方法以包含 `page_num` 属性

## 2. 修改 translation_service.py
- 在 `translation_service.py` 第 231-236 行，移除字典包装，直接设置 TextBlock 对象的 `page_num` 属性
- 移除未使用的 `index` 字段和 `block_index` 变量

## 3. 更新依赖代码
- 修改 `translation_service.py` 中使用字典结构的位置：
  - 第 301 行：`first_block['page_num']` → `first_block.page_num`
  - 第 336 行：`original_block_info['page_num']` → `original_block_info.page_num`
  - 第 402 行：`block_info['page_num']` → `block_info.page_num`
- 修改 `utils/text_processing.py` 中使用字典结构的代码：
  - 第 46 行：`first_block['text_block']` → `first_block`
  - 第 67 行：`curr_block_info['text_block']` → `curr_block_info`
  - 第 69 行：`prev_block_info['text_block']` → `prev_block_info`
  - 第 59 行：`[first_block]` → `[first_block]` (保持不变)
- 修改 `tests/test_translator.py` 中使用字典结构的代码：
  - 第 61 行：`block['page_num']` → `block.page_num`

## 4. 验证修改
- 运行测试确保所有功能正常工作
- 验证翻译流程是否正确使用 TextBlock 对象的 page_num 属性