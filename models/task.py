import threading

# 任务状态枚举
TASK_STATUS = {
    'PENDING': 'pending',
    'PROCESSING': 'processing',
    'COMPLETED': 'completed',
    'ERROR': 'error'
}

# 任务数据类
class Task:
    def __init__(self, task_id, filename):
        self.task_id = task_id
        self.filename = filename
        self.status = TASK_STATUS['PENDING']
        self.progress = 0
        self.message = '准备开始...'
        self.result_file = None
        self.error = None
        self.canceled = False
        self.lock = threading.Lock()
    
    def update_progress(self, progress, message=None):
        with self.lock:
            if self.canceled:
                return False
            self.progress = max(0, min(100, progress))
            if message:
                self.message = message
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
            return True
    
    def set_error(self, error_message):
        with self.lock:
            self.error = error_message
            self.status = TASK_STATUS['ERROR']
            self.progress = 0
            self.message = error_message
    
    def is_canceled(self):
        with self.lock:
            return self.canceled
    
    def cancel(self):
        with self.lock:
            self.canceled = True
            self.status = TASK_STATUS['ERROR']
            self.message = '翻译已取消'
            self.error = '用户取消了翻译任务'
    
    def to_dict(self):
        with self.lock:
            return {
                'task_id': self.task_id,
                'filename': self.filename,
                'status': self.status,
                'progress': self.progress,
                'message': self.message,
                'result_file': self.result_file,
                'error': self.error,
                'canceled': self.canceled
            }
