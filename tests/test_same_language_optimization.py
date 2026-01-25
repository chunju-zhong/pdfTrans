#!/usr/bin/env python3
"""
测试脚本：验证当源语言和目标语言相同时直接拷贝原始页的优化，包括页码范围功能
"""
import os
import sys
import tempfile
import shutil

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.translation_service import translation_service
from models.task import Task

# 创建一个多页的PDF文件用于测试
def create_multi_page_test_pdf(filepath, page_count=3):
    """创建一个多页的测试PDF文件"""
    import fitz
    doc = fitz.open()
    for i in range(page_count):
        page = doc.new_page()
        page.insert_text((100, 100), f"This is page {i+1} of a test PDF file.", fontsize=12)
    doc.save(filepath)
    doc.close()
    return page_count

# 测试源语言和目标语言相同的情况（不指定页码范围）
def test_same_language_copy_all_pages():
    print("=== 测试：源语言和目标语言相同时直接拷贝所有页面 ===")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试PDF文件
        input_pdf = os.path.join(tmpdir, "test_input.pdf")
        page_count = create_multi_page_test_pdf(input_pdf, page_count=3)
        
        # 创建任务对象
        task = Task(task_id="test_task_001", filename="test_input.pdf")
        
        # 调用翻译服务，源语言和目标语言相同，不指定页码范围
        translation_service.process_translation(
            task=task,
            input_filepath=input_pdf,
            source_lang="en",
            target_lang="en",  # 源语言和目标语言相同
            translator_type="baidu",
            unique_id="test_same_lang_all",
            filename="test_input.pdf",
            page_range=""  # 不指定页码范围
        )
        
        # 检查任务状态
        print(f"任务状态: {task.status}")
        print(f"任务消息: {task.message}")
        
        # 检查输出文件是否存在
        from config import config
        output_filename = f"translated_test_same_lang_all_test_input.pdf"
        output_filepath = os.path.join(config.OUTPUT_FOLDER, output_filename)
        
        if os.path.exists(output_filepath):
            print(f"✓ 输出文件已生成: {output_filepath}")
            print(f"✓ 输出文件大小: {os.path.getsize(output_filepath)} bytes")
            
            # 检查输出文件的页数
            import fitz
            with fitz.open(output_filepath) as doc:
                output_page_count = len(doc)
                print(f"✓ 输出文件页数: {output_page_count}")
                print(f"✓ 原始文件页数: {page_count}")
                if output_page_count == page_count:
                    print(f"✓ 页数正确：输出文件包含所有 {page_count} 页")
                else:
                    print(f"✗ 页数错误：预期 {page_count} 页，实际 {output_page_count} 页")
                    return False
            
            # 清理输出文件
            os.remove(output_filepath)
            print(f"✓ 已清理测试文件")
            return True
        else:
            print(f"✗ 输出文件未生成: {output_filepath}")
            return False

# 测试源语言和目标语言相同的情况（指定单个页码）
def test_same_language_copy_single_page():
    print("\n=== 测试：源语言和目标语言相同时拷贝单个页面 ===")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试PDF文件
        input_pdf = os.path.join(tmpdir, "test_input.pdf")
        page_count = create_multi_page_test_pdf(input_pdf, page_count=3)
        
        # 创建任务对象
        task = Task(task_id="test_task_002", filename="test_input.pdf")
        
        # 调用翻译服务，源语言和目标语言相同，指定单个页码
        translation_service.process_translation(
            task=task,
            input_filepath=input_pdf,
            source_lang="en",
            target_lang="en",  # 源语言和目标语言相同
            translator_type="baidu",
            unique_id="test_same_lang_single",
            filename="test_input.pdf",
            page_range="2"  # 指定单个页码
        )
        
        # 检查任务状态
        print(f"任务状态: {task.status}")
        print(f"任务消息: {task.message}")
        
        # 检查输出文件是否存在
        from config import config
        output_filename = f"translated_test_same_lang_single_test_input.pdf"
        output_filepath = os.path.join(config.OUTPUT_FOLDER, output_filename)
        
        if os.path.exists(output_filepath):
            print(f"✓ 输出文件已生成: {output_filepath}")
            print(f"✓ 输出文件大小: {os.path.getsize(output_filepath)} bytes")
            
            # 检查输出文件的页数
            import fitz
            with fitz.open(output_filepath) as doc:
                output_page_count = len(doc)
                print(f"✓ 输出文件页数: {output_page_count}")
                if output_page_count == 1:
                    print(f"✓ 页数正确：输出文件包含 1 页")
                else:
                    print(f"✗ 页数错误：预期 1 页，实际 {output_page_count} 页")
                    return False
            
            # 清理输出文件
            os.remove(output_filepath)
            print(f"✓ 已清理测试文件")
            return True
        else:
            print(f"✗ 输出文件未生成: {output_filepath}")
            return False

# 测试源语言和目标语言相同的情况（指定页码范围）
def test_same_language_copy_page_range():
    print("\n=== 测试：源语言和目标语言相同时拷贝指定页码范围 ===")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试PDF文件
        input_pdf = os.path.join(tmpdir, "test_input.pdf")
        page_count = create_multi_page_test_pdf(input_pdf, page_count=5)
        
        # 创建任务对象
        task = Task(task_id="test_task_003", filename="test_input.pdf")
        
        # 调用翻译服务，源语言和目标语言相同，指定页码范围
        translation_service.process_translation(
            task=task,
            input_filepath=input_pdf,
            source_lang="en",
            target_lang="en",  # 源语言和目标语言相同
            translator_type="baidu",
            unique_id="test_same_lang_range",
            filename="test_input.pdf",
            page_range="2-4"  # 指定页码范围
        )
        
        # 检查任务状态
        print(f"任务状态: {task.status}")
        print(f"任务消息: {task.message}")
        
        # 检查输出文件是否存在
        from config import config
        output_filename = f"translated_test_same_lang_range_test_input.pdf"
        output_filepath = os.path.join(config.OUTPUT_FOLDER, output_filename)
        
        if os.path.exists(output_filepath):
            print(f"✓ 输出文件已生成: {output_filepath}")
            print(f"✓ 输出文件大小: {os.path.getsize(output_filepath)} bytes")
            
            # 检查输出文件的页数
            import fitz
            with fitz.open(output_filepath) as doc:
                output_page_count = len(doc)
                print(f"✓ 输出文件页数: {output_page_count}")
                if output_page_count == 3:
                    print(f"✓ 页数正确：输出文件包含 3 页（页码范围 2-4）")
                else:
                    print(f"✗ 页数错误：预期 3 页，实际 {output_page_count} 页")
                    return False
            
            # 清理输出文件
            os.remove(output_filepath)
            print(f"✓ 已清理测试文件")
            return True
        else:
            print(f"✗ 输出文件未生成: {output_filepath}")
            return False

# 测试源语言和目标语言相同的情况（指定多个不连续页码）
def test_same_language_copy_discontinuous_pages():
    print("\n=== 测试：源语言和目标语言相同时拷贝多个不连续页码 ===")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试PDF文件
        input_pdf = os.path.join(tmpdir, "test_input.pdf")
        page_count = create_multi_page_test_pdf(input_pdf, page_count=5)
        
        # 创建任务对象
        task = Task(task_id="test_task_004", filename="test_input.pdf")
        
        # 调用翻译服务，源语言和目标语言相同，指定多个不连续页码
        translation_service.process_translation(
            task=task,
            input_filepath=input_pdf,
            source_lang="en",
            target_lang="en",  # 源语言和目标语言相同
            translator_type="baidu",
            unique_id="test_same_lang_discontinuous",
            filename="test_input.pdf",
            page_range="1,3,5"  # 指定多个不连续页码
        )
        
        # 检查任务状态
        print(f"任务状态: {task.status}")
        print(f"任务消息: {task.message}")
        
        # 检查输出文件是否存在
        from config import config
        output_filename = f"translated_test_same_lang_discontinuous_test_input.pdf"
        output_filepath = os.path.join(config.OUTPUT_FOLDER, output_filename)
        
        if os.path.exists(output_filepath):
            print(f"✓ 输出文件已生成: {output_filepath}")
            print(f"✓ 输出文件大小: {os.path.getsize(output_filepath)} bytes")
            
            # 检查输出文件的页数
            import fitz
            with fitz.open(output_filepath) as doc:
                output_page_count = len(doc)
                print(f"✓ 输出文件页数: {output_page_count}")
                if output_page_count == 3:
                    print(f"✓ 页数正确：输出文件包含 3 页（页码 1, 3, 5）")
                else:
                    print(f"✗ 页数错误：预期 3 页，实际 {output_page_count} 页")
                    return False
            
            # 清理输出文件
            os.remove(output_filepath)
            print(f"✓ 已清理测试文件")
            return True
        else:
            print(f"✗ 输出文件未生成: {output_filepath}")
            return False

# 测试源语言和目标语言不同的情况
def test_different_language_translation():
    print("\n=== 测试：源语言和目标语言不同时正常翻译 ===")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试PDF文件
        input_pdf = os.path.join(tmpdir, "test_input.pdf")
        create_multi_page_test_pdf(input_pdf, page_count=2)
        
        # 创建任务对象
        task = Task(task_id="test_task_005", filename="test_input.pdf")
        
        try:
            # 调用翻译服务，源语言和目标语言不同
            translation_service.process_translation(
                task=task,
                input_filepath=input_pdf,
                source_lang="en",
                target_lang="zh",  # 源语言和目标语言不同
                translator_type="baidu",
                unique_id="test_diff_lang",
                filename="test_input.pdf"
            )
            
            print(f"任务状态: {task.status}")
            print(f"任务消息: {task.message}")
            
            # 检查任务是否正常处理
            if task.status in ["completed", "error"]:
                print(f"✓ 任务正常处理完成")
                # 清理输出文件
                from config import config
                output_filename = f"translated_test_diff_lang_test_input.pdf"
                output_filepath = os.path.join(config.OUTPUT_FOLDER, output_filename)
                if os.path.exists(output_filepath):
                    os.remove(output_filepath)
                return True
            else:
                print(f"✗ 任务未正常处理")
                return False
        except Exception as e:
            print(f"✗ 任务处理出错: {e}")
            return False

if __name__ == "__main__":
    # 运行测试
    test1_passed = test_same_language_copy_all_pages()
    test2_passed = test_same_language_copy_single_page()
    test3_passed = test_same_language_copy_page_range()
    test4_passed = test_same_language_copy_discontinuous_pages()
    test5_passed = test_different_language_translation()
    
    print("\n=== 测试结果 ===")
    all_tests = [test1_passed, test2_passed, test3_passed, test4_passed, test5_passed]
    passed_tests = sum(all_tests)
    total_tests = len(all_tests)
    
    print(f"通过测试: {passed_tests}/{total_tests}")
    if passed_tests == total_tests:
        print("✓ 所有测试通过！")
        sys.exit(0)
    else:
        print("✗ 测试失败！")
        sys.exit(1)