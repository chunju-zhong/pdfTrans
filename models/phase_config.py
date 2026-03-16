PHASE_CONFIG = {
    'init': {
        'name': '初始化',
        'start': 0,
        'end': 10,
    },
    'extraction': {
        'name': '文本图表提取',
        'start': 10,
        'end': 35,
    },
    'semantic_merge': {
        'name': '语义合并',
        'start': 35,
        'end': 40,
    },
    'translation': {
        'name': '文本翻译',
        'start': 40,
        'end': 80,
    },
    'table_translation': {
        'name': '表格翻译',
        'start': 80,
        'end': 90,
    },
    'generation': {
        'name': '生成输出',
        'start': 90,
        'end': 95,
    },
    'clean': {
        'name': '清理临时文件',
        'start': 95,
        'end': 100,
    }
}

GLOSSARY_PHASE_CONFIG = {
    'init': {
        'name': '开始提取',
        'start': 0,
        'end': 5,
    },
    'pdf_extraction': {
        'name': '文本提取',
        'start': 5,
        'end': 30,
    },
    'term_extraction': {
        'name': '术语提取',
        'start': 30,
        'end': 100,
    }
}


def validate_phase_config(config):
    """验证阶段配置的有效性
    
    Args:
        config: 阶段配置字典
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not config:
        return False, "配置不能为空"
    
    for phase_id, phase_info in config.items():
        if 'start' not in phase_info or 'end' not in phase_info:
            return False, f"阶段 {phase_id} 缺少 start 或 end 配置"
        
        start = phase_info['start']
        end = phase_info['end']
        
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            return False, f"阶段 {phase_id} 的 start/end 必须是数字"
        
        if start < 0 or end > 100:
            return False, f"阶段 {phase_id} 的范围必须在 0-100 之间"
        
        if start >= end:
            return False, f"阶段 {phase_id} 的 start 必须小于 end"
    
    return True, None


def get_phase_info(config, phase_id):
    """获取指定阶段的信息
    
    Args:
        config: 阶段配置字典
        phase_id: 阶段ID
        
    Returns:
        dict or None: 阶段信息，如果不存在则返回 None
    """
    return config.get(phase_id)


def calculate_progress(config, phase_id, phase_percent):
    """根据阶段配置计算整体进度
    
    Args:
        config: 阶段配置字典
        phase_id: 阶段ID
        phase_percent: 阶段内进度 (0-100)
        
    Returns:
        int: 整体进度值
    """
    phase_info = config.get(phase_id)
    if not phase_info:
        return 0
    
    start = phase_info['start']
    end = phase_info['end']
    
    return start + (end - start) * phase_percent // 100
