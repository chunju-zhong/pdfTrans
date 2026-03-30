"""
语言列表命令处理模块

处理 list-languages 子命令的逻辑
"""

from config import config


def list_languages_handler(args):
    """
    处理 list-languages 命令
    
    Args:
        args: 命令行参数
    """
    print("支持的语言:")
    print()
    
    # 获取支持的语言列表
    languages = config.SUPPORTED_LANGUAGES
    
    # 计算最大键长度用于对齐
    max_key_len = max(len(key) for key in languages.keys())
    
    # 打印语言列表
    for code, name in languages.items():
        print(f"  {code:<{max_key_len}}  - {name}")
    
    print()
    print("使用示例:")
    print(f'  pdftrans translate doc.pdf -s en -t zh')
