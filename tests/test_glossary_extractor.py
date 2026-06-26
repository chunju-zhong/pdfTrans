import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from services.glossary_service import glossary_service
from modules.glossary_extractor import (
    create_glossary_extractor,
    BaseApiGlossaryExtractor,
    AipingGlossaryExtractor,
    SiliconFlowGlossaryExtractor,
    QianfanGlossaryExtractor,
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


if __name__ == "__main__":
    pytest.main([__file__])
