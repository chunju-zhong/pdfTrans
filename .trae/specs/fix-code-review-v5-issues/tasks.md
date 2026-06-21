# Tasks

- [x] Task 1: 移除`_compute_table_layout`中Step 1无用的`row_line_counts`变量
  - [x] 删除第955行`row_line_counts = []`
  - [x] 删除第965行`row_line_counts.append(max_lines)`
- [x] Task 2: 截断逻辑计数方式改为显式`attempts`计数器
  - [x] CJK截断：将`if (len(cell_text) - 1 - n) >= max_truncation_attempts`改为`attempts += 1; if attempts >= max_truncation_attempts`
  - [x] 英文截断：将`if (len(words) - 1 - n) >= max_truncation_attempts`改为`attempts += 1; if attempts >= max_truncation_attempts`
- [x] Task 3: 恢复`_extract_json`第三级容错
  - [x] 在markdown代码块提取失败后，添加首尾花括号匹配逻辑：`text.find('{')`/`text.rfind('}')`
- [x] Task 4: `from __future__ import annotations`移至编码声明之后
  - [x] 将第1行的`from __future__ import annotations`移到`# -*- coding: utf-8 -*-`之后
- [x] Task 5: 多bbox拆分段落数不匹配时的fallback处理
  - [x] 当`len(paragraphs) < len(bboxes)`时，用空文本填充剩余bbox
  - [x] 当`len(paragraphs) > len(bboxes)`时，将多余段落合并到最后一个段落
- [x] Task 6: 运行测试验证所有修改

# Task Dependencies
- Task 6 depends on Task 1-5
