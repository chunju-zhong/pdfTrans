import pytest
from unittest.mock import patch, MagicMock
from modules.translator import Translator

from modules.aiping_translator import AipingTranslator
from modules.silicon_flow_translator import SiliconFlowTranslator
from modules.qianfan_translator import QianfanTranslator

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
        assert hasattr(result, 'content')
        assert result.content == 'Hello'
    
    def test_supported_languages_includes_tibetan(self):
        """测试支持的语言包含藏文"""
        translator = Translator(api_key="test_key")
        assert 'bo' in translator.supported_languages
        assert translator.supported_languages['bo'] == '藏文'
    
    def test_validate_language_bo(self):
        """测试藏文语言代码验证"""
        translator = Translator(api_key="test_key")
        assert translator._validate_language('bo') is True
    
    def test_generate_system_prompt_with_lang_codes(self):
        """测试 _generate_system_prompt 含 source_lang_code/target_lang_code 参数"""
        translator = Translator(api_key="test_key")
        
        # 测试带语言代码参数
        prompt = translator._generate_system_prompt(
            doc_type="技术文档",
            source_lang_name="英文",
            target_lang_name="中文",
            glossary="AI: 人工智能",
            source_lang_code="en",
            target_lang_code="zh",
        )
        assert "技术文档" in prompt
        assert "英文" in prompt
        assert "中文" in prompt
        assert "AI:" in prompt
    
    def test_generate_system_prompt_without_lang_codes(self):
        """测试 _generate_system_prompt 不含语言代码参数（向后兼容）"""
        translator = Translator(api_key="test_key")
        
        # 测试不带语言代码参数
        prompt = translator._generate_system_prompt(
            doc_type="AI技术",
            source_lang_name="英文",
            target_lang_name="中文",
            glossary="",
        )
        assert "AI技术" in prompt
        assert "英文" in prompt
        assert "中文" in prompt
    
    def test_batch_translate(self):
        """测试 batch_translate 方法"""
        translator = Translator(api_key="test_key")
        
        # 测试相同语言批量翻译
        texts = ['Hello', 'World']
        results = translator.batch_translate(texts, 'en', 'en')
        assert len(results) == 2
        assert results[0].content == 'Hello'
        assert results[1].content == 'World'
        
        # 测试不同语言批量翻译（应调用translate，会抛出NotImplementedError）
        with pytest.raises(NotImplementedError):
            translator.batch_translate(['Hello'], 'en', 'zh')

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
            translation_result = translator.translate('Hello', 'en', 'zh', doc_type="AI技术", glossary=None)
            assert translation_result.content == '你好'
    
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
            translation_result = translator.translate('Hello', 'en', 'zh', doc_type="AI技术", glossary=None)
            assert translation_result.content == '你好'


class TestCleanupBlocks:
    """测试翻译后清理功能"""

    def test_base_cleanup_returns_original(self):
        """基类 cleanup_blocks 应直接返回原文"""
        translator = Translator("test_key")

        block_pairs = [
            ("Hello World", "你好世界"),
            ("Goodbye", "再见"),
        ]
        result = translator.cleanup_blocks(block_pairs)
        assert result == ["你好世界", "再见"]

    def test_base_cleanup_empty_input(self):
        """空输入应返回空列表"""
        translator = Translator("test_key")
        result = translator.cleanup_blocks([])
        assert result == []

    def test_aiping_cleanup_removes_footer(self):
        """AipingTranslator.cleanup_blocks 应移除页脚残留"""
        translator = AipingTranslator("test_key", "https://test-api.aiping.com/v1", "Qwen3-32B")

        with patch.object(translator.client.chat.completions, 'create') as mock_create:
            mock_response = MagicMock()
            # 模拟LLM返回：块2被清空（页脚），块1保持不变
            mock_response.choices = [MagicMock(
                message=MagicMock(content="---块1---\n表示学习与嵌入\n\n---块2---\n")
            )]
            mock_create.return_value = mock_response

            block_pairs = [
                ("Representation Learning", "表示学习与嵌入"),
                ("x | Table of Contents", "x  |  目录"),
            ]
            result = translator.cleanup_blocks(block_pairs)
            assert result[0] == "表示学习与嵌入"
            assert result[1] == ""

    def test_aiping_cleanup_on_api_error(self):
        """API调用失败时应返回原文"""
        translator = AipingTranslator("test_key", "https://test-api.aiping.com/v1", "Qwen3-32B")

        with patch.object(translator.client.chat.completions, 'create') as mock_create:
            mock_create.side_effect = Exception("API Error")

            block_pairs = [
                ("Hello", "你好"),
            ]
            result = translator.cleanup_blocks(block_pairs)
            assert result == ["你好"]

    def test_parse_cleanup_result_with_markers(self):
        """_parse_cleanup_result 应正确解析带标记的结果"""
        translator = AipingTranslator("test_key", "https://test-api.aiping.com/v1", "Qwen3-32B")

        result_text = "---块1---\n清理后文本1\n\n---块2---\n清理后文本2\n\n---块3---\n"
        parsed = translator._parse_cleanup_result(result_text, 3)
        assert len(parsed) == 3
        assert parsed[0] == "清理后文本1"
        assert parsed[1] == "清理后文本2"
        assert parsed[2] == ""

    def test_parse_cleanup_result_without_markers(self):
        """_parse_cleanup_result 对无标记的结果应尽量按行解析"""
        translator = AipingTranslator("test_key", "https://test-api.aiping.com/v1", "Qwen3-32B")

        result_text = "清理后文本1\n清理后文本2"
        parsed = translator._parse_cleanup_result(result_text, 2)
        assert len(parsed) == 2
        assert parsed[0] == "清理后文本1"
        assert parsed[1] == "清理后文本2"

    def test_silicon_flow_cleanup_removes_footer(self):
        """SiliconFlowTranslator.cleanup_blocks 应移除页脚残留"""
        translator = SiliconFlowTranslator("test_key", "https://api.siliconflow.cn/v1", "tencent/Hunyuan-MT-7B")

        with patch.object(translator.client.chat.completions, 'create') as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(
                message=MagicMock(content="---块1---\n表示学习与嵌入\n\n---块2---\n")
            )]
            mock_create.return_value = mock_response

            block_pairs = [
                ("Representation Learning", "表示学习与嵌入"),
                ("x | Table of Contents", "x  |  目录"),
            ]
            result = translator.cleanup_blocks(block_pairs)
            assert result[0] == "表示学习与嵌入"
            assert result[1] == ""

    def test_silicon_flow_cleanup_on_api_error(self):
        """SiliconFlowTranslator API调用失败时应返回原文"""
        translator = SiliconFlowTranslator("test_key", "https://api.siliconflow.cn/v1", "tencent/Hunyuan-MT-7B")

        with patch.object(translator.client.chat.completions, 'create') as mock_create:
            mock_create.side_effect = Exception("API Error")

            block_pairs = [
                ("Hello", "你好"),
            ]
            result = translator.cleanup_blocks(block_pairs)
            assert result == ["你好"]

    def test_qianfan_cleanup_removes_footer(self):
        """QianfanTranslator.cleanup_blocks 应移除页脚残留"""
        translator = QianfanTranslator("test_key", "https://qianfan.baidubce.com/v2", "ernie-4.0")

        with patch.object(translator.client.chat.completions, 'create') as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(
                message=MagicMock(content="---块1---\n表示学习与嵌入\n\n---块2---\n")
            )]
            mock_create.return_value = mock_response

            block_pairs = [
                ("Representation Learning", "表示学习与嵌入"),
                ("x | Table of Contents", "x  |  目录"),
            ]
            result = translator.cleanup_blocks(block_pairs)
            assert result[0] == "表示学习与嵌入"
            assert result[1] == ""

    def test_qianfan_cleanup_on_api_error(self):
        """QianfanTranslator API调用失败时应返回原文"""
        translator = QianfanTranslator("test_key", "https://qianfan.baidubce.com/v2", "ernie-4.0")

        with patch.object(translator.client.chat.completions, 'create') as mock_create:
            mock_create.side_effect = Exception("API Error")

            block_pairs = [
                ("Hello", "你好"),
            ]
            result = translator.cleanup_blocks(block_pairs)
            assert result == ["你好"]


# 运行所有测试
if __name__ == "__main__":
    pytest.main([__file__])