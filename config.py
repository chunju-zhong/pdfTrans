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
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    OUTPUT_FOLDER = os.path.join(os.getcwd(), 'outputs')
    
    # 百度翻译API配置
    BAIDU_APP_ID = os.environ.get('BAIDU_APP_ID')
    BAIDU_APP_KEY = os.environ.get('BAIDU_APP_KEY')
    
    # aiping API配置
    AIPING_API_KEY = os.environ.get('AIPING_API_KEY')
    AIPING_API_URL = os.environ.get('AIPING_API_URL') or 'https://aiping.cn/api/v1'
    
    # 硅基流动API配置
    SILICON_FLOW_API_KEY = os.environ.get('SILICON_FLOW_API_KEY')
    SILICON_FLOW_API_URL = os.environ.get('SILICON_FLOW_API_URL') or 'https://api.siliconflow.cn/v1'
    
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

# 创建配置实例
config = Config()
