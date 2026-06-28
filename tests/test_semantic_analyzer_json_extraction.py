import pytest
from unittest.mock import patch, MagicMock
from modules.semantic_analyzer import SemanticAnalyzer
from modules.aiping_semantic_analyzer import AipingSemanticAnalyzer


class TestSemanticAnalyzerJsonExtraction:
    """测试语义分析器JSON容错提取（修复 ```json 代码栅栏解析失败）"""

    def setup_method(self):
        self.analyzer = SemanticAnalyzer(
            api_key="test_key",
            api_url="https://test-api.example.com/v1",
            model="test-model"
        )

    def test_extract_pure_json(self):
        """场景1：LLM返回纯JSON（无栅栏）- 应直接解析"""
        text = '{"merge": true}'
        result = self.analyzer._extract_json_from_response(text)
        assert result == {"merge": True}

    def test_extract_json_with_json_fence(self):
        """场景2：LLM返回 ```json 代码栅栏包裹的JSON - 应剥离栅栏解析"""
        text = '```json\n{"merge": [true, false, true]}\n```'
        result = self.analyzer._extract_json_from_response(text)
        assert result == {"merge": [True, False, True]}

    def test_extract_json_with_bare_fence(self):
        """场景3：LLM返回无语言标记的 ``` 栅栏包裹的JSON - 应剥离栅栏解析"""
        text = '```\n{"merge": false}\n```'
        result = self.analyzer._extract_json_from_response(text)
        assert result == {"merge": False}

    def test_extract_json_from_mixed_text(self):
        """场景4：LLM返回混合文本含JSON - 应取首{到尾}之间内容解析"""
        text = 'Here is the result: {"merge": true} done.'
        result = self.analyzer._extract_json_from_response(text)
        assert result == {"merge": True}

    def test_extract_json_returns_none_on_invalid(self):
        """场景5：三级容错全部失败 - 应返回None"""
        text = 'no json here at all'
        result = self.analyzer._extract_json_from_response(text)
        assert result is None

    def test_extract_json_returns_none_on_empty(self):
        """场景6：空字符串 - 应返回None"""
        result = self.analyzer._extract_json_from_response('')
        assert result is None

    def test_extract_json_real_world_error_case(self):
        """场景7：复现错误日志中的真实case（带前后空格的栅栏）"""
        # 这是错误日志中实际出现的格式
        text = '```json \n{"merge": [true, false, true, false, true, true, true, false, true, true, true, true, true, true, true, false, true, true, true]} \n```'
        result = self.analyzer._extract_json_from_response(text)
        assert result is not None
        assert len(result["merge"]) == 19
        assert result["merge"][0] == True
        assert result["merge"][1] == False

    def test_analyze_with_fenced_json_response(self):
        """集成测试：单次分析 - LLM返回```json栅栏包裹的JSON应正常解析不触发重试"""
        from unittest.mock import patch, MagicMock
        with patch.object(self.analyzer.client.chat.completions, 'create') as mock_create:
            mock_response = MagicMock()
            # 模拟LLM用 ```json 栅栏包裹响应
            mock_response.choices = [MagicMock(message=MagicMock(content='```json\n{"merge": true}\n```'))]
            mock_create.return_value = mock_response

            result = self.analyzer.analyze_semantic_relationship("Hello", "world", 'en')

            assert result == True
            # 应该只调用1次（不触发重试）
            assert mock_create.call_count == 1

    def test_batch_analyze_with_fenced_json_response(self):
        """集成测试：批量分析 - LLM返回```json栅栏包裹的JSON应正常解析不触发重试"""
        from unittest.mock import patch, MagicMock
        blocks = ["Hello", "world", "How are", "you"]
        with patch.object(self.analyzer.client.chat.completions, 'create') as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content='```json\n{"merge": [true, false, true]}\n```'))]
            mock_create.return_value = mock_response

            result = self.analyzer.batch_analyze_semantic_relationship(blocks, 'en')

            assert result == [True, False, True]
            # 应该只调用1次（不触发重试）
            assert mock_create.call_count == 1


class TestSemanticAnalyzerEmptyStreamingFallback:
    """测试流式响应 content 为空时从 reasoning_content fallback 提取 JSON"""

    def test_single_analyze_content_empty_reasoning_has_json(self, caplog):
        """场景：单次分析 - content 为空但 reasoning_content 含 JSON，应正常解析不触发重试"""
        import logging
        api_key = "test_key"
        api_url = "https://test-api.aiping.com/v1"
        model = "Qwen3-32B"
        analyzer = AipingSemanticAnalyzer(api_key, api_url, model)

        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
            # 模拟流式响应：content 为空，reasoning_content 含 JSON
            mock_chunk1 = MagicMock()
            mock_chunk1.choices = [MagicMock(
                delta=MagicMock(content=None, reasoning_content='{"merge": true}'),
                finish_reason=None
            )]
            mock_chunk2 = MagicMock()
            mock_chunk2.choices = [MagicMock(
                delta=MagicMock(content=None, reasoning_content=None),
                finish_reason='stop'
            )]
            mock_create.return_value = [mock_chunk1, mock_chunk2]

            with caplog.at_level(logging.WARNING, logger='modules.aiping_semantic_analyzer'):
                result = analyzer.analyze_semantic_relationship("Hello", "world", 'en')

            assert result == True
            assert mock_create.call_count == 1  # 不触发重试
            # 验证 WARNING 日志包含诊断信息
            warning_messages = [r.message for r in caplog.records if r.levelno == logging.WARNING]
            assert any('content 为空' in msg for msg in warning_messages), \
                f"应记录 WARNING 诊断日志，实际: {warning_messages}"

    def test_batch_analyze_content_empty_reasoning_has_json(self, caplog):
        """场景：批量分析 - content 为空但 reasoning_content 含 JSON 数组，应正常解析不触发重试"""
        import logging
        api_key = "test_key"
        api_url = "https://test-api.aiping.com/v1"
        model = "Qwen3-32B"
        analyzer = AipingSemanticAnalyzer(api_key, api_url, model)

        blocks = ["Hello", "world", "How are", "you"]

        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
            # 模拟流式响应：content 为空，reasoning_content 含 JSON 数组
            mock_chunk1 = MagicMock()
            mock_chunk1.choices = [MagicMock(
                delta=MagicMock(content=None, reasoning_content='{"merge": [true, false, true]}'),
                finish_reason=None
            )]
            mock_chunk2 = MagicMock()
            mock_chunk2.choices = [MagicMock(
                delta=MagicMock(content=None, reasoning_content=None),
                finish_reason='stop'
            )]
            mock_create.return_value = [mock_chunk1, mock_chunk2]

            with caplog.at_level(logging.WARNING, logger='modules.aiping_semantic_analyzer'):
                result = analyzer.batch_analyze_semantic_relationship(blocks, 'en')

            assert result == [True, False, True]
            assert mock_create.call_count == 1  # 不触发重试
            warning_messages = [r.message for r in caplog.records if r.levelno == logging.WARNING]
            assert any('content 为空' in msg for msg in warning_messages), \
                f"应记录 WARNING 诊断日志，实际: {warning_messages}"

    def test_both_content_and_reasoning_empty_triggers_retry_and_default(self, caplog):
        """场景：content 和 reasoning_content 均为空，应记录 WARNING 走重试最终返回默认值"""
        import logging
        api_key = "test_key"
        api_url = "https://test-api.aiping.com/v1"
        model = "Qwen3-32B"
        analyzer = AipingSemanticAnalyzer(api_key, api_url, model)

        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
            # 模拟流式响应：content 和 reasoning_content 均为空（如 API 返回空响应）
            mock_chunk1 = MagicMock()
            mock_chunk1.choices = [MagicMock(
                delta=MagicMock(content=None, reasoning_content=None),
                finish_reason='stop'
            )]
            # 3 次重试都返回空响应
            mock_create.return_value = [mock_chunk1]

            with caplog.at_level(logging.WARNING, logger='modules.aiping_semantic_analyzer'):
                result = analyzer.analyze_semantic_relationship("Hello", "world", 'en')

            # 最终返回默认值 False
            assert result == False
            # 触发了 3 次重试
            assert mock_create.call_count == 3
            # 至少记录了一次 WARNING 诊断日志
            warning_messages = [r.message for r in caplog.records if r.levelno == logging.WARNING]
            assert any('content 为空' in msg for msg in warning_messages), \
                f"应记录 WARNING 诊断日志，实际: {warning_messages}"
            # reasoning_content 长度为 0
            assert any('reasoning_content长度=0' in msg for msg in warning_messages), \
                f"WARNING 应显示 reasoning_content长度=0，实际: {warning_messages}"


class TestSemanticAnalyzerBaseNonStreamingFallback:
    """测试 SemanticAnalyzer 基类非流式响应 content 为空时从 reasoning_content fallback"""

    def setup_method(self):
        self.analyzer = SemanticAnalyzer(
            api_key="test_key",
            api_url="https://test-api.example.com/v1",
            model="test-model"
        )

    def test_single_analyze_content_empty_reasoning_has_json(self, caplog):
        """场景：基类单次分析 - 非流式响应 content 为空但 reasoning_content 含 JSON，应正常解析不抛异常"""
        import logging
        with patch.object(self.analyzer.client.chat.completions, 'create') as mock_create:
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_message = MagicMock()
            mock_message.content = None  # content 为空
            mock_message.reasoning_content = '{"merge": true}'  # fallback 内容
            mock_choice.message = mock_message
            mock_choice.finish_reason = "stop"
            mock_response.choices = [mock_choice]
            mock_create.return_value = mock_response

            with caplog.at_level(logging.WARNING, logger='modules.semantic_analyzer'):
                result = self.analyzer.analyze_semantic_relationship("Hello", "world", 'en')

            assert result == True
            warning_messages = [r.message for r in caplog.records if r.levelno == logging.WARNING]
            assert any('content 为空' in msg for msg in warning_messages), \
                f"应记录 WARNING 诊断日志，实际: {warning_messages}"

    def test_batch_analyze_content_empty_reasoning_has_json(self, caplog):
        """场景：基类批量分析 - 非流式响应 content 为空但 reasoning_content 含 JSON 数组，应正常解析不抛异常"""
        import logging
        blocks = ["Hello", "world", "How are", "you"]
        with patch.object(self.analyzer.client.chat.completions, 'create') as mock_create:
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_message = MagicMock()
            mock_message.content = None
            mock_message.reasoning_content = '{"merge": [true, false, true]}'
            mock_choice.message = mock_message
            mock_choice.finish_reason = "stop"
            mock_response.choices = [mock_choice]
            mock_create.return_value = mock_response

            with caplog.at_level(logging.WARNING, logger='modules.semantic_analyzer'):
                result = self.analyzer.batch_analyze_semantic_relationship(blocks, 'en')

            assert result == [True, False, True]
            warning_messages = [r.message for r in caplog.records if r.levelno == logging.WARNING]
            assert any('content 为空' in msg for msg in warning_messages), \
                f"应记录 WARNING 诊断日志，实际: {warning_messages}"

    def test_both_content_and_reasoning_empty_triggers_jsondecodeerror(self, caplog):
        """场景：基类单次分析 - content 和 reasoning_content 均为空，应记录 WARNING 并走 JSONDecodeError 逻辑"""
        import logging
        with patch.object(self.analyzer.client.chat.completions, 'create') as mock_create:
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_message = MagicMock()
            mock_message.content = None
            mock_message.reasoning_content = None
            mock_choice.message = mock_message
            mock_choice.finish_reason = "stop"
            mock_response.choices = [mock_choice]
            mock_create.return_value = mock_response

            with caplog.at_level(logging.WARNING, logger='modules.semantic_analyzer'):
                result = self.analyzer.analyze_semantic_relationship("Hello", "world", 'en')

            # 基类单次分析无重试，直接返回 False
            assert result == False
            warning_messages = [r.message for r in caplog.records if r.levelno == logging.WARNING]
            assert any('content 为空' in msg for msg in warning_messages), \
                f"应记录 WARNING 诊断日志，实际: {warning_messages}"
            assert any('reasoning_content长度=0' in msg for msg in warning_messages), \
                f"WARNING 应显示 reasoning_content长度=0，实际: {warning_messages}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
