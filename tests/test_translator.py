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
            # 模拟流式响应（SiliconFlowTranslator 使用 stream=True）
            mock_stream_chunk = MagicMock()
            mock_stream_chunk.choices = [MagicMock(delta=MagicMock(content='你好'))]
            mock_create.return_value = [mock_stream_chunk]

            # 调用翻译，添加doc_type和glossary参数
            translation_result = translator.translate('Hello', 'en', 'zh', doc_type="AI技术", glossary=None)
            assert translation_result.content == '你好'


class TestFormatBlocks:
    """测试翻译后格式排版优化功能"""

    def test_base_format_returns_original(self):
        """基类 format_blocks（无client）应直接返回原列表"""
        translator = Translator("test_key")

        translated_texts = ["你好世界", "再见"]
        result = translator.format_blocks(translated_texts)
        assert result == ["你好世界", "再见"]

    def test_base_format_empty_input(self):
        """空输入应返回空列表"""
        translator = Translator("test_key")
        result = translator.format_blocks([])
        assert result == []

    _TRANSLATOR_PARAMS = [
        (AipingTranslator, "https://test-api.aiping.com/v1", "Qwen3-32B"),
        (SiliconFlowTranslator, "https://api.siliconflow.cn/v1", "tencent/Hunyuan-MT-7B"),
        (QianfanTranslator, "https://qianfan.baidubce.com/v2", "ernie-4.0"),
    ]

    @pytest.mark.parametrize("translator_cls, api_url, model", _TRANSLATOR_PARAMS)
    def test_formatting(self, translator_cls, api_url, model):
        """format_blocks 应返回格式排版后的结果"""
        translator = translator_cls("test_key", api_url, model)

        with patch.object(translator.client.chat.completions, 'create') as mock_create:
            mock_stream_chunk = MagicMock()
            mock_stream_chunk.choices = [MagicMock(
                delta=MagicMock(content="---块1---\n表示学习与嵌入\n\n---块2---\n")
            )]
            mock_create.return_value = [mock_stream_chunk]

            result = translator.format_blocks(["表示学习与嵌入", "x  |  目录"])
            assert result[0] == "表示学习与嵌入"
            assert result[1] == ""

    @pytest.mark.parametrize("translator_cls, api_url, model", _TRANSLATOR_PARAMS)
    def test_formatting_api_error_fallback(self, translator_cls, api_url, model):
        """API调用失败时异常应向上抛出由调用方处理（Issue 3 行为变更）"""
        translator = translator_cls("test_key", api_url, model)

        with patch.object(translator.client.chat.completions, 'create') as mock_create:
            mock_create.side_effect = Exception("API Error")

            # format_blocks 不再内部吞异常，由调用方 translation_content.py 捕获并 task.add_warning
            with pytest.raises(Exception, match="API Error"):
                translator.format_blocks(["你好"])

    @pytest.mark.parametrize("translator_cls, api_url, model", _TRANSLATOR_PARAMS)
    def test_format_blocks_single_block_empty_llm_response(self, translator_cls, api_url, model):
        """单块+LLM空响应时应回退到原文（防止哨兵字符串写入译文，回归 Issue 1）"""
        translator = translator_cls("test_key", api_url, model)

        with patch.object(translator.client.chat.completions, 'create') as mock_create:
            # 模拟 LLM 返回空内容流（如 finish_reason=length 截断）
            mock_stream_chunk = MagicMock()
            mock_stream_chunk.choices = [MagicMock(delta=MagicMock(content=None))]
            mock_create.return_value = [mock_stream_chunk]

            result = translator.format_blocks(["你好"])
            # 关键：不能返回哨兵字符串，必须回退到原文
            assert result == ["你好"]
            assert "fallback_invalid_format" not in result

    def test_parse_format_result_with_markers(self):
        """_parse_format_result 应正确解析带 ---块N--- 标记的结果"""
        translator = AipingTranslator("test_key", "https://test-api.aiping.com/v1", "Qwen3-32B")

        result_text = "---块1---\n排版后文本1\n\n---块2---\n排版后文本2\n\n---块3---\n"
        parsed = translator._parse_format_result(result_text, 3)
        assert len(parsed) == 3
        assert parsed[0] == "排版后文本1"
        assert parsed[1] == "排版后文本2"
        assert parsed[2] == ""

    def test_parse_format_result_without_markers_line_fallback(self):
        """_parse_format_result 无标记但非空行数足够时应按行回退返回"""
        translator = AipingTranslator("test_key", "https://test-api.aiping.com/v1", "Qwen3-32B")

        result_text = "排版后文本1\n排版后文本2"
        parsed = translator._parse_format_result(result_text, 2)
        assert parsed == ["排版后文本1", "排版后文本2"]

    def test_parse_format_result_without_markers_insufficient_lines(self):
        """_parse_format_result 无标记且回退行数不足时应返回空列表以触发整页回退"""
        translator = AipingTranslator("test_key", "https://test-api.aiping.com/v1", "Qwen3-32B")

        result_text = "只有一行"
        parsed = translator._parse_format_result(result_text, 3)
        assert parsed == []

    def test_format_blocks_input_marker_format(self):
        """format_blocks 构造的输入块标记应为 ---块N--- 格式（无空格）"""
        translator = AipingTranslator("test_key", "https://test-api.aiping.com/v1", "Qwen3-32B")

        with patch.object(translator.client.chat.completions, 'create') as mock_create:
            mock_stream_chunk = MagicMock()
            mock_stream_chunk.choices = [MagicMock(delta=MagicMock(content="---块1---\n文本\n"))]
            mock_create.return_value = [mock_stream_chunk]

            translator.format_blocks(["文本"])

            # 检查传给 create 的 messages 中 user 消息内容
            call_args = mock_create.call_args
            messages = call_args.kwargs["messages"]
            user_content = next(m["content"] for m in messages if m["role"] == "user")

            assert "---块1---" in user_content
            assert "--- 块" not in user_content

    @pytest.mark.parametrize("translator_cls, api_url, model", _TRANSLATOR_PARAMS)
    def test_format_blocks_prompt_includes_target_lang(self, translator_cls, api_url, model):
        """format_blocks user_prompt 应注入目标语言名称以优化排版（Issue 5）"""
        translator = translator_cls("test_key", api_url, model)

        with patch.object(translator.client.chat.completions, 'create') as mock_create:
            mock_stream_chunk = MagicMock()
            mock_stream_chunk.choices = [MagicMock(delta=MagicMock(content="---块1---\n文本\n"))]
            mock_create.return_value = [mock_stream_chunk]

            # 中文目标语言
            translator.format_blocks(["文本"], target_lang="zh")
            call_args = mock_create.call_args
            messages = call_args.kwargs["messages"]
            user_content = next(m["content"] for m in messages if m["role"] == "user")
            assert "目标语言为中文" in user_content

            # 英语目标语言
            translator.format_blocks(["文本"], target_lang="en")
            call_args = mock_create.call_args
            messages = call_args.kwargs["messages"]
            user_content = next(m["content"] for m in messages if m["role"] == "user")
            assert "目标语言为英语" in user_content


# 运行所有测试
if __name__ == "__main__":
    pytest.main([__file__])