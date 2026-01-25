from models.task import Task

# 任务管理服务
class TaskService:
    def __init__(self):
        self.tasks = {}  # 存储所有任务
    
    def create_task(self, task_id, filename):
        """创建新任务"""
        task = Task(task_id, filename)
        self.tasks[task_id] = task
        return task
    
    def get_task(self, task_id):
        """根据任务ID获取任务"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self):
        """获取所有任务"""
        return self.tasks.values()
    
    def cancel_task(self, task_id):
        """取消任务"""
        task = self.get_task(task_id)
        if task:
            task.cancel()
            return True
        return False
    
    def update_task_progress(self, task_id, progress, message=None):
        """更新任务进度"""
        task = self.get_task(task_id)
        if task:
            return task.update_progress(progress, message)
        return False
    
    def set_task_result(self, task_id, result_file):
        """设置任务结果"""
        task = self.get_task(task_id)
        if task:
            return task.set_result(result_file)
        return False
    
    def set_task_error(self, task_id, error_message):
        """设置任务错误"""
        task = self.get_task(task_id)
        if task:
            task.set_error(error_message)
            return True
        return False
    
    def get_task_dict(self, task_id):
        """获取任务的字典表示"""
        task = self.get_task(task_id)
        if task:
            return task.to_dict()
        return None

# 创建任务服务实例
task_service = TaskService()
