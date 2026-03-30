"""
进度显示组件

提供命令行环境下的进度显示功能
"""

import sys
import time
from typing import Optional


class ProgressDisplay:
    """进度显示类"""
    
    def __init__(self, verbose: bool = False):
        """
        初始化进度显示器
        
        Args:
            verbose: 是否显示详细输出
        """
        self.verbose = verbose
        self.current_progress = 0
        self.current_message = ""
        self.start_time = time.time()
    
    def update(self, progress: int, message: str = ""):
        """
        更新进度
        
        Args:
            progress: 进度百分比 (0-100)
            message: 进度消息
        """
        self.current_progress = max(0, min(100, progress))
        self.current_message = message
        
        if self.verbose:
            self._display_progress()
    
    def _display_progress(self):
        """显示进度条"""
        bar_length = 40
        filled = int(bar_length * self.current_progress / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        elapsed = time.time() - self.start_time
        elapsed_str = self._format_time(elapsed)
        
        # 构建输出字符串
        output = f"\r[{bar}] {self.current_progress:3d}% | {elapsed_str}"
        if self.current_message:
            output += f" | {self.current_message}"
        
        # 清除行并输出
        sys.stdout.write('\r' + ' ' * 80 + '\r')
        sys.stdout.write(output[:80])
        sys.stdout.flush()
        
        if self.current_progress >= 100:
            sys.stdout.write('\n')
            sys.stdout.flush()
    
    def _format_time(self, seconds: float) -> str:
        """格式化时间"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m{secs:02d}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h{minutes:02d}m"
    
    def log(self, message: str):
        """
        输出日志消息
        
        Args:
            message: 日志消息
        """
        if self.verbose:
            # 清除当前行
            sys.stdout.write('\r' + ' ' * 80 + '\r')
            print(message)
            # 重新显示进度
            if self.current_progress < 100:
                self._display_progress()
    
    def success(self, message: str):
        """
        输出成功消息
        
        Args:
            message: 成功消息
        """
        if self.current_progress < 100:
            sys.stdout.write('\n')
        print(f"✓ {message}")
    
    def error(self, message: str):
        """
        输出错误消息
        
        Args:
            message: 错误消息
        """
        if self.current_progress < 100:
            sys.stdout.write('\n')
        print(f"✗ {message}", file=sys.stderr)
    
    def warning(self, message: str):
        """
        输出警告消息
        
        Args:
            message: 警告消息
        """
        if self.verbose:
            if self.current_progress < 100:
                sys.stdout.write('\n')
            print(f"⚠ {message}")


class TaskProgressCallback:
    """任务进度回调类，用于与Task对象集成"""
    
    def __init__(self, progress_display: ProgressDisplay):
        """
        初始化回调
        
        Args:
            progress_display: 进度显示器实例
        """
        self.progress_display = progress_display
    
    def __call__(self, progress: int, message: str = ""):
        """
        回调函数
        
        Args:
            progress: 进度百分比
            message: 进度消息
        """
        self.progress_display.update(progress, message)
