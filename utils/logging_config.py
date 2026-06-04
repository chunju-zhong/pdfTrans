import logging

class FlushFileHandler(logging.FileHandler):
    """每次写入后自动刷新到磁盘的 FileHandler，确保日志即时可见"""
    def emit(self, record):
        super().emit(record)
        self.flush()

# 配置日志
def setup_logging():
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    file_handler = FlushFileHandler('app.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[file_handler, stream_handler]
    )

# 获取日志记录器
def get_logger(name):
    return logging.getLogger(name)
