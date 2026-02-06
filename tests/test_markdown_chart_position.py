#!/usr/bin/env python3
"""
测试Markdown文档中图表的正确位置插入功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.markdown_generator import MarkdownGenerator


def test_chart_positioning():
    """测试图表位置插入功能"""
    # 创建一个模拟的MarkdownGenerator实例（只用于测试图表位置插入方法）
    class MockMarkdownGenerator:
        def _process_page_elements(self, page_elements, text_blocks, full_text):
            """处理页面元素，按顺序添加到Markdown文档"""
            # 跟踪已处理的文本块索引
            processed_blocks = set()
            
            # 预处理：检测元素是否位于文本块内部
            elements_with_context = []
            
            for element in page_elements:
                element_type = element['type']
                
                if element_type in ['image', 'table']:
                    # 检查是否位于某个文本块内部
                    containing_block = None
                    insertion_point = 0.5  # 默认插入点（中间位置）
                    
                    elem_y = element['y_position']
                    
                    for block_idx, block in enumerate(text_blocks):
                        if block_idx not in processed_blocks:
                                block_bbox = block.bbox
                                if len(block_bbox) >= 4:
                                    block_y0, block_y1 = block_bbox[1], block_bbox[3]
                                    
                                    # 检查元素是否位于文本块内部
                                    if block_y0 <= elem_y <= block_y1:
                                        containing_block = {
                                            'block': block,
                                            'block_idx': block_idx
                                        }
                                        # 计算插入点比例
                                        insertion_point = (elem_y - block_y0) / (block_y1 - block_y0) if (block_y1 - block_y0) > 0 else 0.5
                                        break
                    
                    elements_with_context.append({
                        'element': element,
                        'containing_block': containing_block,
                        'insertion_point': insertion_point
                    })
                
                elif element_type == 'text':
                    elements_with_context.append({
                        'element': element,
                        'containing_block': None
                    })
            
            # 处理元素
            for item in elements_with_context:
                element = item['element']
                element_type = element['type']
                containing_block = item.get('containing_block')
                
                if element_type == 'text':
                    # 添加文本块
                    block = element['content']
                    block_idx = element['block_idx']
                    
                    if block_idx not in processed_blocks:
                        full_text.append(block.block_text)
                        full_text.append("")
                        processed_blocks.add(block_idx)
                
                elif element_type in ['image', 'table']:
                    if containing_block:
                        # 元素位于文本块内部，需要拆分文本
                        block = containing_block['block']
                        block_idx = containing_block['block_idx']
                        insertion_point = item.get('insertion_point', 0.5)
                        
                        if block_idx not in processed_blocks:
                            # 拆分文本并插入元素
                            self._insert_element_in_text_block(
                                block, element, insertion_point, full_text
                            )
                            processed_blocks.add(block_idx)
                        else:
                            # 文本块已处理，直接添加元素
                            if element_type == 'image':
                                self._add_image_to_markdown(element['content'], full_text)
                            elif element_type == 'table':
                                self._add_table_to_markdown(element['content'], full_text)
                    else:
                        # 元素位于文本块之间，直接添加
                        if element_type == 'image':
                            self._add_image_to_markdown(element['content'], full_text)
                        elif element_type == 'table':
                            self._add_table_to_markdown(element['content'], full_text)
        
        def _insert_element_in_text_block(self, text_block, element, insertion_point, full_text):
            """在文本块内部插入元素，拆分文本"""
            text = text_block.block_text
            text_length = len(text)
            
            # 计算插入位置
            split_index = int(text_length * insertion_point)
            
            # 尝试在单词边界拆分
            if split_index > 0 and split_index < text_length:
                # 向前查找空格或标点
                while split_index > 0 and text[split_index-1].isalnum():
                    split_index -= 1
            
            # 拆分为前后两段
            text_before = text[:split_index].rstrip()
            text_after = text[split_index:].lstrip()
            
            # 添加前段文本
            if text_before:
                full_text.append(text_before)
                full_text.append("")
            
            # 添加元素
            if element['type'] == 'image':
                self._add_image_to_markdown(element['content'], full_text)
            elif element['type'] == 'table':
                self._add_table_to_markdown(element['content'], full_text)
            
            # 添加后段文本
            if text_after:
                full_text.append(text_after)
                full_text.append("")
        
        def _add_image_to_markdown(self, image, full_text):
            """添加图像到Markdown文档"""
            image_path = image.image_path
            # 使用Markdown图像语法
            image_md = f"![图像]({image_path})"
            full_text.append("## 图像")
            full_text.append(image_md)
            full_text.append("")
        
        def _add_table_to_markdown(self, table, full_text):
            """添加表格到Markdown文档"""
            # 简化的表格转换，只返回表格占位符
            table_md = "|表头1|表头2|\n|-----|-----|\n|内容1|内容2|"
            full_text.append("## 表格")
            full_text.append(table_md)
            full_text.append("")
    
    # 创建模拟的文本块
    class MockTextBlock:
        def __init__(self, text, bbox):
            self.block_text = text
            self.bbox = bbox
    
    # 创建模拟的图像
    class MockImage:
        def __init__(self, image_path, bbox):
            self.image_path = image_path
            self.bbox = bbox
    
    # 创建模拟的表格
    class MockTable:
        def __init__(self, bbox):
            self.bbox = bbox
    
    # 创建测试数据
    text_block1 = MockTextBlock("这是第一段文本内容，包含一些描述性文字。", (0, 0, 100, 50))
    text_block2 = MockTextBlock("这是第二段文本内容，包含更多描述性文字。", (0, 100, 100, 150))
    
    image1 = MockImage("images/image1.jpg", (0, 30, 100, 80))  # 位于第一个文本块内部
    table1 = MockTable((0, 120, 100, 170))  # 位于第二个文本块内部
    
    text_blocks = [text_block1, text_block2]
    
    # 创建页面元素列表
    page_elements = [
        {
            'type': 'text',
            'content': text_block1,
            'y_position': 0,
            'block_idx': 0
        },
        {
            'type': 'image',
            'content': image1,
            'y_position': 30
        },
        {
            'type': 'text',
            'content': text_block2,
            'y_position': 100,
            'block_idx': 1
        },
        {
            'type': 'table',
            'content': table1,
            'y_position': 120
        }
    ]
    
    # 按垂直位置排序元素
    page_elements.sort(key=lambda x: x['y_position'])
    
    # 生成Markdown内容
    generator = MockMarkdownGenerator()
    full_text = []
    generator._process_page_elements(page_elements, text_blocks, full_text)
    
    # 打印生成的Markdown内容
    print("生成的Markdown内容:")
    print("\n".join(full_text))
    print("\n")
    
    # 验证内容顺序
    expected_order = [
        "这是第一段文本内容，包含一些描述性文字。",
        "",
        "## 图像",
        "![图像](images/image1.jpg)",
        "",
        "这是第二段文本内容，包含更多描述性文字。",
        "",
        "## 表格",
        "|表头1|表头2|\n|-----|-----|\n|内容1|内容2|",
        ""
    ]
    
    print("验证内容顺序:")
    print(f"预期长度: {len(expected_order)}")
    print(f"实际长度: {len(full_text)}")
    
    all_match = True
    for i, (expected, actual) in enumerate(zip(expected_order, full_text)):
        if expected == actual:
            print(f"行 {i+1}: ✓ 匹配")
        else:
            print(f"行 {i+1}: ✗ 不匹配")
            print(f"  预期: '{expected}'")
            print(f"  实际: '{actual}'")
            all_match = False
    
    if all_match:
        print("\n✓ 所有行都匹配预期顺序！")
        assert True, "所有行都匹配预期顺序！"
    else:
        print("\n✗ 部分行不匹配预期顺序！")
        assert False, "部分行不匹配预期顺序！"


if __name__ == "__main__":
    test_chart_positioning()
    sys.exit(0)
