## 修改计划

### 1. 修改目标
- 所有文本提取方法直接返回TextBlock对象，不返回字典
- 简化外部调用，统一使用TextBlock获取完整块的文本及显示相关数据
- 保持返回结构一致性，便于外部调用

### 2. 修改内容

#### 2.1 修改 `extract_text` 方法
- 内部仍使用TextBlock对象处理
- 最终返回结构中直接包含TextBlock对象
- 更新文档字符串，反映新的返回格式

#### 2.2 修改 `extract_page_text` 方法
- 改为使用TextBlock对象
- 移除行级别处理，返回完整块
- 直接返回包含TextBlock对象的结果
- 更新文档字符串

#### 2.3 修改 `extract_text_blocks` 方法
- 改为使用TextBlock对象
- 直接返回包含TextBlock对象的结果
- 更新文档字符串

#### 2.4 统一返回结构
所有文本提取方法将返回类似结构：
```
{
    'total_pages': int,  # PDF总页数
    'pages': [           # 每页信息列表
        {
            'page_num': int,          # 页码
            'text_blocks': [TextBlock, ...]  # 直接返回TextBlock对象列表
        },
        # 更多页面...
    ]
}
```

### 3. 实现步骤
1. 修改 `extract_text` 方法，直接返回TextBlock对象
2. 修改 `extract_page_text` 方法，返回TextBlock对象
3. 修改 `extract_text_blocks` 方法，返回TextBlock对象
4. 更新所有方法的文档字符串
5. 运行测试，确保修改不破坏现有功能

### 4. 预期效果
- 外部调用者可以直接使用TextBlock对象获取所有信息
- 无需解析复杂的字典结构
- 统一的返回格式，便于使用
- 保留所有文本和样式信息

### 5. 测试计划
- 运行现有的PDF提取器测试
- 确保所有测试通过
- 验证返回的TextBlock对象包含完整的信息

### 6. 风险评估
- 可能需要修改调用这些方法的代码
- 但修改后代码会更简洁，便于维护

### 7. 依赖关系
- 已有的TextBlock类
- PyMuPDF库
- 现有的测试用例