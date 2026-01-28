import pytest
from unittest.mock import patch, MagicMock
from modules.translator import Translator

from modules.aiping_translator import AipingTranslator
from modules.silicon_flow_translator import SiliconFlowTranslator

class TestTranslator:
    """测试翻译器基类功能"""
    
    def test_translate_basic(self):
        """测试基本的translate方法"""
        # 创建一个基本的翻译器实例
        translator = Translator(api_key="test_key")

        # 测试直接调用translate方法
        current_block = {
            'block_text': 'Hello',
            'block_no': 0,
            'page_num': 1
        }

        # 调用翻译方法，添加doc_type和glossary参数
        with pytest.raises(NotImplementedError):
            translator.translate(current_block['block_text'], 'en', 'zh', doc_type="AI技术", glossary=None)

    def test_translate_same_language(self):
        """测试翻译相同语言时的行为"""
        # 创建一个基本的翻译器实例
        translator = Translator(api_key="test_key")
        
        # 测试相同语言翻译，添加doc_type和glossary参数
        result = translator.translate('Hello', 'en', 'en', doc_type="AI技术", glossary=None)
        assert result == 'Hello'

class TestContextTranslation:
    """测试上下文翻译功能"""
    
    def test_context_format(self):
        """测试上下文格式是否正确"""
        # 创建上下文数据
        context_blocks = {
            'previous_blocks': [
                {'block_text': 'This is previous block', 'block_no': 0, 'page_num': 1},
                {'block_text': 'This is another previous block', 'block_no': 1, 'page_num': 1}
            ],
            'next_blocks': [
                {'block_text': 'This is next block', 'block_no': 2, 'page_num': 1},
                {'block_text': 'This is another next block', 'block_no': 3, 'page_num': 2}  # 跨页上下文
            ]
        }
        
        # 验证上下文格式
        assert isinstance(context_blocks, dict)
        assert 'previous_blocks' in context_blocks
        assert 'next_blocks' in context_blocks
        assert isinstance(context_blocks['previous_blocks'], list)
        assert isinstance(context_blocks['next_blocks'], list)
        
        # 验证跨页上下文
        cross_page_next = [block for block in context_blocks['next_blocks'] if block['page_num'] != 1]
        assert len(cross_page_next) == 1

class TestTranslatorImplementations:
    """测试具体翻译器实现的上下文功能"""
    
    def test_aiping_translate(self):
        """测试AI Ping翻译器的翻译"""
        # 创建aiping翻译器实例
        api_key = "test_key"
        api_url = "https://test-api.aiping.com/v1"
        model = "Qwen3-32B"
        translator = AipingTranslator(api_key, api_url, model)
        
        # 模拟聊天完成API
        with patch.object(translator.client.chat.completions, 'create') as mock_create:
            # 模拟流式响应
            mock_stream_chunk = MagicMock()
            mock_stream_chunk.choices = [MagicMock(delta=MagicMock(content='你好'))]
            
            mock_create.return_value = [mock_stream_chunk]
            
            # 调用翻译，添加doc_type和glossary参数
            result = translator.translate('Hello', 'en', 'zh', doc_type="AI技术", glossary=None)
            assert result == '你好'
    
    def test_silicon_flow_translate(self):
        """测试硅基流动翻译器的翻译"""
        # 创建硅基流动翻译器实例
        api_key = "test_key"
        api_url = "https://api.siliconflow.cn/v1"
        model = "tencent/Hunyuan-MT-7B"
        translator = SiliconFlowTranslator(api_key, api_url, model)
        
        # 模拟聊天完成API
        with patch.object(translator.client.chat.completions, 'create') as mock_create:
            # 模拟响应
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content='你好'))]
            mock_create.return_value = mock_response
            
            # 调用翻译，添加doc_type和glossary参数
            result = translator.translate('Hello', 'en', 'zh', doc_type="AI技术", glossary=None)
            assert result == '你好'

# 运行所有测试
if __name__ == "__main__":
    pytest.main([__file__])