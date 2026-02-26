from .semantic_analyzer import SemanticAnalyzer
from .aiping_semantic_analyzer import AipingSemanticAnalyzer

class SemanticAnalyzerFactory:
    """语义分析器工厂类
    
    用于创建不同类型的语义分析器实例
    """
    
    @staticmethod
    def create_analyzer(analyzer_type, api_key, api_url, model):
        """创建语义分析器实例
        
        Args:
            analyzer_type (str): 分析器类型，可选值: "aiping", "silicon_flow"
            api_key (str): API密钥
            api_url (str): API请求地址
            model (str): 要使用的模型名称
            
        Returns:
            SemanticAnalyzer: 语义分析器实例
        """
        if analyzer_type == "aiping":
            return AipingSemanticAnalyzer(api_key, api_url, model)
        else:  # silicon_flow or other
            return SemanticAnalyzer(api_key, api_url, model)
    
    @staticmethod
    def get_available_analyzers():
        """获取可用的语义分析器类型
        
        Returns:
            list: 可用的分析器类型列表
        """
        return ["aiping", "silicon_flow"]
