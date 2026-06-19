import os
import platform
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """配置类"""
    
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY 环境变量未设置，请在 .env 文件中配置")
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # 上传配置
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    OUTPUT_FOLDER = os.path.join(os.getcwd(), 'outputs')
    
    # aiping API配置
    AIPING_API_KEY = os.environ.get('AIPING_API_KEY')
    AIPING_API_URL = os.environ.get('AIPING_API_URL') or 'https://aiping.cn/api/v1'
    AIPING_MODEL = os.environ.get('AIPING_MODEL_TRANSLATION') or 'Qwen3-32B'
    AIPING_MODEL_LAYOUT = os.environ.get('AIPING_MODEL_LAYOUT') or 'Qwen3-32B'
    AIPING_MODEL_GLOSSARY = os.environ.get('AIPING_MODEL_GLOSSARY') or 'Qwen3-32B'
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
    
    # 硅基流动API配置
    SILICON_FLOW_API_KEY = os.environ.get('SILICON_FLOW_API_KEY')
    SILICON_FLOW_API_URL = os.environ.get('SILICON_FLOW_API_URL') or 'https://api.siliconflow.cn/v1'
    SILICON_FLOW_MODEL = os.environ.get('SILICON_FLOW_MODEL_TRANSLATION') or 'tencent/Hunyuan-MT-7B'
    SILICON_FLOW_MODEL_LAYOUT = os.environ.get('SILICON_FLOW_MODEL_LAYOUT') or 'Qwen/Qwen3-32B'
    SILICON_FLOW_MODEL_GLOSSARY = os.environ.get('SILICON_FLOW_MODEL_GLOSSARY') or 'Qwen/Qwen3-32B'
    SILICON_FLOW_EXTRA_BODY = {"enable_thinking": False}

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

    # OCR配置
    USE_OCR = os.environ.get('USE_OCR', 'false').lower() == 'true'  # 是否启用OCR提取
    OCR_ENGINE = os.environ.get('OCR_ENGINE') or 'paddleocr'  # OCR引擎类型
    OCR_LANGUAGE = os.environ.get('OCR_LANGUAGE') or 'ch'  # OCR识别语言
    # macOS 上默认使用 CPU，其他平台默认使用 GPU
    _default_use_gpu = 'false' if platform.system() == 'Darwin' else 'true'
    OCR_USE_GPU = os.environ.get('OCR_USE_GPU', _default_use_gpu).lower() == 'true'  # 是否使用GPU加速

    OCR_DPI = int(os.environ.get('OCR_DPI', '200'))  # OCR渲染DPI
    
    # OCR 内存激进优化配置 (Intel 16GB Mac 崩溃时可启用)
    OCR_SKIP_TABLE = os.environ.get('OCR_SKIP_TABLE', 'false').lower() == 'true'  # 跳过表格识别节省内存
    OCR_SKIP_FORMULA = os.environ.get('OCR_SKIP_FORMULA', 'false').lower() == 'true'  # 跳过公式识别节省内存
    OCR_RENDER_DPI = int(os.environ.get('OCR_RENDER_DPI', '120'))  # OCR渲染DPI: 120默认激进内存优化 | 150质量优先

    # OCR 超时与重试配置
    OCR_HEARTBEAT_TIMEOUT = int(os.environ.get('OCR_HEARTBEAT_TIMEOUT', '0'))  # 心跳超时(秒)，0=禁用，超过判定子进程死机
    OCR_MAX_TOTAL_TIME = int(os.environ.get('OCR_MAX_TOTAL_TIME', '252000'))  # OCR最大总执行时间(秒)
    OCR_STALL_TIMEOUT = int(os.environ.get('OCR_STALL_TIMEOUT', '1800'))  # OCR进度停滞超时(秒)

    OCR_MAX_RETRIES = int(os.environ.get('OCR_MAX_RETRIES', '2'))  # 子进程崩溃后最大重试次数
    OCR_RETRY_BACKOFF = float(os.environ.get('OCR_RETRY_BACKOFF', '5.0'))  # 重试间隔(秒)，每次递增1.5倍
    OCR_DYNAMIC_PARAMS = os.environ.get('OCR_DYNAMIC_PARAMS', 'true').lower() == 'true'  # 根据系统负载动态调整OCR参数

    # LLM OCR配置
    AIPING_OCR_LLM_MODEL = os.environ.get('AIPING_OCR_LLM_MODEL') or 'DeepSeek-OCR-2'
    SILICON_FLOW_OCR_LLM_MODEL = os.environ.get('SILICON_FLOW_OCR_LLM_MODEL') or 'deepseek-ai/DeepSeek-OCR'
    OCR_LLM_MAX_TOKENS = int(os.environ.get('OCR_LLM_MAX_TOKENS', '8192'))
    OCR_LLM_TEMPERATURE = float(os.environ.get('OCR_LLM_TEMPERATURE', '0.1'))
    OCR_LLM_DPI = int(os.environ.get('OCR_LLM_DPI', '150'))  # LLM OCR渲染DPI（比PaddleOCR略低，节省token）

# 创建配置实例
config = Config()
