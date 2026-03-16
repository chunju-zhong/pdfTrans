import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.glossary_extractor import create_glossary_extractor


def test_domain_specific_glossary():
    """测试不同领域的术语提取功能"""
    # 创建术语提取器
    extractor = create_glossary_extractor('aiping')
    
    # 测试AI领域文本（英文）
    ai_text = """
    In the field of artificial intelligence, machine learning models are trained on large datasets. 
    Deep learning, a subset of machine learning, uses neural networks with multiple layers. 
    Natural language processing enables computers to understand and generate human language. 
    Computer vision allows machines to interpret and understand visual information from the world.
    """
    
    print("=== AI领域术语提取 ===")
    glossary_ai = extractor.extract_glossary(ai_text, 'English', 'Chinese', 'AI')
    print(glossary_ai)
    print("\n")
    
    # 测试医学领域文本（英文）
    medical_text = """
    In medicine, physicians diagnose and treat various diseases. 
    Cardiology focuses on the heart and cardiovascular system. 
    Neurology deals with disorders of the nervous system. 
    Oncology is the study and treatment of cancer. 
    Pharmacology involves the study of drugs and their effects.
    """
    
    print("=== 医学领域术语提取 ===")
    glossary_medical = extractor.extract_glossary(medical_text, 'English', 'Chinese', '医学')
    print(glossary_medical)
    print("\n")
    
    # 测试金融领域文本（英文）
    finance_text = """
    In finance, portfolio management involves selecting and managing investments. 
    Risk assessment is the process of evaluating potential losses. 
    Asset allocation refers to distributing investments across different asset classes. 
    Derivatives are financial instruments whose value is derived from an underlying asset. 
    Market liquidity refers to how easily assets can be bought or sold.
    """
    
    print("=== 金融领域术语提取 ===")
    glossary_finance = extractor.extract_glossary(finance_text, 'English', 'Chinese', '金融')
    print(glossary_finance)


if __name__ == "__main__":
    test_domain_specific_glossary()
