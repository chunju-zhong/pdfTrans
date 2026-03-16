# 删除合并块章节相关数据计划

## 任务概述
删除 MergedBlock 模型中的章节信息属性（chapter_id、chapter_title、chapter_level、chapter_number），因为这些属性目前没有被使用。

## 修改步骤

### 1. 修改 models/merged_block.py
- 删除 `__init__` 方法中的章节属性提取代码（第32-36行）
- 删除 `to_dict` 方法中的章节属性返回（第71-74行）

### 2. 验证测试
- 运行 markdown_generator 相关测试，确保功能正常

## 预期结果
- MergedBlock 类不再包含章节相关属性
- 代码逻辑保持不变，因为章节信息是从原始块获取的
- 测试通过
