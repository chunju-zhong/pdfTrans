import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from utils.logging_config import setup_logging
from modules.chapter_identifier import ChapterIdentifier

# 配置日志
setup_logging()

# 创建ChapterIdentifier实例
identifier = ChapterIdentifier()

# 模拟书签数据
sample_bookmarks = [
    [1, "Chapter 1", 0, (0, 100, 0)],  # 带位置信息的书签
    [2, "Section 1.1", 1],  # 不带位置信息的书签
    [1, "Chapter 2", 2, {"to": (0, 150, 0)}],  # 带字典格式位置信息的书签
    [1, "Chapter 3", 3, {"kind": 4, "xref": 378, "page": 2, "dest": "/Fit", "nameddest": "test", "zoom": 0.0}]  # 带 /Fit 类型目标的书签
]

# 构建章节树
chapters = identifier._build_chapter_tree(sample_bookmarks)

print(f"构建完成，共 {len(chapters)} 个根章节")