import os
import tempfile
import pytest
from modules.docx_generator import DocxGenerator
from models.extraction import PdfPage
from models.text_block import TextBlock

class TestDocxGenerator:
    """测试Word生成器"""
    
    def setup_method(self):
        """设置测试环境"""
        self.docx_generator = DocxGenerator()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_generate_docx(self):
        """测试生成Word文档"""
        # 创建测试数据
        text_block1 = TextBlock(
            block_no=1,
            text="这是测试文本块1",
            bbox=(100, 100, 300, 120),
            block_type=0
        )
        text_block1.update_style(
            font="Arial",
            font_size=12,
            color=0,
            flags=0
        )
        
        text_block2 = TextBlock(
            block_no=2,
            text="这是测试文本块2",
            bbox=(100, 130, 300, 150),
            block_type=0
        )
        text_block2.update_style(
            font="Times New Roman",
            font_size=14,
            color=0xFF0000,
            flags=1
        )
        
        pdf_page = PdfPage(
            page_num=1,
            text_blocks=[text_block1, text_block2]
        )
        
        translated_content = {
            'blocks': [pdf_page],
            'tables': []
        }
        
        # 生成Word文件路径
        output_docx_path = os.path.join(self.temp_dir, "test_output.docx")
        
        # 调用生成方法
        self.docx_generator.generate_docx(translated_content, [], output_docx_path)
        
        # 验证文件是否生成
        assert os.path.exists(output_docx_path), "Word文件未生成"
        assert os.path.getsize(output_docx_path) > 0, "Word文件为空"
        
        print(f"Word文件生成成功: {output_docx_path}")