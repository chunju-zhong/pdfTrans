"""测试翻译质量检测功能：未翻译检测增强、垃圾输出检测"""

import pytest
from concurrent.futures import ThreadPoolExecutor
from services.translation_content import TranslationContentTranslator


@pytest.fixture
def translator():
    executor = ThreadPoolExecutor(max_workers=1)
    return TranslationContentTranslator(executor)


# ==================== _normalize_for_comparison ====================

class TestNormalizeForComparison:
    """测试断字标记清理和空白归一化"""

    def test_soft_hyphen_newline_removed(self):
        """软连字符+换行应被去除"""
        result = TranslationContentTranslator._normalize_for_comparison("Simi\u00AD\nlarly")
        assert result == "Similarly"

    def test_regular_hyphen_newline_removed(self):
        """普通连字符+换行应被去除"""
        result = TranslationContentTranslator._normalize_for_comparison("Simi-\nlarly")
        assert result == "Similarly"

    def test_multiple_whitespace_collapsed(self):
        """多余空白应合并为单空格"""
        result = TranslationContentTranslator._normalize_for_comparison("hello   world\n\nfoo")
        assert result == "hello world foo"

    def test_empty_string(self):
        """空字符串"""
        assert TranslationContentTranslator._normalize_for_comparison("") == ""

    def test_no_change_needed(self):
        """无需修改的文本"""
        assert TranslationContentTranslator._normalize_for_comparison("hello world") == "hello world"


# ==================== _calculate_similarity ====================

class TestCalculateSimilarity:
    """测试字符级相似度计算"""

    def test_identical_strings(self):
        """相同字符串相似度为 1.0"""
        assert TranslationContentTranslator._calculate_similarity("hello", "hello") == 1.0

    def test_empty_strings(self):
        """空字符串相似度为 0.0"""
        assert TranslationContentTranslator._calculate_similarity("", "hello") == 0.0
        assert TranslationContentTranslator._calculate_similarity("hello", "") == 0.0
        assert TranslationContentTranslator._calculate_similarity("", "") == 0.0

    def test_completely_different(self):
        """完全不同的短字符串"""
        sim = TranslationContentTranslator._calculate_similarity("abc", "xyz")
        assert sim == 0.0

    def test_partial_overlap(self):
        """部分重叠的短字符串"""
        sim = TranslationContentTranslator._calculate_similarity("abcde", "cdefg")
        # LCS = "cde", max_len=5, similarity = 3/5 = 0.6
        assert 0.5 < sim < 0.7

    def test_long_text_uses_char_set_approximation(self):
        """长文本（>500字符）使用字符集交集近似"""
        text_a = "abcdefgh" * 100  # 800 chars
        text_b = "abcdefgh" * 100
        sim = TranslationContentTranslator._calculate_similarity(text_a, text_b)
        assert sim == 1.0

    def test_long_text_different(self):
        """长文本完全不同"""
        text_a = "a" * 600
        text_b = "z" * 600
        sim = TranslationContentTranslator._calculate_similarity(text_a, text_b)
        # 字符集交集为 0，但长度比 = 1.0，加权: 0.6*0 + 0.4*1.0 = 0.4
        assert sim == pytest.approx(0.4, abs=0.01)


# ==================== _contains_target_language_chars ====================

class TestContainsTargetLanguageChars:
    """测试目标语言字符检测"""

    def test_chinese_chars_detected(self):
        """含中文字符应返回 True"""
        assert TranslationContentTranslator._contains_target_language_chars("你好世界") is True

    def test_mixed_chinese_english(self):
        """中英混合应返回 True"""
        assert TranslationContentTranslator._contains_target_language_chars("Hello 世界") is True

    def test_english_only(self):
        """纯英文应返回 False"""
        assert TranslationContentTranslator._contains_target_language_chars("Hello world") is False

    def test_cjk_range_boundaries(self):
        """CJK 统一汉字范围边界"""
        assert TranslationContentTranslator._contains_target_language_chars("\u4e00") is True  # 一
        assert TranslationContentTranslator._contains_target_language_chars("\u9fff") is True  # 龥
        assert TranslationContentTranslator._contains_target_language_chars("\u4dff") is False  # CJK 前

    def test_empty_string(self):
        """空字符串"""
        assert TranslationContentTranslator._contains_target_language_chars("") is False


# ==================== _is_translation_unchanged（增强后） ====================

class TestIsTranslationUnchangedEnhanced:
    """测试增强后的未翻译检测"""

    def setup_method(self):
        executor = ThreadPoolExecutor(max_workers=1)
        self.translator = TranslationContentTranslator(executor)

    def test_high_similarity_no_chinese_returns_true(self):
        """高相似度且无中文字符 → 未翻译"""
        original = "The tokenizer is responsible for converting text into tokens"
        # 移除断字标记后的原文（模拟 LLM 去除连字符的行为）
        translated = "The tokenizer is responsible for converting text into tokens"
        assert self.translator._is_translation_unchanged(translated, original) is True

    def test_high_similarity_with_chinese_returns_false(self):
        """高相似度但含中文字符 → 已翻译"""
        original = "Hello world"
        translated = "Hello 世界"  # 有中文
        assert self.translator._is_translation_unchanged(translated, original) is False

    def test_pipe_separator_untranslated(self):
        """||| 分段但未翻译 → True（原有逻辑）"""
        original = "Effluent standard Separation option"
        translated = "Effluent standard ||| Separation option"
        assert self.translator._is_translation_unchanged(translated, original) is True

    def test_normal_translation_returns_false(self):
        """正常翻译 → False"""
        original = "Effluent standard"
        translated = "排放标准"
        assert self.translator._is_translation_unchanged(translated, original) is False

    def test_hyphenated_text_not_translated(self):
        """去除断字标记后高相似度且无中文 → True"""
        original = "Simi\u00AD\nlarly, the model uses a vocabu\u00AD\nlary of tokens"
        translated = "Similarly, the model uses a vocabulary of tokens"
        assert self.translator._is_translation_unchanged(translated, original) is True

    def test_low_similarity_no_chinese_returns_false(self):
        """低相似度无中文 → 不是未翻译（可能是垃圾输出，但不在本方法检测范围）"""
        original = "The quick brown fox"
        translated = "xyz abc def"  # 完全不同
        assert self.translator._is_translation_unchanged(translated, original) is False


# ==================== _is_translation_garbage ====================

class TestIsTranslationGarbage:
    """测试垃圾输出检测"""

    def setup_method(self):
        executor = ThreadPoolExecutor(max_workers=1)
        self.translator = TranslationContentTranslator(executor)

    def test_normal_translation_not_garbage(self):
        """正常翻译不是垃圾输出"""
        is_garbage, reason = self.translator._is_translation_garbage("排放标准", "Effluent standard")
        assert is_garbage is False
        assert reason == ""

    def test_expansion_detected(self):
        """膨胀检测：译文长度 > 原文 × 5"""
        original = "Hello"
        translated = "你" * 100  # 100 chars > 5 * 5
        is_garbage, reason = self.translator._is_translation_garbage(translated, original)
        assert is_garbage is True
        assert "膨胀" in reason

    def test_expansion_boundary(self):
        """膨胀边界：译文长度恰好 = 原文 × 5（不含）"""
        original = "a" * 10
        # 使用无重复模式的文本，确保只测试膨胀边界
        translated = "".join(chr(ord('b') + i % 26) for i in range(50))  # 50个不同字符，无重复模式
        assert len(translated) == 50  # 50 = 10 * 5
        is_garbage, reason = self.translator._is_translation_garbage(translated, original)
        # 50 > 10*5(=50) 为 False，且无重复模式 → 不是垃圾
        assert is_garbage is False

    def test_repetition_pattern_detected(self):
        """重复模式检测：同一子串重复 >10 次"""
        original = "Hello world"
        translated = "你好" * 20  # '你好' 重复 20 次
        is_garbage, reason = self.translator._is_translation_garbage(translated, original)
        assert is_garbage is True
        assert "重复" in reason

    def test_repetition_exactly_10_not_garbage(self):
        """重复恰好 10 次（不含 >10）不是垃圾"""
        original = "Hello"
        translated = "你好" * 10  # 10 次，需要 >10 才判定
        is_garbage, reason = self.translator._is_translation_garbage(translated, original)
        # 10 * 2 = 20 chars, original 5 chars, 20 < 5*5=25, not expansion
        # 重复次数恰好 10，不满足 >10 条件
        assert is_garbage is False

    def test_empty_original(self):
        """原文为空不应膨胀检测触发"""
        is_garbage, reason = self.translator._is_translation_garbage("翻译内容", "")
        assert is_garbage is False

    def test_short_repetition_not_garbage(self):
        """短文本有少量重复不应误判"""
        original = "The model"
        translated = "模型模型"  # 只有 2 次重复
        is_garbage, reason = self.translator._is_translation_garbage(translated, original)
        assert is_garbage is False


if __name__ == "__main__":
    pytest.main([__file__])
