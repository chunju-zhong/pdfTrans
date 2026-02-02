## 问题分析

test_translate_api测试失败是因为测试代码需要文件`test_data_en.pdf`，但该文件不存在。测试数据目录中有另一个文件`test_data_en_text.pdf`可以使用。

## 解决方案

修改test_progress.py中的test_translate_api测试，将测试数据文件路径从`test_data_en.pdf`改为`test_data_en_text.pdf`。

## 具体修改

1. 打开`tests/test_progress.py`文件
2. 找到第111行的文件路径：`test_file_path = os.path.join(os.path.dirname(__file__), 'data', 'test_data_en.pdf')`
3. 将`test_data_en.pdf`改为`test_data_en_text.pdf`

## 预期效果

修改后，test_translate_api测试将使用现有的测试数据文件，能够正常运行通过测试。