import os
import platform
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """配置类，支持运行时通过 _load() 重载环境变量"""

    # 不会变化的静态常量可以保持在类级别
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB

    SUPPORTED_LANGUAGES = {
        'zh': '中文',
        'en': '英语',
        'ja': '日语',
        'ko': '韩语',
        'fr': '法语',
        'de': '德语',
        'es': '西班牙语',
        'ru': '俄语',
        'bo': '藏文'
    }

    # 默认语言设置
    DEFAULT_SOURCE_LANGUAGE = 'en'
    DEFAULT_TARGET_LANGUAGE = 'zh'
    DEFAULT_TRANSLATOR = 'aiping'

    # aiping extra body (纯字典，无需重载)
    AIPING_EXTRA_BODY = {
        "enable_thinking": False,
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

    # 硅基流动 extra body
    SILICON_FLOW_EXTRA_BODY = {"enable_thinking": False}

    # 百度千帆 extra body
    QIANFAN_EXTRA_BODY = {
        "enable_thinking": False,            # Qwen3 系列关闭思考
        "thinking": {"type": "disabled"},    # GLM-4.5+/5.x 系列关闭思考
    }

    def __init__(self):
        """初始化配置，调用 _load() 读取环境变量"""
        self._load()

    def _load(self):
        """（重）加载环境变量配置

        将所有依赖环境变量的属性从类级别移到实例级别（惰性求值）。
        支持在运行时修改环境变量后调用此方法刷新配置。
        """
        # 基本配置
        self.SECRET_KEY = os.environ.get('SECRET_KEY')
        if not self.SECRET_KEY:
            raise RuntimeError("SECRET_KEY 环境变量未设置，请在 .env 文件中配置")
        self.DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

        # 上传配置
        self.UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
        self.OUTPUT_FOLDER = os.path.join(os.getcwd(), 'outputs')

        # aiping API配置
        self.AIPING_API_KEY = os.environ.get('AIPING_API_KEY')
        self.AIPING_API_URL = os.environ.get('AIPING_API_URL') or 'https://aiping.cn/api/v1'
        self.AIPING_MODEL = os.environ.get('AIPING_MODEL_TRANSLATION') or 'Qwen3-32B'
        self.AIPING_MODEL_LAYOUT = os.environ.get('AIPING_MODEL_LAYOUT') or 'Qwen3-32B'
        self.AIPING_MODEL_GLOSSARY = os.environ.get('AIPING_MODEL_GLOSSARY') or 'Qwen3-32B'

        # 硅基流动API配置
        self.SILICON_FLOW_API_KEY = os.environ.get('SILICON_FLOW_API_KEY')
        self.SILICON_FLOW_API_URL = os.environ.get('SILICON_FLOW_API_URL') or 'https://api.siliconflow.cn/v1'
        self.SILICON_FLOW_MODEL = os.environ.get('SILICON_FLOW_MODEL_TRANSLATION') or 'tencent/Hunyuan-MT-7B'
        self.SILICON_FLOW_MODEL_LAYOUT = os.environ.get('SILICON_FLOW_MODEL_LAYOUT') or 'Qwen/Qwen3-32B'
        self.SILICON_FLOW_MODEL_GLOSSARY = os.environ.get('SILICON_FLOW_MODEL_GLOSSARY') or 'Qwen/Qwen3-32B'

        # 百度千帆API配置
        self.QIANFAN_API_KEY = os.environ.get('QIANFAN_API_KEY')
        self.QIANFAN_API_URL = os.environ.get('QIANFAN_API_URL') or 'https://qianfan.baidubce.com/v2'
        self.QIANFAN_MODEL = os.environ.get('QIANFAN_MODEL_TRANSLATION') or 'Qwen3-32B'
        self.QIANFAN_MODEL_LAYOUT = os.environ.get('QIANFAN_MODEL_LAYOUT') or 'Qwen3-32B'
        self.QIANFAN_MODEL_GLOSSARY = os.environ.get('QIANFAN_MODEL_GLOSSARY') or 'Qwen3-32B'

        # 文档类型配置
        self.DEFAULT_DOC_TYPE = os.environ.get('DEFAULT_DOC_TYPE') or 'AI技术'

        # 线程池配置
        self.MAX_WORKERS = int(os.environ.get('MAX_WORKERS', '8'))
        self.TRANSLATION_BATCH_SIZE = int(os.environ.get('TRANSLATION_BATCH_SIZE', '10'))

        # 两阶段并行合并配置
        self.USE_TWO_PHASE_MERGE = os.environ.get('USE_TWO_PHASE_MERGE', 'true').lower() == 'true'
        self.MERGE_MAX_WORKERS = int(os.environ.get('MERGE_MAX_WORKERS', '5'))
        self.MERGE_BATCH_SIZE = int(os.environ.get('MERGE_BATCH_SIZE', '20'))

        # OCR配置
        self.USE_OCR = os.environ.get('USE_OCR', 'false').lower() == 'true'
        self.OCR_ENGINE = os.environ.get('OCR_ENGINE') or 'paddleocr'
        self.OCR_LANGUAGE = os.environ.get('OCR_LANGUAGE') or 'ch'
        _default_use_gpu = 'false' if platform.system() == 'Darwin' else 'true'
        self.OCR_USE_GPU = os.environ.get('OCR_USE_GPU', _default_use_gpu).lower() == 'true'

        # OCR 内存激进优化配置
        self.OCR_SKIP_TABLE = os.environ.get('OCR_SKIP_TABLE', 'false').lower() == 'true'
        self.OCR_SKIP_FORMULA = os.environ.get('OCR_SKIP_FORMULA', 'false').lower() == 'true'
        self.OCR_PADDLE_DPI = int(os.environ.get('OCR_PADDLE_DPI', '120'))

        # OCR 超时与重试配置
        self.OCR_HEARTBEAT_TIMEOUT = int(os.environ.get('OCR_HEARTBEAT_TIMEOUT', '300'))
        self.OCR_MAX_TOTAL_TIME = int(os.environ.get('OCR_MAX_TOTAL_TIME', '252000'))
        self.OCR_STALL_TIMEOUT = int(os.environ.get('OCR_STALL_TIMEOUT', '1800'))
        self.OCR_MAX_RETRIES = int(os.environ.get('OCR_MAX_RETRIES', '2'))
        self.OCR_RETRY_BACKOFF = float(os.environ.get('OCR_RETRY_BACKOFF', '5.0'))
        self.OCR_DYNAMIC_PARAMS = os.environ.get('OCR_DYNAMIC_PARAMS', 'true').lower() == 'true'

        # 翻译API参数
        self.TRANSLATION_TEMPERATURE = float(os.environ.get('TRANSLATION_TEMPERATURE', '0.1'))
        self.TRANSLATION_TOP_P = float(os.environ.get('TRANSLATION_TOP_P', '0.9'))
        self.TRANSLATION_MAX_TOKENS = int(os.environ.get('TRANSLATION_MAX_TOKENS', '8192'))
        self.TRANSLATION_TIMEOUT = int(os.environ.get('TRANSLATION_TIMEOUT', '30'))

        # 语义分析参数
        self.SEMANTIC_ANALYSIS_TEMPERATURE = float(os.environ.get('SEMANTIC_ANALYSIS_TEMPERATURE', '0.1'))
        self.SEMANTIC_ANALYSIS_TOP_P = float(os.environ.get('SEMANTIC_ANALYSIS_TOP_P', '0.9'))
        self.SEMANTIC_ANALYSIS_SINGLE_MAX_TOKENS = int(os.environ.get('SEMANTIC_ANALYSIS_SINGLE_MAX_TOKENS', '1024'))
        self.SEMANTIC_ANALYSIS_BATCH_MAX_TOKENS = int(os.environ.get('SEMANTIC_ANALYSIS_BATCH_MAX_TOKENS', '2048'))
        self.SEMANTIC_ANALYSIS_TIMEOUT = int(os.environ.get('SEMANTIC_ANALYSIS_TIMEOUT', '30'))

        # 术语提取API参数
        self.GLOSSARY_TEMPERATURE = float(os.environ.get('GLOSSARY_TEMPERATURE', '0.3'))
        self.GLOSSARY_MAX_TOKENS = int(os.environ.get('GLOSSARY_MAX_TOKENS', '4096'))
        self.GLOSSARY_TIMEOUT = int(os.environ.get('GLOSSARY_TIMEOUT', '30'))

        # 排版/Markdown生成参数
        self.LAYOUT_TEMPERATURE = float(os.environ.get('LAYOUT_TEMPERATURE', '0.1'))
        self.LAYOUT_MAX_TOKENS = int(os.environ.get('LAYOUT_MAX_TOKENS', '8192'))

        # 翻译后格式排版开关
        self.ENABLE_FORMAT_BLOCKS = os.environ.get('ENABLE_FORMAT_BLOCKS', 'false')

        # LLM OCR配置
        self.AIPING_OCR_LLM_MODEL = os.environ.get('AIPING_OCR_LLM_MODEL') or 'DeepSeek-OCR'
        self.SILICON_FLOW_OCR_LLM_MODEL = os.environ.get('SILICON_FLOW_OCR_LLM_MODEL') or 'deepseek-ai/DeepSeek-OCR'
        self.QIANFAN_OCR_LLM_MODEL = os.environ.get('QIANFAN_OCR_LLM_MODEL') or 'DeepSeek-OCR'
        self.OCR_LLM_MAX_TOKENS = int(os.environ.get('OCR_LLM_MAX_TOKENS', '8000'))
        self.OCR_LLM_TEMPERATURE = float(os.environ.get('OCR_LLM_TEMPERATURE', '0.1'))
        self.OCR_LLM_FREQUENCY_PENALTY = float(os.environ.get('OCR_LLM_FREQUENCY_PENALTY', '0.0'))
        self.OCR_LLM_PRESENCE_PENALTY = float(os.environ.get('OCR_LLM_PRESENCE_PENALTY', '0.0'))
        self.OCR_LLM_DPI = int(os.environ.get('OCR_LLM_DPI', '150'))
        self.OCR_LLM_TIMEOUT = int(os.environ.get('OCR_LLM_TIMEOUT', '300'))


# 创建配置实例
config = Config()
