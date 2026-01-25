## 字体选择流程优化方案

### 1. 问题分析
当前字体选择流程存在以下问题：
- 无法从系统动态获取可用字体列表
- 字体选择范围有限，只尝试了少数预定义字体
- 没有充分利用系统中已安装的字体资源
- 对中文等非西文语言的支持不够完善

### 2. 优化目标
- 实现从系统动态获取目标语言可用字体列表
- 优先从系统可用字体中选择支持目标语言的字体
- 合理处理PyMuPDF默认字体的回退机制
- 确保字体选择流程的跨平台兼容性

### 3. 具体实现方案

#### 3.1 添加系统字体获取功能
```python
def _get_system_fonts(self):
    """从系统中获取可用字体列表
    
    Returns:
        list: 系统可用字体名称列表
    """
    # 使用PIL的ImageFont获取系统字体
    # 这是一个跨平台的实现方式
    system_fonts = []
    try:
        # 尝试获取系统字体目录
        if sys.platform == 'win32':
            # Windows系统字体目录
            font_dirs = [r'C:\Windows\Fonts']
        elif sys.platform == 'darwin':
            # macOS系统字体目录
            font_dirs = [
                '/System/Library/Fonts',
                '/Library/Fonts',
                os.path.expanduser('~/Library/Fonts')
            ]
        else:
            # Linux系统字体目录
            font_dirs = [
                '/usr/share/fonts',
                '/usr/local/share/fonts',
                os.path.expanduser('~/.fonts')
            ]
        
        # 遍历字体目录，获取字体文件
        for font_dir in font_dirs:
            if os.path.exists(font_dir):
                for root, _, files in os.walk(font_dir):
                    for file in files:
                        if file.endswith(('.ttf', '.otf', '.ttc')):
                            # 获取字体名称（不含扩展名）
                            font_name = os.path.splitext(file)[0]
                            system_fonts.append(font_name)
        
        # 去重
        system_fonts = list(set(system_fonts))
        logger.info(f"从系统获取到 {len(system_fonts)} 种可用字体")
    except Exception as e:
        logger.warning(f"获取系统字体列表失败: {e}")
        system_fonts = []
    
    return system_fonts
```

#### 3.2 修改字体选择核心逻辑
```python
def _get_suitable_font(self, page, original_font, target_lang):
    """获取适合目标语言的字体
    
    Args:
        page (fitz.Page): PDF页面对象
        original_font (str): 原始字体名称
        target_lang (str): 目标语言代码
        
    Returns:
        str: 适合的字体名称
    """
    logger.info(f"获取适合字体: 原字体='{original_font}', 目标语言='{target_lang}'")
    
    # 尝试使用原始字体
    if original_font:
        try:
            logger.debug(f"尝试使用原始字体 '{original_font}'")
            page.insert_font(fontname=original_font, fontfile=None)
            logger.info(f"成功使用原始字体 '{original_font}'")
            return original_font
        except Exception as e:
            logger.debug(f"原始字体 '{original_font}' 插入失败: {e}")
    
    # 1. 从系统获取可用字体列表
    system_fonts = self._get_system_fonts()
    
    # 2. 从系统字体中选择支持目标语言的字体
    if system_fonts:
        logger.info(f"开始从系统字体中选择支持 '{target_lang}' 的字体")
        for font_name in system_fonts:
            try:
                # 检查字体是否支持目标语言
                if self._check_font_support(font_name, target_lang):
                    logger.debug(f"尝试使用系统字体 '{font_name}'")
                    page.insert_font(fontname=font_name, fontfile=None)
                    logger.info(f"成功使用系统字体 '{font_name}'")
                    return font_name
            except Exception as e:
                logger.debug(f"系统字体 '{font_name}' 插入失败: {e}")
    
    # 3. 系统字体选择失败，检查PyMuPDF默认字体'helv'是否支持目标语言
    logger.info(f"系统字体选择失败，检查PyMuPDF默认字体'helv'是否支持 '{target_lang}'")
    if self._check_font_support('helv', target_lang):
        try:
            logger.debug("尝试使用PyMuPDF默认字体 'helv'")
            page.insert_font(fontname='helv', fontfile=None)
            logger.info("成功使用PyMuPDF默认字体 'helv'")
            return "helv"
        except Exception as e:
            logger.debug(f"PyMuPDF默认字体 'helv' 插入失败: {e}")
    
    # 4. 所有尝试失败，提示用户安装字体
    error_msg = f"无法找到适合目标语言 '{target_lang}' 的字体，请安装相应的系统字体"
    logger.error(error_msg)
    raise Exception(error_msg)
```

#### 3.3 优化字体支持检查方法
```python
def _check_font_support(self, font_name, target_lang):
    """检查字体是否支持目标语言
    
    Args:
        font_name (str): 字体名称
        target_lang (str): 目标语言代码
        
    Returns:
        bool: 字体是否支持目标语言
    """
    try:
        # 尝试加载字体
        font = ImageFont.truetype(font_name, 12)
        
        # 测试字符
        test_chars = {
            'zh': '你好世界',
            'en': 'Hello World',
            'ja': 'こんにちは世界',
            'ko': '안녕하세요 세계'
        }
        
        # 获取目标语言的测试字符
        test_char = test_chars.get(target_lang, test_chars['en'])
        
        # 尝试绘制测试字符
        font.getbbox(test_char)
        return True
    except Exception as e:
        logger.debug(f"字体 '{font_name}' 不支持目标语言 '{target_lang}': {e}")
        return False
```

### 4. 优化后的字体选择流程
1. **尝试原始字体**：首先尝试使用原始PDF中的字体
2. **系统字体选择**：
   - 从系统动态获取可用字体列表
   - 遍历系统字体，检查是否支持目标语言
   - 选择第一个支持目标语言且能被PyMuPDF使用的字体
3. **默认字体回退**：
   - 检查PyMuPDF默认字体'helv'是否支持目标语言
   - 如果支持，使用'helv'
4. **提示安装**：如果所有尝试失败，提示用户安装适合目标语言的字体

### 5. 预期效果
- 能够充分利用系统中已安装的字体资源
- 优先选择支持目标语言的系统字体
- 只有当系统字体都不支持时，才使用PyMuPDF默认字体
- 提供清晰的错误提示，指导用户安装适合的字体
- 提高中文等非西文语言的显示效果

### 6. 注意事项
- 跨平台兼容性：确保系统字体获取方法在不同操作系统上都能正常工作
- 性能考虑：系统字体列表可能很大，需要优化遍历和检查逻辑
- 错误处理：妥善处理字体加载失败等异常情况
- 日志记录：添加详细的日志，便于调试和监控字体选择流程

通过以上优化，PDF翻译工具的字体选择流程将更加智能和灵活，能够更好地适应不同语言和系统环境，提供更好的翻译PDF生成效果。