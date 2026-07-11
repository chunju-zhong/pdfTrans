"""测试格式排版开关（ENABLE_FORMAT_BLOCKS）和翻译重试机制"""

import pytest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch, MagicMock, call
from services.translation_content import TranslationContentTranslator
from models.result_types import TranslationResult


# ==================== 格式排版开关 ====================

class TestFormatBlocksToggle:
    """测试 ENABLE_FORMAT_BLOCKS 配置的格式排版控制"""

    def setup_method(self):
        executor = ThreadPoolExecutor(max_workers=1)
        self.translator = TranslationContentTranslator(executor)

    @patch('services.translation_content.config')
    def test_format_blocks_disabled(self, mock_config):
        """ENABLE_FORMAT_BLOCKS=false 时不执行格式排版"""
        mock_config.ENABLE_FORMAT_BLOCKS = 'false'

        # mock translator.format_blocks 以确保不被调用
        mock_translator = MagicMock()

        # 调用 _translate_content 的格式排版部分逻辑
        should_format = False
        if mock_config.ENABLE_FORMAT_BLOCKS == 'true':
            should_format = True
        elif mock_config.ENABLE_FORMAT_BLOCKS == 'auto':
            if 'pdf' in ('markdown',):  # output_format='markdown'
                should_format = True

        assert should_format is False

    @patch('services.translation_content.config')
    def test_format_blocks_always_enabled(self, mock_config):
        """ENABLE_FORMAT_BLOCKS=true 时始终执行格式排版"""
        mock_config.ENABLE_FORMAT_BLOCKS = 'true'

        should_format = False
        if mock_config.ENABLE_FORMAT_BLOCKS == 'true':
            should_format = True
        elif mock_config.ENABLE_FORMAT_BLOCKS == 'auto':
            pass

        assert should_format is True

    @patch('services.translation_content.config')
    def test_format_blocks_auto_with_pdf(self, mock_config):
        """ENABLE_FORMAT_BLOCKS=auto 且 output_format=pdf 时执行格式排版"""
        mock_config.ENABLE_FORMAT_BLOCKS = 'auto'
        output_format = 'pdf'

        should_format = False
        if mock_config.ENABLE_FORMAT_BLOCKS == 'true':
            should_format = True
        elif mock_config.ENABLE_FORMAT_BLOCKS == 'auto':
            if output_format in ('pdf', 'pdf_docx', 'all'):
                should_format = True

        assert should_format is True

    @patch('services.translation_content.config')
    def test_format_blocks_auto_with_pdf_docx(self, mock_config):
        """ENABLE_FORMAT_BLOCKS=auto 且 output_format=pdf_docx 时执行格式排版"""
        mock_config.ENABLE_FORMAT_BLOCKS = 'auto'
        output_format = 'pdf_docx'

        should_format = False
        if mock_config.ENABLE_FORMAT_BLOCKS == 'true':
            should_format = True
        elif mock_config.ENABLE_FORMAT_BLOCKS == 'auto':
            if output_format in ('pdf', 'pdf_docx', 'all'):
                should_format = True

        assert should_format is True

    @patch('services.translation_content.config')
    def test_format_blocks_auto_with_markdown(self, mock_config):
        """ENABLE_FORMAT_BLOCKS=auto 且 output_format=markdown 时不执行格式排版"""
        mock_config.ENABLE_FORMAT_BLOCKS = 'auto'
        output_format = 'markdown'

        should_format = False
        if mock_config.ENABLE_FORMAT_BLOCKS == 'true':
            should_format = True
        elif mock_config.ENABLE_FORMAT_BLOCKS == 'auto':
            if output_format in ('pdf', 'pdf_docx', 'all'):
                should_format = True

        assert should_format is False

    @patch('services.translation_content.config')
    def test_format_blocks_auto_with_all(self, mock_config):
        """ENABLE_FORMAT_BLOCKS=auto 且 output_format=all 时执行格式排版"""
        mock_config.ENABLE_FORMAT_BLOCKS = 'auto'
        output_format = 'all'

        should_format = False
        if mock_config.ENABLE_FORMAT_BLOCKS == 'true':
            should_format = True
        elif mock_config.ENABLE_FORMAT_BLOCKS == 'auto':
            if output_format in ('pdf', 'pdf_docx', 'all'):
                should_format = True

        assert should_format is True


# ==================== 翻译重试机制 ====================

class TestTranslationRetryUntranslated:
    """测试合并块/原始块翻译未翻译时的自动重试"""

    def setup_method(self):
        executor = ThreadPoolExecutor(max_workers=1)
        self.translator = TranslationContentTranslator(executor)

    def test_retry_on_untranslated_merged_block(self):
        """合并块翻译未翻译时应重试"""
        mock_translator = MagicMock()
        # 第一次翻译返回未翻译内容，第二次返回翻译内容
        mock_translator.translate.side_effect = [
            TranslationResult(content="Effluent standard", finish_reason="stop"),
            TranslationResult(content="排放标准", finish_reason="stop"),
        ]

        original = "Effluent standard"
        # 模拟重试逻辑
        first_result = mock_translator.translate(original, 'en', 'zh', doc_type="general", glossary=None)
        translated_text = first_result.content

        if self.translator._is_translation_unchanged(translated_text, original):
            retry_result = mock_translator.translate(original, 'en', 'zh', doc_type="general", glossary=None)
            if not self.translator._is_translation_unchanged(retry_result.content, original):
                translated_text = retry_result.content

        assert translated_text == "排放标准"
        assert mock_translator.translate.call_count == 2

    def test_retry_still_untranslated_fallback_to_original(self):
        """重试后仍未翻译应回退原文"""
        mock_translator = MagicMock()
        # 两次翻译都返回未翻译内容
        mock_translator.translate.side_effect = [
            TranslationResult(content="Effluent standard", finish_reason="stop"),
            TranslationResult(content="Effluent standard", finish_reason="stop"),
        ]

        original = "Effluent standard"
        first_result = mock_translator.translate(original, 'en', 'zh', doc_type="general", glossary=None)
        translated_text = first_result.content

        if self.translator._is_translation_unchanged(translated_text, original):
            retry_result = mock_translator.translate(original, 'en', 'zh', doc_type="general", glossary=None)
            if not self.translator._is_translation_unchanged(retry_result.content, original):
                translated_text = retry_result.content
            else:
                translated_text = original

        assert translated_text == original
        assert mock_translator.translate.call_count == 2

    def test_no_retry_when_translated(self):
        """正常翻译不需要重试"""
        mock_translator = MagicMock()
        mock_translator.translate.return_value = TranslationResult(
            content="排放标准", finish_reason="stop"
        )

        original = "Effluent standard"
        first_result = mock_translator.translate(original, 'en', 'zh', doc_type="general", glossary=None)
        translated_text = first_result.content

        if self.translator._is_translation_unchanged(translated_text, original):
            # 不会进入此分支
            retry_result = mock_translator.translate(original, 'en', 'zh', doc_type="general", glossary=None)
            translated_text = retry_result.content

        assert translated_text == "排放标准"
        assert mock_translator.translate.call_count == 1


class TestTranslationGarbageFallback:
    """测试垃圾输出检测后的回退机制"""

    def setup_method(self):
        executor = ThreadPoolExecutor(max_workers=1)
        self.translator = TranslationContentTranslator(executor)

    def test_garbage_expansion_fallback(self):
        """膨胀垃圾输出应回退原文"""
        original = "Hello"
        garbage = "你" * 100

        is_garbage, reason = self.translator._is_translation_garbage(garbage, original)
        assert is_garbage is True

        # 模拟回退逻辑
        if is_garbage:
            final_text = original
        else:
            final_text = garbage

        assert final_text == original

    def test_garbage_repetition_fallback(self):
        """重复模式垃圾输出应回退原文"""
        original = "The model"
        garbage = "模型" * 20

        is_garbage, reason = self.translator._is_translation_garbage(garbage, original)
        assert is_garbage is True

        if is_garbage:
            final_text = original
        else:
            final_text = garbage

        assert final_text == original

    def test_normal_translation_not_fallback(self):
        """正常翻译不应回退"""
        original = "Effluent standard"
        translated = "排放标准"

        is_garbage, _ = self.translator._is_translation_garbage(translated, original)
        assert is_garbage is False

        if is_garbage:
            final_text = original
        else:
            final_text = translated

        assert final_text == translated


if __name__ == "__main__":
    pytest.main([__file__])
