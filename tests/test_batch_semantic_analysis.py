import pytest
from unittest.mock import patch, MagicMock
from modules.semantic_analyzer import SemanticAnalyzer
from modules.aiping_semantic_analyzer import AipingSemanticAnalyzer

class TestBatchSemanticAnalysis:
    """测试批量语义分析功能"""

    def test_batch_analyze_semantic_relationship_base(self):
        """测试基类批量语义分析方法"""
        # 创建一个基本的语义分析器实例
        analyzer = SemanticAnalyzer(
            api_key="test_key",
            api_url="https://test-api.example.com/v1",
            model="test-model"
        )

        # 测试数据
        blocks = ["Hello", "world", "How are", "you"]

        # 模拟聊天完成API
        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
            # 模拟响应 - 4个块产生3个合并决策
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content='{"merge": [true, false, true]}'))]
            mock_create.return_value = mock_response

            # 调用批量语义分析
            result = analyzer.batch_analyze_semantic_relationship(blocks, 'en')

            # 验证结果
            assert isinstance(result, list)
            assert len(result) == 3
            assert result == [True, False, True]

    def test_generate_batch_semantic_analysis_prompt(self):
        """测试批量语义分析提示词生成"""
        # 创建一个基本的语义分析器实例
        analyzer = SemanticAnalyzer(
            api_key="test_key",
            api_url="https://test-api.example.com/v1",
            model="test-model"
        )

        # 测试提示词生成
        blocks = ["Hello", "world", "How are", "you"]

        prompt = analyzer._generate_batch_semantic_analysis_prompt(blocks, 'en')

        # 验证提示词包含必要的内容 - 新格式使用顺序块编号
        assert "你是专业的文本语义分析专家" in prompt
        assert "块1:" in prompt
        assert "块2:" in prompt
        assert "块3:" in prompt
        assert "块4:" in prompt
        assert "Hello" in prompt
        assert "world" in prompt
        assert "How are" in prompt
        assert "you" in prompt
        assert "语义角色" in prompt
        assert "输出要求" in prompt
        assert "上下文感知" in prompt

class TestAipingBatchSemanticAnalysis:
    """测试 Aiping 语义分析器批量语义分析功能"""

    def test_aiping_batch_analyze_semantic_relationship(self):
        """测试 Aiping 批量语义分析基本功能"""
        # 创建 aiping 语义分析器实例
        api_key = "test_key"
        api_url = "https://test-api.aiping.com/v1"
        model = "Qwen3-32B"
        analyzer = AipingSemanticAnalyzer(api_key, api_url, model)

        # 测试数据
        blocks = ["Hello", "world", "How are", "you"]

        # 模拟聊天完成API
        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
            # 模拟流式响应 - 4个块产生3个合并决策
            mock_stream_chunk1 = MagicMock()
            mock_stream_chunk1.choices = [MagicMock(delta=MagicMock(content='{"merge": [true, false, true]}'))]

            mock_create.return_value = [mock_stream_chunk1]

            # 调用批量语义分析
            result = analyzer.batch_analyze_semantic_relationship(blocks, 'en')

            # 验证结果
            assert isinstance(result, list)
            assert len(result) == 3
            assert result == [True, False, True]

    def test_aiping_batch_analyze_semantic_relationship_error_handling(self):
        """测试 Aiping 批量语义分析错误处理"""
        # 创建 aiping 语义分析器实例
        api_key = "test_key"
        api_url = "https://test-api.aiping.com/v1"
        model = "Qwen3-32B"
        analyzer = AipingSemanticAnalyzer(api_key, api_url, model)

        # 测试数据
        blocks = ["Hello", "world", "How are", "you"]

        # 模拟聊天完成API - JSON解析错误
        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
            # 模拟流式响应
            mock_stream_chunk1 = MagicMock()
            mock_stream_chunk1.choices = [MagicMock(delta=MagicMock(content='invalid json'))]

            mock_create.return_value = [mock_stream_chunk1]

            # 调用批量语义分析，应该返回默认值
            result = analyzer.batch_analyze_semantic_relationship(blocks, 'en')

            # 验证结果 - 4个块产生3个默认False
            assert isinstance(result, list)
            assert len(result) == 3
            assert result == [False, False, False]

    def test_aiping_batch_analyze_semantic_relationship_retry(self):
        """测试 Aiping 批量语义分析重试机制"""
        # 创建 aiping 语义分析器实例
        api_key = "test_key"
        api_url = "https://test-api.aiping.com/v1"
        model = "Qwen3-32B"
        analyzer = AipingSemanticAnalyzer(api_key, api_url, model)

        # 测试数据 - 2个块产生1个合并决策
        blocks = ["Hello", "world"]

        # 模拟聊天完成API - 第一次失败，第二次成功
        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
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
            result = analyzer.batch_analyze_semantic_relationship(blocks, 'en')

            # 验证结果
            assert isinstance(result, list)
            assert len(result) == 1
            assert result == [True]

class TestBatchSemanticAnalysisEdgeCases:
    """测试批量语义分析边界情况"""

    def test_batch_analyze_semantic_relationship_empty_input(self):
        """测试空输入"""
        # 创建 aiping 语义分析器实例
        api_key = "test_key"
        api_url = "https://test-api.aiping.com/v1"
        model = "Qwen3-32B"
        analyzer = AipingSemanticAnalyzer(api_key, api_url, model)

        # 测试空输入
        blocks = []

        # 调用批量语义分析 - 空列表直接返回空结果，无需mock
        result = analyzer.batch_analyze_semantic_relationship(blocks, 'en')

        # 验证结果
        assert isinstance(result, list)
        assert len(result) == 0

    def test_batch_analyze_semantic_relationship_result_count_mismatch(self):
        """测试结果数量不匹配情况"""
        # 创建 aiping 语义分析器实例
        api_key = "test_key"
        api_url = "https://test-api.aiping.com/v1"
        model = "Qwen3-32B"
        analyzer = AipingSemanticAnalyzer(api_key, api_url, model)

        # 测试数据 - 4个块期望3个合并决策
        blocks = ["Hello", "world", "How are", "you"]

        # 模拟聊天完成API - 返回结果数量不匹配
        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
            # 模拟响应 - 只返回1个决策，但期望3个
            mock_stream_chunk1 = MagicMock()
            mock_stream_chunk1.choices = [MagicMock(delta=MagicMock(content='{"merge": [true]}'))]

            mock_create.return_value = [mock_stream_chunk1]

            # 调用批量语义分析，应该返回补足后的结果
            result = analyzer.batch_analyze_semantic_relationship(blocks, 'en')

            # 验证结果 - 补足缺失项为False
            assert isinstance(result, list)
            assert len(result) == 3
            assert result == [True, False, False]

    def test_batch_analyze_semantic_relationship_large_input(self):
        """测试大量文本对输入"""
        # 创建 aiping 语义分析器实例
        api_key = "test_key"
        api_url = "https://test-api.aiping.com/v1"
        model = "Qwen3-32B"
        analyzer = AipingSemanticAnalyzer(api_key, api_url, model)

        # 测试数据 - 6个块产生5个合并决策
        blocks = ["Hello", "world", "How are", "you", "I am", "fine"]

        # 模拟聊天完成API
        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
            # 模拟响应
            mock_stream_chunk1 = MagicMock()
            mock_stream_chunk1.choices = [MagicMock(delta=MagicMock(content='{"merge": [true, true, false, true, false]}'))]

            mock_create.return_value = [mock_stream_chunk1]

            # 调用批量语义分析
            result = analyzer.batch_analyze_semantic_relationship(blocks, 'en')

            # 验证结果
            assert isinstance(result, list)
            assert len(result) == 5
            assert result == [True, True, False, True, False]

if __name__ == "__main__":
    pytest.main([__file__])
