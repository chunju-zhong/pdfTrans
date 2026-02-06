import os

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    """检查文件是否允许上传"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_directory_exists(directory):
    """确保目录存在，如果不存在则创建"""
    os.makedirs(directory, exist_ok=True)

def remove_file(filepath):
    """删除文件，如果文件不存在则忽略"""
    if os.path.exists(filepath):
        os.remove(filepath)

def create_zip(zip_path, files, directories=None):
    """创建zip文件，包含指定的文件和目录
    
    Args:
        zip_path (str): zip文件路径
        files (list): 文件路径列表
        directories (list): 目录路径列表
    """
    import zipfile
    import os
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 添加文件
        for file_path in files:
            if os.path.exists(file_path):
                # 计算相对路径，确保文件在zip根目录
                arcname = os.path.basename(file_path)
                zipf.write(file_path, arcname)
        
        # 添加目录
        if directories:
            for directory in directories:
                if os.path.exists(directory):
                    # 遍历目录中的所有文件
                    for root, _, dir_files in os.walk(directory):
                        for file in dir_files:
                            file_path = os.path.join(root, file)
                            # 计算相对路径，保持目录结构
                            arcname = os.path.relpath(file_path, os.path.dirname(directory))
                            zipf.write(file_path, arcname)
