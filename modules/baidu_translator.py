import requests
import hashlib
import random
from .translator import Translator

class BaiduTranslator(Translator):
    """百度翻译API实现
    
    继承自Translator基类，实现百度翻译API的调用逻辑。
    """
    
    def __init__(self, app_id, app_key):
        """初始化百度翻译器
        
        Args:
            app_id (str): 百度翻译API的App ID
            app_key (str): 百度翻译API的App Key
        """
        super().__init__(app_key)
        self.app_id = app_id
        self.api_url = "https://fanyi-api.baidu.com/api/trans/vip/translate"
        
        # 百度翻译API支持的语言代码映射
        self.language_map = {
            'zh': 'zh',
            'en': 'en',
            'ja': 'jp',
            'ko': 'kor',
            'fr': 'fra',
            'de': 'de',
            'es': 'spa',
            'ru': 'ru'
        }
    
    def translate(self, text, source_lang, target_lang, doc_type="技术文档", glossary=""):
        """使用百度翻译API翻译文本
        
        Args:
            text (str): 要翻译的文本
            source_lang (str): 源语言代码
            target_lang (str): 目标语言代码
            doc_type (str): 文档类型
            glossary (str): 术语表
            
        Returns:
            str: 翻译后的文本
        """
        # 检查原语言与目标语言是否一致
        if source_lang == target_lang:
            # 语言一致，直接返回原文本
            return text
        
        # 验证语言代码
        if not self._validate_language(source_lang) or not self._validate_language(target_lang):
            raise ValueError(f"不支持的语言代码: {source_lang} 或 {target_lang}")
        
        # 构建优化的系统提示词
        lang_map = {
            'zh': '中文',
            'en': '英文',
            'ja': '日文',
            'ko': '韩文',
            'fr': '法文',
            'de': '德文',
            'es': '西班牙文',
            'ru': '俄文'
        }
        
        source_lang_name = lang_map.get(source_lang, source_lang)
        target_lang_name = lang_map.get(target_lang, target_lang)
        
        # 构建针对技术文档英翻中的专属提示词
        prompt = f"""
你是专业的{doc_type}翻译专家，擅长将{source_lang_name}文档精准翻译成{target_lang_name}，严格遵循以下规则：
1. 语义连贯：必须基于完整上下文理解，禁止逐词直译导致的句子断裂；
2. 术语一致：严格使用以下术语表翻译，不随意变更：
{glossary if glossary else '无'}
3. 句式严谨：保持技术文档的正式语气，保留被动语态和逻辑连接词；
4. 不增删义：严格遵循原文含义，不添加额外解释，不遗漏任何细节（包括标点、括号、冒号的位置）；
5. 格式兼容：翻译结果需便于后续按原文本块拆分，不擅自添加换行、分段（保持段落级完整性）；
6. 技术精准：对于{doc_type}术语、代码片段、公式等，保持高度准确性，避免误译。

请将以下{source_lang_name}的{doc_type}文本翻译成{target_lang_name}，严格遵守上述所有规则：

{text}
        """
        
        # 记录完整的提示词
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"百度翻译API请求提示词: {prompt.strip()}")
        
        # 文本预处理
        processed_text = self._preprocess_text(prompt.strip())
        
        # 转换为百度翻译API支持的语言代码
        baidu_source_lang = self.language_map[source_lang]
        baidu_target_lang = self.language_map[target_lang]
        
        # 生成签名
        salt = str(random.randint(32768, 65536))
        sign = self._generate_sign(processed_text, salt)
        
        # 构建请求参数
        params = {
            'q': processed_text,
            'from': baidu_source_lang,
            'to': baidu_target_lang,
            'appid': self.app_id,
            'salt': salt,
            'sign': sign
        }
        
        try:
            # 发送请求
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            
            if 'trans_result' in result:
                translated_text = ''
                for item in result['trans_result']:
                    translated_text += item['dst'] + ' '
                
                # 文本后处理
                return self._postprocess_text(translated_text.strip(), text)
            else:
                raise Exception(f"百度翻译API返回错误: {result.get('error_msg', '未知错误')}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"百度翻译API请求失败: {str(e)}")
        except Exception as e:
            raise Exception(f"百度翻译失败: {str(e)}")
    
    def _generate_sign(self, text, salt):
        """生成百度翻译API的签名
        
        Args:
            text (str): 要翻译的文本
            salt (str): 随机数
            
        Returns:
            str: 生成的签名
        """
        # 签名生成规则：appid + q + salt + appkey 的MD5值
        sign_str = f"{self.app_id}{text}{salt}{self.api_key}"
        md5 = hashlib.md5()
        md5.update(sign_str.encode('utf-8'))
        return md5.hexdigest()
