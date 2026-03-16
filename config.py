import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """配置类"""
    
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # 上传配置
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    OUTPUT_FOLDER = os.path.join(os.getcwd(), 'outputs')
    
    # aiping API配置
    AIPING_API_KEY = os.environ.get('AIPING_API_KEY')
    AIPING_API_URL = os.environ.get('AIPING_API_URL') or 'https://aiping.cn/api/v1'
    AIPING_MODEL = os.environ.get('AIPING_MODEL_TRANSLATION') or 'Qwen3-32B'
    AIPING_MODEL_LAYOUT = os.environ.get('AIPING_MODEL_LAYOUT') or 'Qwen3-32B'
    AIPING_MODEL_GLOSSARY = os.environ.get('AIPING_MODEL_GLOSSARY') or 'Qwen3-32B'
    AIPING_EXTRA_BODY = {
        "provider": {
            "only": [],
            "order": [],
            "sort": "output_price",
            "input_price_range": [],
            "output_price_range": [],
            "input_length_range": [],
            "throughput_range": [],
            "latency_range": []
        }
    }
    
    # 硅基流动API配置
    SILICON_FLOW_API_KEY = os.environ.get('SILICON_FLOW_API_KEY')
    SILICON_FLOW_API_URL = os.environ.get('SILICON_FLOW_API_URL') or 'https://api.siliconflow.cn/v1'
    SILICON_FLOW_MODEL = os.environ.get('SILICON_FLOW_MODEL_TRANSLATION') or 'tencent/Hunyuan-MT-7B'
    SILICON_FLOW_MODEL_LAYOUT = os.environ.get('SILICON_FLOW_MODEL_LAYOUT') or 'Qwen/Qwen3-32B'
    SILICON_FLOW_MODEL_GLOSSARY = os.environ.get('SILICON_FLOW_MODEL_GLOSSARY') or 'Qwen/Qwen3-32B'
    
    # 支持的语言列表
    SUPPORTED_LANGUAGES = {
        'zh': '中文',
        'en': '英语',
        'ja': '日语',
        'ko': '韩语',
        'fr': '法语',
        'de': '德语',
        'es': '西班牙语',
        'ru': '俄语'
    }
    
    # 默认语言设置
    DEFAULT_SOURCE_LANGUAGE = 'en'
    DEFAULT_TARGET_LANGUAGE = 'zh'
    
    # 默认翻译服务
    DEFAULT_TRANSLATOR = 'aiping'
    
    # 文档类型配置
    DEFAULT_DOC_TYPE = os.environ.get('DEFAULT_DOC_TYPE') or 'AI技术'
    SUPPORTED_DOC_TYPES = ['AI技术', '技术文档', '商务文档', '学术论文', '法律文档', '医学文档']
    
    # 线程池配置
    MAX_WORKERS = int(os.environ.get('MAX_WORKERS', '8'))  # 最大线程数
    TRANSLATION_BATCH_SIZE = int(os.environ.get('TRANSLATION_BATCH_SIZE', '10'))  # 翻译批处理大小

    # 两阶段并行合并配置
    USE_TWO_PHASE_MERGE = os.environ.get('USE_TWO_PHASE_MERGE', 'true').lower() == 'true'  # 是否使用两阶段并行合并
    MERGE_MAX_WORKERS = int(os.environ.get('MERGE_MAX_WORKERS', '5'))  # 并行合并的最大线程数
    MERGE_BATCH_SIZE = int(os.environ.get('MERGE_BATCH_SIZE', '20'))  # 每批处理的文本对数量

# 创建配置实例
config = Config()
