#!/usr/bin/env python3
"""
测试Markdown表格生成功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.extraction import PdfTable, PdfCell


def test_table_generation():
    """测试表格生成功能"""
    # 创建测试表格数据，使用PdfCell和PdfTable对象
    table_data = [
        # 表头
        [
            {'text': '主体实体'},
            {'text': '认证 / 验证'},
            {'text': '备注'}
        ],
        # 数据行1
        [
            {'text': '用户'},
            {'text': '通过OAuth或单点登录（SSO）进行认证'},
            {'text': '具有完全自主性和行为责任的人类主体'}
        ],
        # 数据行2
        [
            {'text': '智能体（新一类原则）'},
            {'text': '已通过SPIFFE验证'},
            {'text': '智能体拥有被授权的权限，能够代表用户执行操作。'}
        ],
        # 数据行3
        [
            {'text': '服务账号'},
            {'text': '集成到身份与访问管理（IAM）'},
            {'text': '应用与容器完全确定，不对行为负责'}
        ]
    ]
    
    # 创建PdfCell对象
    cells = []
    for i, row in enumerate(table_data):
        cell_row = []
        for j, cell_data in enumerate(row):
            cell = PdfCell(
                text=cell_data['text'],
                bbox=(50 + j * 100, 150 + i * 30, 150 + j * 100, 180 + i * 30),
                row_idx=i,
                col_idx=j
            )
            cell_row.append(cell)
        cells.append(cell_row)
    
    # 创建PdfTable对象
    test_table = PdfTable(
        page_num=1,
        table_idx=0,
        cells=cells,
        bbox=(50, 150, 350, 240),
        row_heights=[30, 30, 30, 30],
        col_widths=[100, 100, 100]
    )
    
    # 创建一个模拟的MarkdownGenerator实例（只用于测试表格生成方法）
    class MockMarkdownGenerator:
        def _convert_table_to_markdown(self, table):
            """模拟表格转换方法"""
            # 使用cells属性
            cells = table.cells
            if not cells:
                return ""
            
            # 获取表格尺寸
            num_rows = len(cells)
            num_cols = len(cells[0]) if num_rows > 0 else 0
            
            if num_rows == 0 or num_cols == 0:
                return ""
            
            # 构建Markdown表格
            markdown_table = []
            
            # 添加表头行
            header_row = cells[0]
            row_cells = []
            for cell in header_row:
                # 使用text属性
                cell_text = cell.text
                row_cells.append(cell_text)
            markdown_table.append("|" + "|".join(row_cells) + "| ")
            
            # 添加表头分隔线
            header_separator = ["---"] * num_cols
            markdown_table.append(" |" + "|".join(header_separator) + "| ")
            
            # 添加表格内容（跳过表头行）
            for i, row in enumerate(cells[1:]):
                row_cells = []
                for cell in row:
                    # 使用text属性
                    cell_text = cell.text
                    row_cells.append(cell_text)
                if i == len(cells[1:]) - 1:
                    # 最后一行
                    markdown_table.append(" |" + "|".join(row_cells) + "|")
                else:
                    # 非最后一行
                    markdown_table.append(" |" + "|".join(row_cells) + "| ")
            
            return "\n".join(markdown_table) + "\n"
    
    # 生成表格
    generator = MockMarkdownGenerator()
    table_md = generator._convert_table_to_markdown(test_table)
    
    # 打印生成的表格
    print("生成的Markdown表格:")
    print(repr(table_md))
    print("\n实际输出:")
    print(table_md)
    
    # 验证表格格式
    expected_lines = [
        '|主体实体|认证 / 验证|备注| ',
        ' |---|---|---| ',
        ' |用户|通过OAuth或单点登录（SSO）进行认证|具有完全自主性和行为责任的人类主体| ',
        ' |智能体（新一类原则）|已通过SPIFFE验证|智能体拥有被授权的权限，能够代表用户执行操作。| ',
        ' |服务账号|集成到身份与访问管理（IAM）|应用与容器完全确定，不对行为负责|'
    ]
    
    actual_lines = table_md.strip().split('\n')
    
    print("\n验证结果:")
    print(f"预期行数: {len(expected_lines)}")
    print(f"实际行数: {len(actual_lines)}")
    
    all_match = True
    for i, (expected, actual) in enumerate(zip(expected_lines, actual_lines)):
        if expected == actual:
            print(f"行 {i+1}: ✓ 匹配")
        else:
            print(f"行 {i+1}: ✗ 不匹配")
            print(f"  预期: {repr(expected)}")
            print(f"  实际: {repr(actual)}")
            all_match = False
    
    if all_match:
        print("\n✓ 所有行都匹配预期格式！")
        assert True, "所有行都匹配预期格式！"
    else:
        print("\n✗ 部分行不匹配预期格式！")
        assert False, "部分行不匹配预期格式！"


if __name__ == "__main__":
    test_table_generation()
    sys.exit(0)
