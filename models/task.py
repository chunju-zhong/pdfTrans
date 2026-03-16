import threading
import time

from models.copyable import CopyableMixin
from models.phase_config import PHASE_CONFIG, GLOSSARY_PHASE_CONFIG

# 任务状态枚举
TASK_STATUS = {
    'PENDING': 'pending',
    'PROCESSING': 'processing',
    'COMPLETED': 'completed',
    'ERROR': 'error'
}

# 任务数据类
class Task(CopyableMixin):
    def __init__(self, task_id, filename):
        self.task_id = task_id
        self.filename = filename
        self.status = TASK_STATUS['PENDING']
        self.progress = 0
        self.message = '准备开始...'
        self.result_file = None
        self.attachments = []
        self.error = None
        self.canceled = False
        self.warnings = []
        self.glossary = ''
        self.start_time = time.time()
        self.end_time = None
        self.lock = threading.RLock()
        self.task_type = 'translation'
        self.phase_config = PHASE_CONFIG
        self.current_phase = 'init'
    
    def update_progress(self, progress, message=None):
        with self.lock:
            if self.canceled:
                return False
            self.progress = max(0, min(100, progress))
            if message:
                self.message = message
            return True
    
    def set_task_type(self, task_type):
        with self.lock:
            self.task_type = task_type
            if task_type == 'glossary':
                self.phase_config = GLOSSARY_PHASE_CONFIG
            else:
                self.phase_config = PHASE_CONFIG
    
    def update_phase_progress(self, phase, phase_percent, message=None):
        with self.lock:
            if self.canceled:
                return False
            phase_info = self.phase_config.get(phase)
            if not phase_info:
                return False
            start = phase_info['start']
            end = phase_info['end']
            overall_progress = start + (end - start) * phase_percent // 100
            self.progress = max(0, min(100, overall_progress))
            if message:
                self.message = message
            self.current_phase = phase
            return True
    
    def set_status(self, status):
        with self.lock:
            self.status = status
    
    def set_result(self, result_file):
        with self.lock:
            if self.canceled:
                return False
            self.result_file = result_file
            self.status = TASK_STATUS['COMPLETED']
            self.progress = 100
            self.message = '翻译完成！'
            self.set_end_time()
            return True
    
    def set_error(self, error_message):
        with self.lock:
            self.error = error_message
            self.status = TASK_STATUS['ERROR']
            self.progress = 0
            self.message = error_message
            self.set_end_time()
    
    def is_canceled(self):
        with self.lock:
            return self.canceled
    
    def cancel(self):
        with self.lock:
            self.canceled = True
            self.status = TASK_STATUS['ERROR']
            self.message = '翻译已取消'
            self.error = '用户取消了翻译任务'
            self.set_end_time()
    
    def add_attachment(self, attachment_file):
        with self.lock:
            self.attachments.append(attachment_file)
    
    def add_warning(self, message, context=None):
        with self.lock:
            warning = {
                'message': message,
                'context': context or {}
            }
            self.warnings.append(warning)
    
    def get_warnings(self):
        with self.lock:
            return self.warnings.copy()
    
    def get_total_time(self):
        with self.lock:
            if self.end_time:
                return self.end_time - self.start_time
            else:
                return time.time() - self.start_time
    
    def set_end_time(self):
        with self.lock:
            if not self.end_time:
                self.end_time = time.time()
    
    def to_dict(self):
        with self.lock:
            return {
                'task_id': self.task_id,
                'filename': self.filename,
                'status': self.status,
                'progress': self.progress,
                'message': self.message,
                'result_file': self.result_file,
                'attachments': self.attachments,
                'error': self.error,
                'canceled': self.canceled,
                'warnings': self.warnings,
                'glossary': self.glossary,
                'total_time': self.get_total_time()
            }
