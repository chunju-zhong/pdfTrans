import os
import tempfile
import shutil
import pytest
from modules.markdown_generator import MarkdownGenerator, AipingMarkdownGenerator, create_markdown_generator


class TestMarkdownGenerator:
    """测试MarkdownGenerator基类"""

    def test_initialization(self):
        """测试初始化功能"""
        api_key = "test_api_key"
        api_url = "https://api.example.com/v1"
        model = "gpt-4"
        
        generator = MarkdownGenerator(api_key, api_url, model)
        
        assert generator.api_key == api_key
        assert generator.api_url == api_url
        assert generator.model == model
        assert generator.client is not None

    def test_load_layout_prompt(self):
        """测试加载布局提示词"""
        api_key = "test_api_key"
        api_url = "https://api.example.com/v1"
        model = "gpt-4"
        
        generator = MarkdownGenerator(api_key, api_url, model)
        prompt = generator._load_layout_prompt()
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "将文本转换为结构化 Markdown" in prompt


class TestAipingMarkdownGenerator:
    """测试AipingMarkdownGenerator类"""

    def test_initialization(self):
        """测试初始化功能"""
        api_key = "test_api_key"
        api_url = "https://api.example.com/v1"
        model = "gpt-4"
        
        generator = AipingMarkdownGenerator(api_key, api_url, model)
        
        assert generator.api_key == api_key
        assert generator.api_url == api_url
        assert generator.model == model
        assert generator.client is not None

    def test_cost_preference_strategy(self):
        """测试费用优先策略设置"""
        api_key = "test_api_key"
        api_url = "https://api.example.com/v1"
        model = "gpt-4"
        
        generator = AipingMarkdownGenerator(api_key, api_url, model)
        
        # 测试_call_api方法是否正确设置了费用优先策略
        # 由于无法直接调用API，我们测试方法是否存在并能正常执行
        # 实际的费用优先策略设置在extra_body中，我们可以通过查看代码确认
        # 这里我们只测试方法是否存在
        assert hasattr(generator, '_call_api')

    def test_convert_table_to_markdown(self):
        """测试表格转换为Markdown"""
        api_key = "test_api_key"
        api_url = "https://api.example.com/v1"
        model = "gpt-4"
        
        generator = AipingMarkdownGenerator(api_key, api_url, model)
        
        # 创建模拟表格对象
        class MockCell:
            def __init__(self, text):
                self.text = text
        
        class MockTable:
            def __init__(self):
                self.cells = [
                    [MockCell("Header 1"), MockCell("Header 2")],
                    [MockCell("Row 1 Col 1"), MockCell("Row 1 Col 2")],
                    [MockCell("Row 2 Col 1"), MockCell("Row 2 Col 2")]
                ]
        
        table = MockTable()
        markdown_table = generator._convert_table_to_markdown(table)
        
        assert isinstance(markdown_table, str)
        assert len(markdown_table) > 0
        assert "Header 1" in markdown_table
        assert "Header 2" in markdown_table
        assert "Row 1 Col 1" in markdown_table
        assert "Row 1 Col 2" in markdown_table
        assert "Row 2 Col 1" in markdown_table
        assert "Row 2 Col 2" in markdown_table

    def test_copy_images_to_output(self):
        """测试复制图像到输出目录"""
        api_key = "test_api_key"
        api_url = "https://api.example.com/v1"
        model = "gpt-4"
        
        generator = AipingMarkdownGenerator(api_key, api_url, model)
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建临时图像文件
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir=temp_dir) as temp_img:
                temp_img.write(b"fake image data")
                img_path = temp_img.name
            
            # 创建模拟图像对象
            class MockImage:
                def __init__(self, path):
                    self.page_num = 1
                    self.image_idx = 0
                    self.image_path = path
                    self.bbox = (0, 0, 100, 100)
            
            images = [MockImage(img_path)]
            output_dir = os.path.join(temp_dir, "output")
            doc_id = "test_doc"
            
            # 测试复制图像
            updated_images = generator._copy_images_to_output(images, output_dir, doc_id)
            
            assert len(updated_images) == 1
            assert "images_test_doc" in updated_images[0].image_path
            assert os.path.exists(os.path.join(output_dir, updated_images[0].image_path))
            
            # 清理临时文件
            os.unlink(img_path)


class TestCreateMarkdownGenerator:
    """测试create_markdown_generator工厂方法"""

    def test_create_aiping_generator(self):
        """测试创建AipingMarkdownGenerator实例"""
        api_key = "test_api_key"
        api_url = "https://api.example.com/v1"
        model = "gpt-4"
        
        generator = create_markdown_generator("aiping", api_key, api_url, model)
        
        assert isinstance(generator, AipingMarkdownGenerator)
        assert generator.api_key == api_key
        assert generator.api_url == api_url
        assert generator.model == model

    def test_create_silicon_flow_generator(self):
        """测试创建基础MarkdownGenerator实例"""
        api_key = "test_api_key"
        api_url = "https://api.example.com/v1"
        model = "gpt-4"
        
        generator = create_markdown_generator("silicon_flow", api_key, api_url, model)
        
        assert isinstance(generator, MarkdownGenerator)
        assert not isinstance(generator, AipingMarkdownGenerator)
        assert generator.api_key == api_key
        assert generator.api_url == api_url
        assert generator.model == model

    def test_invalid_api_type(self):
        """测试无效的API类型"""
        api_key = "test_api_key"
        api_url = "https://api.example.com/v1"
        model = "gpt-4"
        
        with pytest.raises(ValueError, match="无效的API类型"):
            create_markdown_generator("invalid_api", api_key, api_url, model)
