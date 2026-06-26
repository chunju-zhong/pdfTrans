"""
OCR视觉模型对比测试

对 tests/data/W3PD1098-v1.pdf 第6页，使用不同视觉模型进行 OCR + 翻译，
输出文件名以模型名命名，用于比较各模型的识别准确性。

用法:
    python tests/test_ocr_vision_models.py                     # 运行所有视觉模型
    python tests/test_ocr_vision_models.py --model DeepSeek-OCR # 只运行指定模型
    python tests/test_ocr_vision_models.py --dry-run            # 仅列出模型，不运行
    python tests/test_ocr_vision_models.py --parallel 3         # 并行运行N个模型
"""

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 测试数据目录
DATA_DIR = os.path.join(PROJECT_ROOT, "tests", "data")
# 模型列表文件
MODELS_FILE = os.path.join(PROJECT_ROOT, "aiping_models_all.json")
# 输入PDF
INPUT_PDF = os.path.join(DATA_DIR, "W3PD1098-v1.pdf")
# 默认输出目录
DEFAULT_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "tests", "output_ocr_comparison")


def load_vision_models():
    """从模型列表文件中加载所有视觉模型（vlm 类型）"""
    if not os.path.exists(MODELS_FILE):
        print(f"[错误] 模型列表文件不存在: {MODELS_FILE}")
        sys.exit(1)

    with open(MODELS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    vision_models = []
    for model in data.get("models", []):
        model_type = model.get("model_type", "")
        # 支持 vlm 字符串类型以及列表类型
        if model_type == "vlm" or (isinstance(model_type, list) and "vlm" in model_type):
            vision_models.append(model["id"])

    return vision_models


def run_translation(model_name, output_dir, dry_run=False, run_index=None, total=None):
    """对单个视觉模型执行 pdftrans translate 命令

    Args:
        model_name: 视觉模型名称
        output_dir: 输出文件目录
        dry_run: 如果为 True，只打印命令不执行
        run_index: 当前运行的索引（从1开始）
        total: 总模型数

    Returns:
        dict: 运行结果 {"model": str, "success": bool, "output": str, "elapsed": float}
    """
    # 输出文件路径
    safe_name = model_name.replace("/", "_").replace(" ", "_").replace("(", "").replace(")", "")
    output_file = os.path.join(output_dir, f"page6_{safe_name}.pdf")

    # 构建命令
    cmd = [
        sys.executable, "cli.py", "translate",
        INPUT_PDF,
        "-p", "6",
        "--ocr",
        "--ocr-engine", "llm",
        "--translation-model", "GLM-5.1",
        "--ocr-llm-model", model_name,
        "-o", output_file,
    ]

    # 显示命令
    prefix = ""
    if run_index is not None and total is not None:
        prefix = f"[{run_index}/{total}] "

    print(f"\n{'='*80}")
    print(f"{prefix}模型: {model_name}")
    print(f"{'='*80}")
    print(f"输出: {output_file}")
    print(f"命令: {' '.join(cmd)}")

    if dry_run:
        return {"model": model_name, "success": None, "output": "", "elapsed": 0}

    # 执行命令
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10分钟超时
            cwd=PROJECT_ROOT,
        )
        elapsed = time.time() - start_time

        if result.returncode == 0:
            print(f"成功 ({elapsed:.1f}s)")
            if result.stderr:
                print(f"   stderr: {result.stderr.strip()[-200:]}")
            return {
                "model": model_name,
                "success": True,
                "output": output_file,
                "elapsed": elapsed,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        else:
            print(f"失败 ({elapsed:.1f}s)")
            print(f"   返回码: {result.returncode}")
            if result.stdout:
                print(f"   stdout: {result.stdout.strip()[-300:]}")
            if result.stderr:
                print(f"   stderr: {result.stderr.strip()[-500:]}")
            return {
                "model": model_name,
                "success": False,
                "output": "",
                "elapsed": elapsed,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"超时 ({elapsed:.1f}s)")
        return {
            "model": model_name,
            "success": False,
            "output": "",
            "elapsed": elapsed,
            "error": "Timeout",
        }
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"异常 ({elapsed:.1f}s): {e}")
        return {
            "model": model_name,
            "success": False,
            "output": "",
            "elapsed": elapsed,
            "error": str(e),
        }


def print_summary(results, output_dir):
    """打印结果汇总"""
    success_count = sum(1 for r in results if r["success"])
    fail_count = sum(1 for r in results if not r["success"])
    total_time = sum(r["elapsed"] for r in results)

    print(f"\n\n{'='*80}")
    print("  结 果 汇 总")
    print(f"{'='*80}")
    print(f"总模型数: {len(results)}")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"总耗时: {total_time:.1f}s")
    print(f"平均耗时: {total_time / len(results):.1f}s" if results else "")
    print()

    if success_count > 0:
        print(f"{'模型名称':<45} {'状态':<6} {'耗时(s)':<10} {'输出文件'}")
        print("-" * 100)
        for r in results:
            if r["success"]:
                status = "OK"
                output = os.path.basename(r["output"])
            else:
                status = "FAIL"
                output = "-"
            print(f"{r['model']:<45} {status:<6} {r['elapsed']:<10.1f} {output}")

    if fail_count > 0:
        print(f"\n{'='*40} 失败详情 {'='*40}")
        for r in results:
            if not r["success"]:
                print(f"\n--- {r['model']} ---")
                if r.get("error"):
                    print(f"错误: {r['error']}")
                else:
                    stderr = r.get("stderr", "")
                    if stderr:
                        print(f"stderr: {stderr.strip()[-500:]}")

    # 写入汇总文件
    summary_file = os.path.join(output_dir, "summary.json")
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total": len(results),
        "success": success_count,
        "fail": fail_count,
        "total_time_seconds": round(total_time, 1),
        "models": [
            {
                "name": r["model"],
                "success": r["success"],
                "elapsed_seconds": round(r["elapsed"], 1),
                "output_file": os.path.basename(r["output"]) if r.get("output") else None,
                "error": r.get("error") or (
                    r["stderr"][-500:] if r.get("stderr") else None
                ),
            }
            for r in results
        ],
    }
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n汇总已保存: {summary_file}")


def main():
    parser = argparse.ArgumentParser(description="OCR视觉模型对比测试")
    parser.add_argument(
        "--model",
        default=None,
        help="只运行指定的单个模型（默认：运行所有视觉模型）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅列出模型和执行命令，不实际运行",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="并行运行的模型数量（默认：1，串行执行）",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"输出文件目录（默认: {DEFAULT_OUTPUT_DIR}）",
    )
    args = parser.parse_args()
    output_dir = args.output_dir

    # 加载模型列表
    models = load_vision_models()

    if not models:
        print("[错误] 未找到任何视觉模型 (vlm)")
        sys.exit(1)

    print(f"共发现 {len(models)} 个视觉模型:")
    for i, m in enumerate(models, 1):
        print(f"  {i:2d}. {m}")

    # 筛选指定模型
    if args.model:
        if args.model not in models:
            print(f"[错误] 模型 '{args.model}' 不在视觉模型列表中")
            sys.exit(1)
        models = [args.model]
        print(f"\n仅运行指定模型: {args.model}")

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    if args.dry_run:
        print(f"\n{'='*80}")
        print("DRY RUN 模式 - 仅列出，不执行")
        print(f"{'='*80}")
        for i, m in enumerate(models, 1):
            safe_name = m.replace("/", "_").replace(" ", "_").replace("(", "").replace(")", "")
            output_file = os.path.join(output_dir, f"page6_{safe_name}.pdf")
            print(f"\n[{i}/{len(models)}] {m}")
            print(f"  {sys.executable} cli.py translate {INPUT_PDF} -p 6 --ocr --ocr-engine llm "
                  f"--translation-model GLM-5.1 --ocr-llm-model \"{m}\" -o {output_file}")
        print(f"\n输出目录: {output_dir}")
        return

    # 执行翻译
    print(f"\n{'='*80}")
    print(f"开始测试 {len(models)} 个视觉模型")
    print(f"输入: {INPUT_PDF} (第6页)")
    print(f"翻译模型: GLM-5.1")
    print(f"输出目录: {output_dir}")
    print(f"并行数: {args.parallel}")
    print(f"{'='*80}")

    results = []

    if args.parallel <= 1:
        # 串行执行
        for i, model_name in enumerate(models, 1):
            result = run_translation(model_name, output_dir=output_dir, run_index=i, total=len(models))
            results.append(result)
    else:
        # 并行执行
        with ThreadPoolExecutor(max_workers=args.parallel) as executor:
            future_to_model = {
                executor.submit(
                    run_translation, model_name, output_dir=output_dir, run_index=i, total=len(models)
                ): model_name
                for i, model_name in enumerate(models, 1)
            }
            for future in as_completed(future_to_model):
                model_name = future_to_model[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"\n[错误] {model_name}: {e}")
                    results.append({"model": model_name, "success": False, "error": str(e)})

    # 按模型名称排序结果
    results.sort(key=lambda r: r["model"])

    # 打印汇总
    print_summary(results, output_dir)


if __name__ == "__main__":
    main()
