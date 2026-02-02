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
    
    def test_clean_xml_compatible_text(self):
        """测试清理XML兼容文本的方法
        
        验证 _clean_xml_compatible_text 方法能够正确清理XML不兼容的字符。
        """
        # 测试用例1：包含控制字符的文本
        test_text1 = "Hello\x00World\x01"
        result1 = self.docx_generator._clean_xml_compatible_text(test_text1)
        assert result1 == "HelloWorld", "控制字符应该被移除"
        
        # 测试用例2：包含NULL字节的文本
        test_text2 = "Test\x00String"
        result2 = self.docx_generator._clean_xml_compatible_text(test_text2)
        assert result2 == "TestString", "NULL字节应该被移除"
        
        # 测试用例3：包含制表符、换行符和回车符的文本（应该保留）
        test_text3 = "Line1\tTabbed\nLine2\rLine3"
        result3 = self.docx_generator._clean_xml_compatible_text(test_text3)
        assert result3 == test_text3, "制表符、换行符和回车符应该被保留"
        
        # 测试用例4：包含Unicode字符的文本（应该保留）
        test_text4 = "Hello 世界 🌍"
        result4 = self.docx_generator._clean_xml_compatible_text(test_text4)
        assert result4 == test_text4, "Unicode字符应该被保留"
        
        # 测试用例5：空字符串
        test_text5 = ""
        result5 = self.docx_generator._clean_xml_compatible_text(test_text5)
        assert result5 == "", "空字符串应该返回空字符串"
        
        # 测试用例6：None值
        test_text6 = None
        result6 = self.docx_generator._clean_xml_compatible_text(test_text6)
        assert result6 == "", "None值应该返回空字符串"
        
        # 测试用例7：正常文本（应该保持不变）
        test_text7 = "Normal text with spaces and punctuation!"
        result7 = self.docx_generator._clean_xml_compatible_text(test_text7)
        assert result7 == test_text7, "正常文本应该保持不变"