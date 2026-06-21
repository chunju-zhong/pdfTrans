# 保存表格单元格估算行数并先算行高再算列宽 Spec

## Why
LLM OCR识别阶段在`_parse_html_table`中采用"先列宽后行高"的单向计算，但列宽分配是猜测性的，可能导致行高估算不准。更合理的做法是：先根据原始内容行数确定行高（行高受bbox约束是硬限制），再根据行高反推每列需要多少宽度才能让文本在给定行数内换行完成。这样行高优先保证，列宽为行高服务。

## What Changes
- 在PdfCell模型中新增`estimated_lines`字段，保存识别阶段计算的估算行数
- 在`_parse_html_table`中将"先列宽后行高"改为"先行高后列宽"的迭代优化：先估算每行行数和行高，钳位行高到bbox后，反推每列需要的最小宽度
- 在`_draw_translated_table`中利用`estimated_lines`优化字体大小选择和溢出预判

## Impact
- Affected code: `models/extraction.py` 中 PdfCell 类
- Affected code: `modules/ocr/llm_extractor.py` 中 `_parse_html_table` 方法
- Affected code: `modules/pdf_generator.py` 中 `_draw_translated_table` 方法
- 影响范围：所有LLM OCR识别的表格

## ADDED Requirements

### Requirement: 先行高后列宽的迭代优化计算
`_parse_html_table` SHALL 使用"先行高后列宽"的迭代优化算法，而非"先列宽后行高"。

#### Scenario: 迭代优化流程
- **WHEN** 解析HTML表格得到所有单元格文本内容
- **THEN** 系统应按以下迭代流程计算行高和列宽：

  **Step 1: 估算每行行数和行高**
  - 对每行的每个单元格，估算其文本在单行显示时的宽度（`display_width`）
  - 初始假设每列等宽（`table_width / n_cols`），估算每个单元格的换行行数
  - 每行的行数 = 该行所有单元格中最大的估算行数
  - 行高 = 行数 × 单行高度

  **Step 2: 钳位行高到原始bbox**
  - 如果总行高 > bbox高度，按比例缩小
  - 如果总行高 <= bbox高度，按比例放大填满

  **Step 3: 根据行高反推列宽**
  - 钳位后每行的实际可用行数 = 钳位后行高 / 单行高度
  - 对每个单元格，计算在给定行数下需要的最小列宽：`min_col_width = display_width / available_lines`
  - 对每列，取该列所有单元格的最大`min_col_width`作为该列的权重
  - 按权重比例分配表格总宽度到各列
  - 钳位列宽：最小10%，最大50%

  **Step 4: 用新列宽重新估算行数和行高**
  - 用Step 3得到的列宽重新计算每个单元格的换行行数
  - 重新计算每行行高

  **Step 5: 重新钳位行高到原始bbox**
  - 同Step 2

  **Step 6: 检查收敛**
  - 如果行高变化 < 0.5pt 或达到最大迭代次数（3次），停止
  - 否则回到Step 3，用新行高重新反推列宽

#### Scenario: 列宽反推策略
- **WHEN** 根据行高反推列宽
- **THEN** 每个单元格所需最小列宽 = `ceil(display_width / available_lines)` × 字体大小系数
- **AND** 合并单元格的所需宽度按`col_span`均分到各列
- **AND** 每列权重 = 该列所有单元格所需宽度的最大值
- **AND** 列宽仍需满足最小10%、最大50%的钳位约束

#### Scenario: 迭代收敛保障
- **WHEN** 迭代达到最大次数（3次）或行高变化 < 0.5pt
- **THEN** 停止迭代，使用当前列宽和行高
- **AND** 最终行高仍需钳位到原始bbox范围内

### Requirement: PdfCell保存估算行数
PdfCell SHALL 新增`estimated_lines`字段，记录该单元格在最终列宽下估算的文本换行行数。

#### Scenario: 识别阶段计算估算行数
- **WHEN** `_parse_html_table`迭代优化完成后
- **THEN** 每个单元格的最终估算行数应保存到`estimated_lines`字段
- **AND** 对于空单元格，`estimated_lines`默认为0
- **AND** 对于有文本的单元格，`estimated_lines = max(1, ceil(display_width / span_width))`

#### Scenario: PdfCell序列化/反序列化
- **WHEN** PdfCell通过`to_dict()`序列化
- **THEN** 输出字典应包含`estimated_lines`字段
- **WHEN** PdfCell通过`from_dict()`反序列化
- **THEN** 应从字典中读取`estimated_lines`字段，默认为0

### Requirement: 绘制阶段利用估算行数优化渲染
`_draw_translated_table` SHALL 利用PdfCell的`estimated_lines`字段优化字体大小选择。

#### Scenario: 根据估算行数预判单元格容量
- **WHEN** 绘制表格单元格文本
- **THEN** 系统应利用`estimated_lines`和单元格高度计算可容纳的最大字体大小
- **AND** 如果估算行数×单行高度 > 单元格高度，说明文本可能溢出，应直接使用较小的初始字体

#### Scenario: 估算行数不可用时的回退
- **WHEN** PdfCell的`estimated_lines`为0或不存在（旧数据兼容）
- **THEN** 绘制阶段应回退到现有的5次缩小字体+截断逻辑，行为不变

## MODIFIED Requirements

### Requirement: _parse_html_table 列宽行高计算
原有策略（先列宽后行高单向计算）修改为：先行高后列宽的迭代优化，先确定行高（受bbox约束），再根据行高反推列宽，迭代直到收敛。

### Requirement: PdfCell数据模型
原有PdfCell字段新增`estimated_lines`字段。
