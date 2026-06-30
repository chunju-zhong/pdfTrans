import os
import tempfile
import pytest
import inspect
from unittest.mock import patch, MagicMock
from services.glossary_service import glossary_service
from modules.glossary_extractor import (
    create_glossary_extractor,
    BaseApiGlossaryExtractor,
    AipingGlossaryExtractor,
    SiliconFlowGlossaryExtractor,
    QianfanGlossaryExtractor,
    GLOSSARY_CORE_REQUIREMENT_DOMAIN,
    GLOSSARY_CORE_REQUIREMENT_EXCLUDE_COMMON,
    GLOSSARY_CORE_REQUIREMENT_ANALYZE,
    GLOSSARY_CORE_REQUIREMENT_NO_TERMS,
    GLOSSARY_CORE_REQUIREMENT_NO_GLOSSARY,
    GLOSSARY_CORE_REQUIREMENT_UNCERTAIN,
    GLOSSARY_CORE_REQUIREMENT_STRICT_NO_GLOSSARY,
    GLOSSARY_CORE_REQUIREMENT_OUTPUT_FORMAT,
    GLOSSARY_IMPORTANT_SOURCE_LANG,
    GLOSSARY_IMPORTANT_SOURCE_LANG_VERIFY,
    GLOSSARY_IMPORTANT_KEEP_ORIGINAL,
)


class TestGlossaryExtractor:
    """术语提取器测试类"""
    
    def test_glossary_service_initialization(self):
        """测试术语提取服务初始化"""
        assert glossary_service is not None
    
    def test_create_glossary_extractor(self):
        """测试创建术语提取器"""
        # 测试创建aiping术语提取器
        aiping_extractor = create_glossary_extractor('aiping')
        assert aiping_extractor is not None
        assert isinstance(aiping_extractor, AipingGlossaryExtractor)
        
        # 测试创建硅基流动术语提取器
        silicon_flow_extractor = create_glossary_extractor('silicon_flow')
        assert silicon_flow_extractor is not None
        assert isinstance(silicon_flow_extractor, SiliconFlowGlossaryExtractor)
        
        # 测试创建百度千帆术语提取器
        qianfan_extractor = create_glossary_extractor('qianfan')
        assert qianfan_extractor is not None
        assert isinstance(qianfan_extractor, QianfanGlossaryExtractor)
    
    def test_base_api_glossary_extractor_inheritance(self):
        """测试 BaseApiGlossaryExtractor 继承结构"""
        # 验证所有提取器都继承自 BaseApiGlossaryExtractor
        assert issubclass(AipingGlossaryExtractor, BaseApiGlossaryExtractor)
        assert issubclass(SiliconFlowGlossaryExtractor, BaseApiGlossaryExtractor)
        assert issubclass(QianfanGlossaryExtractor, BaseApiGlossaryExtractor)
    
    def test_qianfan_glossary_extractor_init(self):
        """测试 QianfanGlossaryExtractor 初始化"""
        extractor = QianfanGlossaryExtractor(
            api_key='test_key',
            api_url='https://test.api.com',
            model='test-model'
        )
        assert extractor.api_key == 'test_key'
        assert extractor.api_url == 'https://test.api.com'
        assert extractor.model == 'test-model'
        assert extractor.provider_name == 'qianfan'
    
    def test_extract_glossary_from_text(self):
        """测试从文本中提取术语"""
        # 创建测试文本
        test_text = """Large Language Model (LLM) is a type of artificial intelligence that can generate human-like text. 
AI agents are autonomous systems that can perform tasks without human intervention. 
The agent paradigm has shifted from passive, discrete tasks to autonomous problem-solving. 
Prompt engineering is the process of designing effective prompts for LLMs."""
        
        # 测试aiping术语提取器
        aiping_extractor = create_glossary_extractor('aiping')
        glossary = aiping_extractor.extract_glossary(test_text, 'en', 'zh')
        assert isinstance(glossary, str)
        # 验证术语表格式
        if glossary:
            lines = glossary.strip().split('\n')
            for line in lines:
                assert ': ' in line, f"术语格式错误: {line}"
        
        # 测试硅基流动术语提取器
        silicon_flow_extractor = create_glossary_extractor('silicon_flow')
        glossary = silicon_flow_extractor.extract_glossary(test_text, 'en', 'zh')
        assert isinstance(glossary, str)
        # 验证术语表格式
        if glossary:
            lines = glossary.strip().split('\n')
            for line in lines:
                assert ': ' in line, f"术语格式错误: {line}"
        
        # 测试百度千帆术语提取器
        qianfan_extractor = create_glossary_extractor('qianfan')
        glossary = qianfan_extractor.extract_glossary(test_text, 'en', 'zh')
        assert isinstance(glossary, str)
        if glossary:
            lines = glossary.strip().split('\n')
            for line in lines:
                assert ': ' in line, f"术语格式错误: {line}"
    
    def test_extract_glossary_empty_text(self):
        """测试从空文本中提取术语"""
        empty_text = ""
        
        # 测试aiping术语提取器
        aiping_extractor = create_glossary_extractor('aiping')
        glossary = aiping_extractor.extract_glossary(empty_text, 'en', 'zh')
        assert isinstance(glossary, str)
        
        # 测试硅基流动术语提取器
        silicon_flow_extractor = create_glossary_extractor('silicon_flow')
        glossary = silicon_flow_extractor.extract_glossary(empty_text, 'en', 'zh')
        assert isinstance(glossary, str)
        
        # 测试百度千帆术语提取器
        qianfan_extractor = create_glossary_extractor('qianfan')
        glossary = qianfan_extractor.extract_glossary(empty_text, 'en', 'zh')
        assert isinstance(glossary, str)
    
    def test_extract_glossary_short_text(self):
        """测试从短文本中提取术语"""
        short_text = "Hello world"
        
        # 测试aiping术语提取器
        aiping_extractor = create_glossary_extractor('aiping')
        glossary = aiping_extractor.extract_glossary(short_text, 'en', 'zh')
        assert isinstance(glossary, str)
        
        # 测试硅基流动术语提取器
        silicon_flow_extractor = create_glossary_extractor('silicon_flow')
        glossary = silicon_flow_extractor.extract_glossary(short_text, 'en', 'zh')
        assert isinstance(glossary, str)
        
        # 测试百度千帆术语提取器
        qianfan_extractor = create_glossary_extractor('qianfan')
        glossary = qianfan_extractor.extract_glossary(short_text, 'en', 'zh')
        assert isinstance(glossary, str)



class TestGlossaryExtractorRefactoring:
    """术语提取器重构测试类 - 验证代码优化后的新结构"""
    
    def test_extract_glossary_function_length(self):
        """测试extract_glossary()函数行数不超过50行"""
        source = inspect.getsource(BaseApiGlossaryExtractor.extract_glossary)
        lines = source.strip().split('\n')
        assert len(lines) <= 50, f"extract_glossary()函数超过50行，当前{len(lines)}行"
    
    def test_build_prompt_function_length(self):
        """测试_build_prompt()方法行数不超过50行"""
        source = inspect.getsource(BaseApiGlossaryExtractor._build_prompt)
        lines = source.strip().split('\n')
        assert len(lines) <= 50, f"_build_prompt()方法超过50行，当前{len(lines)}行"
    
    def test_call_api_function_length(self):
        """测试_call_api()方法行数不超过50行"""
        source = inspect.getsource(BaseApiGlossaryExtractor._call_api)
        lines = source.strip().split('\n')
        assert len(lines) <= 50, f"_call_api()方法超过50行，当前{len(lines)}行"
    
    def test_process_response_function_length(self):
        """测试_process_response()方法行数不超过50行"""
        source = inspect.getsource(BaseApiGlossaryExtractor._process_response)
        lines = source.strip().split('\n')
        assert len(lines) <= 50, f"_process_response()方法超过50行，当前{len(lines)}行"
    
    def test_format_glossary_function_length(self):
        """测试_format_glossary()方法行数不超过50行"""
        source = inspect.getsource(BaseApiGlossaryExtractor._format_glossary)
        lines = source.strip().split('\n')
        assert len(lines) <= 50, f"_format_glossary()方法超过50行，当前{len(lines)}行"
    
    def test_glossary_constants_exist(self):
        """测试术语提取常量已定义"""
        constants = [
            GLOSSARY_CORE_REQUIREMENT_DOMAIN,
            GLOSSARY_CORE_REQUIREMENT_EXCLUDE_COMMON,
            GLOSSARY_CORE_REQUIREMENT_ANALYZE,
            GLOSSARY_CORE_REQUIREMENT_NO_TERMS,
            GLOSSARY_CORE_REQUIREMENT_NO_GLOSSARY,
            GLOSSARY_CORE_REQUIREMENT_UNCERTAIN,
            GLOSSARY_CORE_REQUIREMENT_STRICT_NO_GLOSSARY,
            GLOSSARY_CORE_REQUIREMENT_OUTPUT_FORMAT,
            GLOSSARY_IMPORTANT_SOURCE_LANG,
            GLOSSARY_IMPORTANT_SOURCE_LANG_VERIFY,
            GLOSSARY_IMPORTANT_KEEP_ORIGINAL,
        ]
        for constant in constants:
            assert isinstance(constant, str), f"常量类型错误: {constant}"
            assert len(constant) > 0, "常量内容为空"
    
    def test_glossary_constants_contain_placeholders(self):
        """测试术语提取常量包含正确的占位符"""
        assert "{doc_type_text}" in GLOSSARY_CORE_REQUIREMENT_DOMAIN
        assert "{doc_type_text}" in GLOSSARY_CORE_REQUIREMENT_EXCLUDE_COMMON
        assert "{doc_type_text}" in GLOSSARY_CORE_REQUIREMENT_ANALYZE
        assert "{source_lang_name}" in GLOSSARY_IMPORTANT_SOURCE_LANG
        assert "{source_lang_name}" in GLOSSARY_IMPORTANT_SOURCE_LANG_VERIFY
    
    def test_build_prompt_uses_constants(self):
        """测试_build_prompt()方法使用常量构建提示词"""
        extractor = BaseApiGlossaryExtractor(
            api_key='test_key',
            api_url='https://test.api.com',
            model='test-model'
        )
        prompt = extractor._build_prompt("test text", "en", "zh")
        assert isinstance(prompt, str)
        assert len(prompt) > 0
    
    def test_format_glossary_handles_no_glossary(self):
        """测试_format_glossary()方法正确处理NO_GLOSSARY标识"""
        extractor = BaseApiGlossaryExtractor(
            api_key='test_key',
            api_url='https://test.api.com',
            model='test-model'
        )
        result = extractor._format_glossary("NO_GLOSSARY")
        assert result == ""
        
        result = extractor._format_glossary("NO_GLOSSARY\nAI: 人工智能")
        assert result == "AI: 人工智能"
    
    def test_format_glossary_formats_lines(self):
        """测试_format_glossary()方法正确格式化术语行"""
        extractor = BaseApiGlossaryExtractor(
            api_key='test_key',
            api_url='https://test.api.com',
            model='test-model'
        )
        input_text = "LLM: 大语言模型\nAI: 人工智能\nMachine Learning"
        result = extractor._format_glossary(input_text)
        lines = result.split('\n')
        assert len(lines) == 3
        assert "LLM: 大语言模型" in lines
        assert "AI: 人工智能" in lines
        assert "Machine Learning: Machine Learning" in lines
    
    def test_extract_glossary_calls_helper_methods(self):
        """测试extract_glossary()方法调用辅助方法"""
        extractor = BaseApiGlossaryExtractor(
            api_key='test_key',
            api_url='https://test.api.com',
            model='test-model'
        )
        
        with patch.object(extractor, '_build_prompt', return_value='test prompt') as mock_build:
            with patch.object(extractor, '_call_api', return_value=MagicMock(
                choices=[MagicMock(message=MagicMock(content='LLM: 大语言模型'))]
            )) as mock_call:
                with patch.object(extractor, '_process_response', return_value='LLM: 大语言模型') as mock_process:
                    result = extractor.extract_glossary("test text", "en", "zh")
                    mock_build.assert_called_once()
                    mock_call.assert_called_once_with('test prompt')
                    mock_process.assert_called_once()
                    assert result == 'LLM: 大语言模型'
    
    def test_extract_glossary_error_handling(self):
        """测试extract_glossary()方法正确处理异常"""
        extractor = BaseApiGlossaryExtractor(
            api_key='test_key',
            api_url='https://test.api.com',
            model='test-model'
        )
        
        with patch.object(extractor, '_build_prompt', side_effect=Exception("API Error")):
            result = extractor.extract_glossary("test text", "en", "zh")
            assert result == ""


class TestTibetanTerminologyMap:
    """藏文术语对照表测试类"""
    
    def test_tibetan_terminology_map_exists(self):
        """测试藏文术语对照表常量已定义"""
        from prompts.language_rules.bo_to_zh import TIBETAN_TERMINOLOGY_MAP
        assert isinstance(TIBETAN_TERMINOLOGY_MAP, dict)
        assert len(TIBETAN_TERMINOLOGY_MAP) > 0
    
    def test_tibetan_terminology_map_content(self):
        """测试藏文术语对照表包含关键术语"""
        from prompts.language_rules.bo_to_zh import TIBETAN_TERMINOLOGY_MAP
        
        expected_terms = {
            "ལྡེབ": "页/篇/牒",
            "ལྡེའུ་མིག": "目录/纲要",
            "དཀར་ཆག": "目录/总纲/名录",
            "ཞལ་གདམས": "教诲/教授/口诀",
            "རིན་པོ་ཆེ": "珍宝/珍贵",
            "རྫོགས་པ་ཆེན་པོ": "大圆满",
            "བྱིན་རླབས": "加持",
        }
        
        for tibetan, chinese in expected_terms.items():
            assert tibetan in TIBETAN_TERMINOLOGY_MAP, f"缺失术语: {tibetan}"
            assert TIBETAN_TERMINOLOGY_MAP[tibetan] == chinese, f"术语翻译错误: {tibetan}"
    
    def test_format_terminology_table_function(self):
        """测试format_terminology_table()函数"""
        from prompts.language_rules.bo_to_zh import format_terminology_table
        
        result_with_notes = format_terminology_table(with_notes=True)
        assert isinstance(result_with_notes, str)
        assert len(result_with_notes) > 0
        
        result_without_notes = format_terminology_table(with_notes=False)
        assert isinstance(result_without_notes, str)
        assert len(result_without_notes) > 0
        
        assert len(result_with_notes) > len(result_without_notes)
    
    def test_terminology_map_used_in_rules(self):
        """测试术语对照表在规则中被引用"""
        from prompts.language_rules.bo_to_zh import RULES, TIBETAN_TERMINOLOGY_MAP
        
        translation_rule = None
        glossary_rule = None
        
        for rule in RULES:
            if rule.task_type == "translation" and rule.source_lang == "bo":
                translation_rule = rule
            if rule.task_type == "glossary" and rule.source_lang == "bo":
                glossary_rule = rule
        
        assert translation_rule is not None, "翻译规则未找到"
        assert glossary_rule is not None, "术语提取规则未找到"
        
        content_translation = translation_rule.content
        content_glossary = glossary_rule.content
        
        for tibetan, chinese in TIBETAN_TERMINOLOGY_MAP.items():
            assert tibetan in content_translation or tibetan in content_glossary, \
                f"术语 {tibetan} 未在规则中使用"


if __name__ == "__main__":
    pytest.main([__file__])
