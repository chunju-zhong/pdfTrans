"""
翻译命令处理模块

处理 translate 子命令的逻辑
"""

import os
import sys
import uuid

from cli.progress_display import ProgressDisplay, TaskProgressCallback
from config import config
from services.task_service import Task, task_service
from services.translation_service import translation_service
from utils.file_utils import allowed_file

def get_output_path_with_correct_suffix(output_path, output_format):
    """
    根据输出格式智能处理文件后缀
    
    Args:
        output_path: 用户指定的输出路径
        output_format: 输出格式 (pdf, docx, markdown)
        
    Returns:
        str: 处理后的输出路径
    """
    # 获取文件扩展名
    _, ext = os.path.splitext(output_path)
    ext = ext.lower()
    
    # 根据格式确定需要的后缀
    if output_format == 'pdf':
        expected_ext = '.pdf'
    elif output_format == 'docx':
        expected_ext = '.docx'
    elif output_format == 'markdown':
        expected_ext = '.zip'  # Markdown生成的是zip文件
    else:
        return output_path
    
    # 如果已经有正确的后缀，直接返回
    if ext == expected_ext:
        return output_path
    
    # 否则添加正确的后缀
    return f"{output_path}{expected_ext}"


def translate_handler(args):
    """
    处理 translate 命令
    
    Args:
        args: 命令行参数
    """
    # 验证输入文件
    input_path = args.input
    if not os.path.exists(input_path):
        print(f"错误: 输入文件不存在: {input_path}")
        sys.exit(1)
    
    if not allowed_file(input_path):
        print(f"错误: 不支持的文件类型，仅支持PDF文件")
        sys.exit(1)
    
    # 检查章节拆分和输出格式的兼容性
    if args.chapter_split and args.format != 'markdown':
        print("警告: --chapter-split 只在选择Markdown输出格式时起作用")
    
    # 读取术语表
    glossary = ""
    if args.glossary:
        if not os.path.exists(args.glossary):
            print(f"错误: 术语表文件不存在: {args.glossary}")
            sys.exit(1)
        try:
            with open(args.glossary, 'r', encoding='utf-8') as f:
                glossary = f.read()
        except Exception as e:
            print(f"错误: 无法读取术语表文件: {e}")
            sys.exit(1)
    
    # 创建进度显示器
    progress = ProgressDisplay(verbose=args.verbose)
    
    # 生成唯一ID
    unique_id = str(uuid.uuid4())[:8]
    
    # 确定输出文件名
    if args.output:
        # 智能处理文件后缀
        output_path = get_output_path_with_correct_suffix(args.output, args.format)
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        # 创建 tmp 子目录用于存放临时文件
        tmp_dir = os.path.join(output_dir, 'tmp')
        os.makedirs(tmp_dir, exist_ok=True)
    else:
        # 自动生成输出文件名
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        if args.format == 'pdf':
            output_filename = f"translated_{base_name}.pdf"
        elif args.format == 'docx':
            output_filename = f"translated_{base_name}.docx"
        else:  # markdown
            output_filename = f"translated_{base_name}.zip"  # Markdown生成的是zip文件
        output_path = os.path.join(config.OUTPUT_FOLDER, output_filename)
        # 确保输出目录存在
        os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)
        # 创建 tmp 子目录用于存放临时文件
        tmp_dir = os.path.join(config.OUTPUT_FOLDER, 'tmp')
        os.makedirs(tmp_dir, exist_ok=True)
    
    # 创建任务ID
    task_id = str(uuid.uuid4())
    
    # 创建任务对象
    task = task_service.create_task(task_id, os.path.basename(input_path))
    task.update_phase_progress('init', 100, '文件检查完成...')
    
    progress.log(f"开始翻译: {input_path}")
    progress.log(f"源语言: {args.source} -> 目标语言: {args.target}")
    progress.log(f"翻译服务: {args.translator}")
    progress.log(f"输出格式: {args.format}")
    if args.pages:
        progress.log(f"页码范围: {args.pages}")
    if glossary:
        progress.log(f"已加载术语表")
    if args.semantic_merge:
        progress.log("启用语义合并")
    if args.llm_merge:
        progress.log("使用LLM合并")
    if args.chapter_split:
        progress.log("按章节拆分输出")
    
    try:
        # 执行同步翻译
        result = translation_service.process_translation_sync(
            task=task,
            input_filepath=input_path,
            source_lang=args.source,
            target_lang=args.target,
            translator_type=args.translator,
            unique_id=unique_id,
            filename=os.path.basename(input_path),
            doc_type=args.doc_type,
            glossary=glossary,
            page_range=args.pages or "",
            output_format=args.format,
            semantic_merge=args.semantic_merge,
            use_llm_merging=args.llm_merge,
            chapter_split=args.chapter_split,
            progress_callback=TaskProgressCallback(progress),
            is_cli=True,
            output_path=os.path.dirname(output_path) if args.output else None,
            output_filename=os.path.basename(output_path) if args.output else None,
            tmp_dir=tmp_dir
        )
        
        if result:
            # 直接使用用户指定的输出路径或默认路径
            final_output_path = output_path if args.output else os.path.join(config.OUTPUT_FOLDER, result)
            progress.success(f"翻译完成！")
            progress.log(f"输出文件: {final_output_path}")
            
            # 显示警告信息
            if task.warnings:
                progress.warning(f"翻译过程中有 {len(task.warnings)} 个警告:")
                for warning in task.warnings:
                    progress.warning(f"  - {warning['message']}")
        else:
            progress.error("翻译失败")
            sys.exit(1)
            
    except KeyboardInterrupt:
        progress.log("\n正在取消翻译...")
        task_service.cancel_task(task_id)
        progress.error("翻译已取消")
        sys.exit(130)
    except Exception as e:
        progress.error(f"翻译失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
