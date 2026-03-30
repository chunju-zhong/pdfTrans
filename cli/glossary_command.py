"""
术语提取命令处理模块

处理 glossary 子命令的逻辑
"""

import os
import sys
import uuid

from cli.progress_display import ProgressDisplay, TaskProgressCallback
from config import config
from services.task_service import Task, task_service
from services.glossary_service import glossary_service
from utils.file_utils import allowed_file


def glossary_handler(args):
    """
    处理 glossary 命令
    
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
    
    # 创建进度显示器
    progress = ProgressDisplay(verbose=args.verbose)
    
    # 确定输出文件名
    if args.output:
        output_path = args.output
    else:
        # 自动生成输出文件名
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = f"glossary_{base_name}.txt"
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # 创建 tmp 子目录用于存放临时文件
    if output_dir:
        tmp_dir = os.path.join(output_dir, 'tmp')
    else:
        tmp_dir = os.path.join(os.getcwd(), 'tmp')
    os.makedirs(tmp_dir, exist_ok=True)
    
    # 创建任务ID
    task_id = str(uuid.uuid4())
    
    # 创建任务对象
    task = task_service.create_task(task_id, os.path.basename(input_path))
    task.set_task_type('glossary')
    task.update_phase_progress('init', 100, '文件检查完成...')
    
    progress.log(f"开始提取术语: {input_path}")
    progress.log(f"源语言: {args.source} -> 目标语言: {args.target}")
    progress.log(f"翻译服务: {args.translator}")
    if args.pages:
        progress.log(f"页码范围: {args.pages}")
    
    try:
        # 解析页码范围
        pages = None
        if args.pages:
            try:
                page_list = []
                ranges = args.pages.split(',')
                for r in ranges:
                    r = r.strip()
                    if '-' in r:
                        start, end = r.split('-')
                        page_list.extend(range(int(start), int(end) + 1))
                    else:
                        page_list.append(int(r))
                pages = sorted(list(set(page_list)))
                progress.log(f"解析页码范围: {args.pages} -> {pages}")
            except Exception as e:
                progress.warning(f"解析页码范围失败: {e}，将提取所有页面")
                pages = None
        
        # 执行同步术语提取
        glossary = glossary_service.extract_glossary_sync(
            pdf_path=input_path,
            source_lang=args.source,
            target_lang=args.target,
            extractor_type=args.translator,
            pages=pages,
            doc_type=args.doc_type,
            task=task,
            progress_callback=TaskProgressCallback(progress),
            tmp_dir=tmp_dir
        )
        
        if glossary:
            # 保存术语表到文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(glossary)
            
            progress.success(f"术语提取完成！")
            progress.log(f"输出文件: {output_path}")
            
            # 统计术语数量
            term_count = len([line for line in glossary.split('\n') if line.strip()])
            progress.log(f"提取到 {term_count} 个术语")
        else:
            progress.warning("未提取到任何术语")
            
    except KeyboardInterrupt:
        progress.log("\n正在取消术语提取...")
        task_service.cancel_task(task_id)
        progress.error("术语提取已取消")
        sys.exit(130)
    except Exception as e:
        progress.error(f"术语提取失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
