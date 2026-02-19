import pytest
from unittest.mock import patch, MagicMock
from modules.translator import Translator
from modules.aiping_translator import AipingTranslator
from modules.silicon_flow_translator import SiliconFlowTranslator

class TestBatchSemanticAnalysis:
    """测试批量语义分析功能"""

    def test_batch_analyze_semantic_relationship_base(self):
        """测试基类批量语义分析方法"""
        # 创建一个基本的翻译器实例
        translator = Translator(api_key="test_key")

        # 测试直接调用批量语义分析方法
        text_pairs = [
            ("Hello", "world"),
            ("How are", "you")
        ]

        # 调用批量语义分析方法，应该抛出 NotImplementedError
        with pytest.raises(NotImplementedError):
            translator.batch_analyze_semantic_relationship(text_pairs, 'en')

    def test_generate_batch_semantic_analysis_prompt(self):
        """测试批量语义分析提示词生成"""
        # 创建一个基本的翻译器实例
        translator = Translator(api_key="test_key")

        # 测试提示词生成
        text_pairs = [
            ("Hello", "world"),
            ("How are", "you")
        ]

        prompt = translator._generate_batch_semantic_analysis_prompt(text_pairs, 'en')
        
        # 验证提示词包含必要的内容
        assert "你是专业的文本语义分析专家" in prompt
        assert "对1:" in prompt
        assert "块1: \"Hello\"" in prompt
        assert "块2: \"world\"" in prompt
        assert "对2:" in prompt
        assert "块1: \"How are\"" in prompt
        assert "块2: \"you\"" in prompt
        assert "分析标准" in prompt
        assert "重要输出要求" in prompt

class TestAipingBatchSemanticAnalysis:
    """测试 Aiping 翻译器批量语义分析功能"""

    def test_aiping_batch_analyze_semantic_relationship(self):
        """测试 Aiping 批量语义分析基本功能"""
        # 创建 aiping 翻译器实例
        api_key = "test_key"
        api_url = "https://test-api.aiping.com/v1"
        model = "Qwen3-32B"
        translator = AipingTranslator(api_key, api_url, model)

        # 测试数据
        text_pairs = [
            ("Hello", "world"),
            ("How are", "you")
        ]

        # 模拟聊天完成API
        with patch.object(translator.client.chat.completions, 'create') as mock_create:
            # 模拟流式响应
            mock_stream_chunk1 = MagicMock()
            mock_stream_chunk1.choices = [MagicMock(delta=MagicMock(content='{"merge": [true, false]}'))]

            mock_create.return_value = [mock_stream_chunk1]

            # 调用批量语义分析
            result = translator.batch_analyze_semantic_relationship(text_pairs, 'en')
            
            # 验证结果
            assert isinstance(result, list)
            assert len(result) == 2
            assert result == [True, False]

    def test_aiping_batch_analyze_semantic_relationship_error_handling(self):
        """测试 Aiping 批量语义分析错误处理"""
        # 创建 aiping 翻译器实例
        api_key = "test_key"
        api_url = "https://test-api.aiping.com/v1"
        model = "Qwen3-32B"
        translator = AipingTranslator(api_key, api_url, model)

        # 测试数据
        text_pairs = [
            ("Hello", "world"),
            ("How are", "you")
        ]

        # 模拟聊天完成API - JSON解析错误
        with patch.object(translator.client.chat.completions, 'create') as mock_create:
            # 模拟流式响应
            mock_stream_chunk1 = MagicMock()
            mock_stream_chunk1.choices = [MagicMock(delta=MagicMock(content='invalid json'))]

            mock_create.return_value = [mock_stream_chunk1]

            # 调用批量语义分析，应该返回默认值
            result = translator.batch_analyze_semantic_relationship(text_pairs, 'en')
            
            # 验证结果
            assert isinstance(result, list)
            assert len(result) == 2
            assert result == [False, False]

    def test_aiping_batch_analyze_semantic_relationship_retry(self):
        """测试 Aiping 批量语义分析重试机制"""
        # 创建 aiping 翻译器实例
        api_key = "test_key"
        api_url = "https://test-api.aiping.com/v1"
        model = "Qwen3-32B"
        translator = AipingTranslator(api_key, api_url, model)

        # 测试数据
        text_pairs = [
            ("Hello", "world")
        ]

        # 模拟聊天完成API - 第一次失败，第二次成功
        with patch.object(translator.client.chat.completions, 'create') as mock_create:
            # 第一次调用抛出异常
            # 第二次调用返回正确响应
            mock_stream_chunk1 = MagicMock()
            mock_stream_chunk1.choices = [MagicMock(delta=MagicMock(content='{"merge": [true]}'))]

            # 第一次调用抛出异常，第二次调用返回正确响应
            def side_effect(*args, **kwargs):
                if side_effect.called:
                    return [mock_stream_chunk1]
                side_effect.called = True
                raise Exception("API Error")
            
            side_effect.called = False
            mock_create.side_effect = side_effect

            # 调用批量语义分析
            result = translator.batch_analyze_semantic_relationship(text_pairs, 'en')
            
            # 验证结果
            assert isinstance(result, list)
            assert len(result) == 1
            assert result == [True]

class TestSiliconFlowBatchSemanticAnalysis:
    """测试 Silicon Flow 翻译器批量语义分析功能"""

    def test_silicon_flow_batch_analyze_semantic_relationship(self):
        """测试 Silicon Flow 批量语义分析基本功能"""
        # 创建硅基流动翻译器实例
        api_key = "test_key"
        api_url = "https://api.siliconflow.cn/v1"
        model = "tencent/Hunyuan-MT-7B"
        translator = SiliconFlowTranslator(api_key, api_url, model)

        # 测试数据
        text_pairs = [
            ("Hello", "world"),
            ("How are", "you")
        ]

        # 模拟聊天完成API
        with patch.object(translator.client.chat.completions, 'create') as mock_create:
            # 模拟响应
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content='{"merge": [true, false]}'))]
            mock_create.return_value = mock_response

            # 调用批量语义分析
            result = translator.batch_analyze_semantic_relationship(text_pairs, 'en')
            
            # 验证结果
            assert isinstance(result, list)
            assert len(result) == 2
            assert result == [True, False]

    def test_silicon_flow_batch_analyze_semantic_relationship_error_handling(self):
        """测试 Silicon Flow 批量语义分析错误处理"""
        # 创建硅基流动翻译器实例
        api_key = "test_key"
        api_url = "https://api.siliconflow.cn/v1"
        model = "tencent/Hunyuan-MT-7B"
        translator = SiliconFlowTranslator(api_key, api_url, model)

        # 测试数据
        text_pairs = [
            ("Hello", "world"),
            ("How are", "you")
        ]

        # 模拟聊天完成API - JSON解析错误
        with patch.object(translator.client.chat.completions, 'create') as mock_create:
            # 模拟响应
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content='invalid json'))]
            mock_create.return_value = mock_response

            # 调用批量语义分析，应该返回默认值
            result = translator.batch_analyze_semantic_relationship(text_pairs, 'en')
            
            # 验证结果
            assert isinstance(result, list)
            assert len(result) == 2
            assert result == [False, False]

class TestBatchSemanticAnalysisEdgeCases:
    """测试批量语义分析边界情况"""

    def test_batch_analyze_semantic_relationship_empty_input(self):
        """测试空输入"""
        # 创建 aiping 翻译器实例
        api_key = "test_key"
        api_url = "https://test-api.aiping.com/v1"
        model = "Qwen3-32B"
        translator = AipingTranslator(api_key, api_url, model)

        # 测试空输入
        text_pairs = []

        # 模拟聊天完成API
        with patch.object(translator.client.chat.completions, 'create') as mock_create:
            # 模拟响应
            mock_stream_chunk1 = MagicMock()
            mock_stream_chunk1.choices = [MagicMock(delta=MagicMock(content='{"merge": []}'))]

            mock_create.return_value = [mock_stream_chunk1]

            # 调用批量语义分析
            result = translator.batch_analyze_semantic_relationship(text_pairs, 'en')
            
            # 验证结果
            assert isinstance(result, list)
            assert len(result) == 0

    def test_batch_analyze_semantic_relationship_result_count_mismatch(self):
        """测试结果数量不匹配情况"""
        # 创建 aiping 翻译器实例
        api_key = "test_key"
        api_url = "https://test-api.aiping.com/v1"
        model = "Qwen3-32B"
        translator = AipingTranslator(api_key, api_url, model)

        # 测试数据
        text_pairs = [
            ("Hello", "world"),
            ("How are", "you")
        ]

        # 模拟聊天完成API - 返回结果数量不匹配
        with patch.object(translator.client.chat.completions, 'create') as mock_create:
            # 模拟响应
            mock_stream_chunk1 = MagicMock()
            mock_stream_chunk1.choices = [MagicMock(delta=MagicMock(content='{"merge": [true]}'))]

            mock_create.return_value = [mock_stream_chunk1]

            # 调用批量语义分析，应该返回默认值
            result = translator.batch_analyze_semantic_relationship(text_pairs, 'en')
            
            # 验证结果
            assert isinstance(result, list)
            assert len(result) == 2
            assert result == [False, False]

    def test_batch_analyze_semantic_relationship_large_input(self):
        """测试大量文本对输入"""
        # 创建 aiping 翻译器实例
        api_key = "test_key"
        api_url = "https://test-api.aiping.com/v1"
        model = "Qwen3-32B"
        translator = AipingTranslator(api_key, api_url, model)

        # 测试数据 - 5个文本对
        text_pairs = [
            ("Hello", "world"),
            ("How are", "you"),
            ("I am", "fine"),
            ("Thank", "you"),
            ("Good", "bye")
        ]

        # 模拟聊天完成API
        with patch.object(translator.client.chat.completions, 'create') as mock_create:
            # 模拟响应
            mock_stream_chunk1 = MagicMock()
            mock_stream_chunk1.choices = [MagicMock(delta=MagicMock(content='{"merge": [true, true, false, true, false]}'))]

            mock_create.return_value = [mock_stream_chunk1]

            # 调用批量语义分析
            result = translator.batch_analyze_semantic_relationship(text_pairs, 'en')
            
            # 验证结果
            assert isinstance(result, list)
            assert len(result) == 5
            assert result == [True, True, False, True, False]

if __name__ == "__main__":
    pytest.main([__file__])
