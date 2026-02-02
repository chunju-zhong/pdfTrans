import logging

logger = logging.getLogger(__name__)

def process_page_numbers(pages, total_pages):
    """处理页码参数
    
    Args:
        pages (list[int] | None): 页码列表（1-based）
        total_pages (int): 总页数
        
    Returns:
        tuple:
            list[int]: 有效的1-based页码列表
            list[int]: 有效的0-based页码列表
    """
    if pages is None:
        # 处理所有页面
        one_based_pages = list(range(1, total_pages + 1))
        zero_based_pages = list(range(total_pages))
        logger.info(f"提取所有页面: {one_based_pages}")
        return one_based_pages, zero_based_pages
    
    # 去重并排序
    unique_pages = sorted(set(pages))
    
    # 验证页码范围
    valid_one_based_pages = []
    valid_zero_based_pages = []
    
    for page in unique_pages:
        if 1 <= page <= total_pages:
            valid_one_based_pages.append(page)
            valid_zero_based_pages.append(page - 1)  # 转换为0-based
        else:
            logger.warning(f"页码{page}超出范围（总页数: {total_pages}），将被忽略")
    
    logger.info(f"指定提取的页码: {valid_one_based_pages}")
    return valid_one_based_pages, valid_zero_based_pages

def validate_page_number(page_num, total_pages):
    """验证页码是否有效
    
    Args:
        page_num (int): 页码（1-based）
        total_pages (int): 总页数
        
    Returns:
        bool: 是否有效
    """
    return 1 <= page_num <= total_pages

def convert_to_zero_based(page_num):
    """将1-based页码转换为0-based
    
    Args:
        page_num (int): 1-based页码
        
    Returns:
        int: 0-based页码
    """
    return page_num - 1

def convert_to_one_based(page_num):
    """将0-based页码转换为1-based
    
    Args:
        page_num (int): 0-based页码
        
    Returns:
        int: 1-based页码
    """
    return page_num + 1

def get_pages_for_processing(pages, total_pages):
    """获取要处理的页码
    
    Args:
        pages (list[int] | None): 页码列表（1-based）
        total_pages (int): 总页数
        
    Returns:
        list[int]: 要处理的1-based页码列表
    """
    one_based_pages, _ = process_page_numbers(pages, total_pages)
    return one_based_pages

def create_pages_param(pages):
    """创建页码参数字符串
    
    Args:
        pages (list[int]): 1-based页码列表
        
    Returns:
        str: 逗号分隔的页码字符串
    """
    if not pages:
        return ""
    return ','.join(map(str, pages))

def get_page_range_description(pages, total_pages):
    """获取页码范围描述
    
    Args:
        pages (list[int] | None): 页码列表（1-based）
        total_pages (int): 总页数
        
    Returns:
        str: 页码范围描述
    """
    if pages is None:
        return f"所有页面 (1-{total_pages})"
    
    valid_pages, _ = process_page_numbers(pages, total_pages)
    if not valid_pages:
        return "无有效页码"
    
    return f"页码: {valid_pages}"
