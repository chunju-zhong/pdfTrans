import pytest
from unittest.mock import patch, MagicMock
from modules.semantic_analyzer import SemanticAnalyzer
from modules.aiping_semantic_analyzer import AipingSemanticAnalyzer
from modules.semantic_analyzer_factory import SemanticAnalyzerFactory

class TestSemanticAnalyzer:
    """测试语义分析器基类"""

    def test_analyze_semantic_relationship(self):
        """测试语义分析方法"""
        # 创建语义分析器实例
        analyzer = SemanticAnalyzer(
            api_key="test_key",
            api_url="https://test-api.example.com/v1",
            model="test-model"
        )

        # 测试数据
        text1 = "Hello"
        text2 = "world"

        # 模拟聊天完成API
        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
            # 模拟响应
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content='{"merge": true}'))]
            mock_create.return_value = mock_response

            # 调用语义分析方法
            result = analyzer.analyze_semantic_relationship(text1, text2, 'en')
            
            # 验证结果
            assert isinstance(result, bool)
            assert result == True

    def test_batch_analyze_semantic_relationship(self):
        """测试批量语义分析方法"""
        # 创建语义分析器实例
        analyzer = SemanticAnalyzer(
            api_key="test_key",
            api_url="https://test-api.example.com/v1",
            model="test-model"
        )

        # 测试数据
        text_pairs = [
            ("Hello", "world"),
            ("How are", "you")
        ]

        # 模拟聊天完成API
        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
            # 模拟响应
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content='{"merge": [true, false]}'))]
            mock_create.return_value = mock_response

            # 调用批量语义分析方法
            result = analyzer.batch_analyze_semantic_relationship(text_pairs, 'en')
            
            # 验证结果
            assert isinstance(result, list)
            assert len(result) == 2
            assert result == [True, False]

    def test_batch_analyze_with_retry(self):
        """测试批量语义分析方法的重试机制"""
        # 创建语义分析器实例
        analyzer = SemanticAnalyzer(
            api_key="test_key",
            api_url="https://test-api.example.com/v1",
            model="test-model"
        )

        # 测试数据
        text_pairs = [
            ("Hello", "world"),
            ("How are", "you"),
            ("I am", "fine")
        ]

        # 模拟聊天完成API - 前两次返回错误数量的结果，第三次返回正确结果
        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
            # 第一次响应 - 缺少一个结果
            mock_response1 = MagicMock()
            mock_response1.choices = [MagicMock(message=MagicMock(content='{"merge": [true, false]}'))]
            # 第二次响应 - 缺少一个结果
            mock_response2 = MagicMock()
            mock_response2.choices = [MagicMock(message=MagicMock(content='{"merge": [true, false]}'))]
            # 第三次响应 - 正确结果
            mock_response3 = MagicMock()
            mock_response3.choices = [MagicMock(message=MagicMock(content='{"merge": [true, false, true]}'))]
            
            # 设置mock的返回值序列
            mock_create.side_effect = [mock_response1, mock_response2, mock_response3]

            # 调用批量语义分析方法
            result = analyzer.batch_analyze_semantic_relationship(text_pairs, 'en')
            
            # 验证结果
            assert isinstance(result, list)
            assert len(result) == 3
            assert result == [True, False, True]
            # 验证mock被调用了3次
            assert mock_create.call_count == 3

    def test_batch_analyze_with_final_failure(self):
        """测试批量语义分析方法在最终失败时的处理"""
        # 创建语义分析器实例
        analyzer = SemanticAnalyzer(
            api_key="test_key",
            api_url="https://test-api.example.com/v1",
            model="test-model"
        )

        # 测试数据
        text_pairs = [
            ("Hello", "world"),
            ("How are", "you"),
            ("I am", "fine")
        ]

        # 模拟聊天完成API - 始终返回错误数量的结果
        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
            # 响应 - 缺少一个结果
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content='{"merge": [true, false]}'))]
            mock_create.return_value = mock_response

            # 调用批量语义分析方法
            result = analyzer.batch_analyze_semantic_relationship(text_pairs, 'en')
            
            # 验证结果 - 应该补足缺失的项为false
            assert isinstance(result, list)
            assert len(result) == 3
            assert result == [True, False, False]
            # 验证mock被调用了3次
            assert mock_create.call_count == 3

    def test_generate_semantic_analysis_prompt(self):
        """测试语义分析提示词生成"""
        # 创建语义分析器实例
        analyzer = SemanticAnalyzer(
            api_key="test_key",
            api_url="https://test-api.example.com/v1",
            model="test-model"
        )

        # 测试提示词生成
        text1 = "Hello"
        text2 = "world"

        prompt = analyzer._generate_semantic_analysis_prompt(text1, text2, 'en')
        
        # 验证提示词包含必要的内容
        assert "你是专业的文本语义分析专家" in prompt
        assert "块1: \"Hello\"" in prompt
        assert "块2: \"world\"" in prompt
        assert "分析标准" in prompt
        assert "重要输出要求" in prompt

    def test_generate_batch_semantic_analysis_prompt(self):
        """测试批量语义分析提示词生成"""
        # 创建语义分析器实例
        analyzer = SemanticAnalyzer(
            api_key="test_key",
            api_url="https://test-api.example.com/v1",
            model="test-model"
        )

        # 测试提示词生成
        text_pairs = [
            ("Hello", "world"),
            ("How are", "you")
        ]

        prompt = analyzer._generate_batch_semantic_analysis_prompt(text_pairs, 'en')
        
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

class TestAipingSemanticAnalyzer:
    """测试 Aiping 语义分析器"""

    def test_analyze_semantic_relationship(self):
        """测试 Aiping 语义分析方法"""
        # 创建 Aiping 语义分析器实例
        analyzer = AipingSemanticAnalyzer(
            api_key="test_key",
            api_url="https://test-api.aiping.com/v1",
            model="Qwen3-32B"
        )

        # 测试数据
        text1 = "Hello"
        text2 = "world"

        # 模拟聊天完成API
        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
            # 模拟流式响应
            mock_stream_chunk1 = MagicMock()
            mock_stream_chunk1.choices = [MagicMock(delta=MagicMock(content='{"merge": true}'))]

            mock_create.return_value = [mock_stream_chunk1]

            # 调用语义分析方法
            result = analyzer.analyze_semantic_relationship(text1, text2, 'en')
            
            # 验证结果
            assert isinstance(result, bool)
            assert result == True

    def test_batch_analyze_semantic_relationship(self):
        """测试 Aiping 批量语义分析方法"""
        # 创建 Aiping 语义分析器实例
        analyzer = AipingSemanticAnalyzer(
            api_key="test_key",
            api_url="https://test-api.aiping.com/v1",
            model="Qwen3-32B"
        )

        # 测试数据
        text_pairs = [
            ("Hello", "world"),
            ("How are", "you")
        ]

        # 模拟聊天完成API
        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
            # 模拟流式响应
            mock_stream_chunk1 = MagicMock()
            mock_stream_chunk1.choices = [MagicMock(delta=MagicMock(content='{"merge": [true, false]}'))]

            mock_create.return_value = [mock_stream_chunk1]

            # 调用批量语义分析方法
            result = analyzer.batch_analyze_semantic_relationship(text_pairs, 'en')
            
            # 验证结果
            assert isinstance(result, list)
            assert len(result) == 2
            assert result == [True, False]

    def test_batch_analyze_with_retry(self):
        """测试 Aiping 批量语义分析方法的重试机制"""
        # 创建 Aiping 语义分析器实例
        analyzer = AipingSemanticAnalyzer(
            api_key="test_key",
            api_url="https://test-api.aiping.com/v1",
            model="Qwen3-32B"
        )

        # 测试数据
        text_pairs = [
            ("Hello", "world"),
            ("How are", "you"),
            ("I am", "fine")
        ]

        # 模拟聊天完成API - 前两次返回错误数量的结果，第三次返回正确结果
        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
            # 第一次响应 - 缺少一个结果
            mock_stream_chunk1 = MagicMock()
            mock_stream_chunk1.choices = [MagicMock(delta=MagicMock(content='{"merge": [true, false]}'))]
            # 第二次响应 - 缺少一个结果
            mock_stream_chunk2 = MagicMock()
            mock_stream_chunk2.choices = [MagicMock(delta=MagicMock(content='{"merge": [true, false]}'))]
            # 第三次响应 - 正确结果
            mock_stream_chunk3 = MagicMock()
            mock_stream_chunk3.choices = [MagicMock(delta=MagicMock(content='{"merge": [true, false, true]}'))]
            
            # 设置mock的返回值序列
            mock_create.side_effect = [[mock_stream_chunk1], [mock_stream_chunk2], [mock_stream_chunk3]]

            # 调用批量语义分析方法
            result = analyzer.batch_analyze_semantic_relationship(text_pairs, 'en')
            
            # 验证结果
            assert isinstance(result, list)
            assert len(result) == 3
            assert result == [True, False, True]
            # 验证mock被调用了3次
            assert mock_create.call_count == 3

    def test_batch_analyze_with_final_failure(self):
        """测试 Aiping 批量语义分析方法在最终失败时的处理"""
        # 创建 Aiping 语义分析器实例
        analyzer = AipingSemanticAnalyzer(
            api_key="test_key",
            api_url="https://test-api.aiping.com/v1",
            model="Qwen3-32B"
        )

        # 测试数据
        text_pairs = [
            ("Hello", "world"),
            ("How are", "you"),
            ("I am", "fine")
        ]

        # 模拟聊天完成API - 始终返回错误数量的结果
        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
            # 响应 - 缺少一个结果
            mock_stream_chunk = MagicMock()
            mock_stream_chunk.choices = [MagicMock(delta=MagicMock(content='{"merge": [true, false]}'))]
            mock_create.return_value = [mock_stream_chunk]

            # 调用批量语义分析方法
            result = analyzer.batch_analyze_semantic_relationship(text_pairs, 'en')
            
            # 验证结果 - 应该补足缺失的项为false
            assert isinstance(result, list)
            assert len(result) == 3
            assert result == [True, False, False]
            # 验证mock被调用了3次
            assert mock_create.call_count == 3

class TestSemanticAnalyzerFactory:
    """测试语义分析器工厂"""

    def test_create_analyzer_default(self):
        """测试创建默认语义分析器"""
        # 创建默认语义分析器
        analyzer = SemanticAnalyzerFactory.create_analyzer(
            "default",
            "test_key",
            "https://test-api.example.com/v1",
            "test-model"
        )

        # 验证类型
        assert isinstance(analyzer, SemanticAnalyzer)

    def test_create_analyzer_aiping(self):
        """测试创建 Aiping 语义分析器"""
        # 创建 Aiping 语义分析器
        analyzer = SemanticAnalyzerFactory.create_analyzer(
            "aiping",
            "test_key",
            "https://test-api.aiping.com/v1",
            "Qwen3-32B"
        )

        # 验证类型
        assert isinstance(analyzer, AipingSemanticAnalyzer)

    def test_get_available_analyzers(self):
        """测试获取可用的语义分析器类型"""
        analyzers = SemanticAnalyzerFactory.get_available_analyzers()
        
        # 验证结果
        assert isinstance(analyzers, list)
        assert "aiping" in analyzers
        assert "silicon_flow" in analyzers

if __name__ == "__main__":
    pytest.main([__file__])
