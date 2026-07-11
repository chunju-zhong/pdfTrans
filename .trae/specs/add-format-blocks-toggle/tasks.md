# Tasks

- [x] Task 1: 在 config.py 中添加 ENABLE_FORMAT_BLOCKS 配置项
  - [x] SubTask 1.1: 添加 `self.ENABLE_FORMAT_BLOCKS = os.environ.get('ENABLE_FORMAT_BLOCKS', 'false')` 配置（默认关闭）
  - [x] SubTask 1.2: 在 `.env.example` 中添加配置说明

- [x] Task 2: 将 output_format 参数传递到 _translate_content 方法
  - [x] SubTask 2.1: 修改 `translation_content.py` 中 `_translate_content` 方法签名，添加 `output_format` 参数
  - [x] SubTask 2.2: 修改调用 `_translate_content` 的上层方法，传递 `output_format`（translation_service.py 三处）

- [x] Task 3: 在 format_blocks 调用前添加条件判断
  - [x] SubTask 3.1: 根据 `config.ENABLE_FORMAT_BLOCKS` 和 `output_format` 判断是否执行 format_blocks
  - [x] SubTask 3.2: 跳过时记录 INFO 日志

# Task Dependencies

- Task 3 依赖 Task 1 和 Task 2
