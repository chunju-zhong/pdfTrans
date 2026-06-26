#!/usr/bin/env python3
"""使用 aiping API 获取所有视觉理解模型 ID（VL + OCR，排除图像生成模型）"""

import requests
from config import config

API_URL = config.AIPING_API_URL.rstrip("/") + "/models"
HEADERS = {
    "Authorization": f"Bearer {config.AIPING_API_KEY}",
    "Content-Type": "application/json",
}

# 明确排除的非视觉理解模型
EXCLUDE_IDS = {
    "DeepSeek-R1-Distill-Qwen-32B", "DeepSeek-R1-Distill-Qwen-7B",
    "DeepSeek-R1-Distill-Llama-70B", "DeepSeek-R1-Distill-Qwen-14B",
    "DeepSeek-R1-Distill-Llama-8B",
    "DeepSeek-R1-0528", "DeepSeek-R1",
    "DeepSeek-V3", "DeepSeek-V3-0324", "DeepSeek-V3.1",
    "DeepSeek-V3.1-Terminus", "DeepSeek-V3.2-Exp",
    "DeepSeek-V3.2", "DeepSeek-V4-Pro", "DeepSeek-V4-Flash",
    "Kimi-K2-Instruct", "Kimi-K2-0905", "Kimi-K2-Thinking",
    "Kimi-K2.5", "Kimi-K2.6", "Kimi-K2.7-Code",
    "Kling-V1", "Kling-V1.5", "Kling-V2", "Kling-V2.1",
    "Kling-V2-New", "Kling-V2.6", "Kling-V3", "Kling-V3-Omni",
    "Kling-Video-O1",
    "MiniMax-M1-80k", "MiniMax-M2", "MiniMax-M2.1",
    "MiniMax-M2.5", "MiniMax-M2.7", "MiniMax-M3",
    "MiniMax-Hailuo-02", "MiniMax-Hailuo-2.3",
    "MiniMax-Speech-2.8-hd", "MiniMax-Speech-02-hd",
    "Doubao-Seed-1.8", "Doubao-Seed-2.0-pro", "Doubao-Seed-2.1-pro",
    "Doubao-Seed-2.1-turbo", "Doubao-Seed-2.0-lite",
    "Doubao-Seed-2.0-mini", "Doubao-Seed-2.0-Code",
    "MiMo-V2-Flash",
    "Wan2.5-T2I-Preview", "Wan2.5-I2I-Preview",
    "Wan2.6-I2V", "Wan2.6-T2V", "Wan2.6-R2V",
    "ViduQ2", "ViduQ2-Pro", "ViduQ3-Pro", "ViduQ3-Turbo",
    "ViduQ3-Pro-Fast", "ViduQ2-Turbo",
    "Step-3.5-Flash",
    "Doubao-Seedream-4.0", "Doubao-Seedream-4.5", "Doubao-Seedream-5.0-lite",
}

# 视觉理解模型关键词（VL + OCR，排除图像生成类）
VISION_UNDERSTANDING_PATTERNS = [
    # VL 视觉语言模型
    "qwen3-vl-", "qwen2.5-vl-", "qwen2-vl-",
    "internvl", "deepseek-vl", "cogvlm",
    # GLM 带 V 后缀的视觉版
    "glm-4.5v", "glm-4.6v",
    # OCR 模型
    "deepseek-ocr",
]


def is_vision_understanding_model(model_id: str) -> bool:
    """判断是否为视觉理解模型（VL 或 OCR，排除图像生成）"""
    if model_id in EXCLUDE_IDS:
        return False
    model_lower = model_id.lower()
    return any(pattern.lower() in model_lower for pattern in VISION_UNDERSTANDING_PATTERNS)


def get_model_category(model_id: str) -> str:
    """获取模型所属分类标签"""
    model_lower = model_id.lower()
    if any(k in model_lower for k in ["qwen3-vl-", "qwen2.5-vl-", "qwen2-vl-", "internvl", "deepseek-vl", "cogvlm"]):
        return "视觉语言 (VL)"
    if "glm-4.5v" in model_lower or "glm-4.6v" in model_lower:
        return "视觉语言 (GLM-V)"
    if "deepseek-ocr" in model_lower:
        return "OCR"
    return "视觉理解"


print(f"请求 API: {API_URL}")
print()

try:
    resp = requests.get(API_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()
except Exception as e:
    print(f"请求失败: {e}")
    if 'resp' in dir() and resp.text:
        print(f"响应内容: {resp.text[:500]}")
    exit(1)

models = data.get("data", [])
print(f"共获取到 {len(models)} 个模型\n")

# 筛选视觉理解模型
vision_models = []
other_models = []

for model in models:
    if is_vision_understanding_model(model["id"]):
        vision_models.append(model)
    else:
        other_models.append(model)

# 输出结果
print("=" * 100)
print(f"视觉理解模型（VL + OCR，共 {len(vision_models)} 个）：")
print("=" * 100)
print(f"{'#':>3} | {'模型 ID':<45} | {'分类':<18} | {'输入价格':<12} | {'输出价格':<12}")
print("-" * 100)
for i, model in enumerate(vision_models, 1):
    mid = model["id"]
    cat = get_model_category(mid)
    price = model.get("price", {})
    in_price = price.get("input_price_range", ["-"])
    out_price = price.get("output_price_range", ["-"])
    in_str = f"{in_price[0]}-{in_price[1]}" if isinstance(in_price, list) and len(in_price) > 1 else str(in_price)
    out_str = f"{out_price[0]}-{out_price[1]}" if isinstance(out_price, list) and len(out_price) > 1 else str(out_price)
    print(f"{i:3d} | {mid:<45} | {cat:<18} | ¥{in_str:<9} | ¥{out_str:<9}")

print(f"\n排除的图像生成/其他模型：{len(other_models)} 个")
print(f"\n提示：视觉理解模型可直接接收图像输入进行分析理解（VL、OCR 等），")
print(f"      已排除图像生成类模型（Qwen-Image、Kolors、即梦、豆包Seedream 等）。")