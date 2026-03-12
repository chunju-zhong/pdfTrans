# Markdown生成器代码简化重构规格说明

## Why
当前 `markdown_generator.py` 代码存在以下问题：
1. **嵌套函数**：`_generate_chapter_markdowns` 方法中存在 `collect_chapters` 嵌套函数
2. **代码重复**：`generate_markdown` 方法中处理无章节和有章节的两套逻辑高度相似
3. **结构混乱**：方法职责不清晰，部分方法过长
4. **性能考虑**：存在不必要的对象复制和数据遍历

## What Changes
- 移除 `_generate_chapter_markdowns` 中的嵌套函数 `collect_chapters`
- 重构代码结构，统一有章节和无章节的处理流程
- 拆分过长方法，提高代码可读性
- 优化数据组织和遍历逻辑

## Impact
- Affected specs: 现有Markdown生成功能保持不变
- Affected code: `modules/markdown_generator.py`

## ADDED Requirements

### Requirement: 移除嵌套函数
系统SHALL将所有嵌套函数重构为模块级函数或类方法

#### Scenario: 移除嵌套函数
- **GIVEN** 当前代码中存在嵌套函数 `collect_chapters`
- **WHEN** 重构该函数为类方法
- **THEN** 功能保持不变，代码中不存在嵌套函数定义

### Requirement: 代码结构简化
系统SHALL统一有章节和无章节的Markdown生成逻辑

#### Scenario: 统一处理流程
- **GIVEN** 当前存在两套处理流程（按章节和不按章节）
- **WHEN** 重构为统一的处理框架
- **THEN** 代码量减少，逻辑更清晰

## MODIFIED Requirements

### Requirement: Markdown生成功能
- **保持不变**：生成的Markdown格式和内容
- **保持不变**：图像、表格的定位逻辑
- **保持不变**：章节索引文件的生成

## REMOVED Requirements

### Requirement: 嵌套函数
- **Reason**: 项目规范要求避免嵌套函数，提高代码可读性和可维护性
- **Migration**: 将嵌套函数重构为类方法

## 实现要点

1. **将 `collect_chapters` 提取为类方法**：
   ```python
   def _collect_all_chapters(self, chapters):
       """递归收集所有章节，包括子章节"""
       all_chapters = []
       for chapter in chapters:
           all_chapters.append(chapter)
           if chapter.children:
               all_chapters.extend(self._collect_all_chapters(chapter.children))
       return all_chapters
   ```

2. **统一处理流程**：
   - 提取公共的页面内容处理逻辑
   - 减少代码重复

3. **性能优化**：
   - 减少不必要的数据复制
   - 使用更高效的数据结构
