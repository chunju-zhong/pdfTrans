# -*- coding: utf-8 -*-
import logging
import os

import psutil

from config import config

logger = logging.getLogger(__name__)


class SystemProfile:
    def __init__(self):
        mem = psutil.virtual_memory()
        self.cpu_count = psutil.cpu_count(logical=False) or psutil.cpu_count(logical=True) or 1
        self.cpu_count_logical = psutil.cpu_count(logical=True) or 1
        self.total_memory_gb = round(mem.total / (1024 ** 3), 2)
        self.available_memory_gb = round(mem.available / (1024 ** 3), 2)
        self.memory_percent = mem.percent
        self.gpu_available = False
        self.gpu_count = 0
        self._detect_gpu()
        if hasattr(os, "getloadavg"):
            self.load_avg_1m = os.getloadavg()[0]
        else:
            self.load_avg_1m = 0.0
        logger.info(
            "系统资源检测: CPU物理=%d 逻辑=%d, 可用内存=%.1f/%.1fGB(%.0f%%), GPU=%s(%d), 负载=%.2f",
            self.cpu_count,
            self.cpu_count_logical,
            self.available_memory_gb,
            self.total_memory_gb,
            self.memory_percent,
            self.gpu_available,
            self.gpu_count,
            self.load_avg_1m,
        )

    def _detect_gpu(self):
        try:
            import paddle
            if paddle.is_compiled_with_cuda():
                count = paddle.device.cuda.device_count()
                if count > 0:
                    self.gpu_available = True
                    self.gpu_count = count
        except Exception:
            pass

    def is_high_load(self):
        return self.memory_percent > 85 or self.load_avg_1m > self.cpu_count * 0.8

    def is_low_memory(self):
        return self.available_memory_gb < 4.0


class OcrParameterCalculator:
    MEMORY_TIERS = {
        "minimal": (0, 8),
        "low": (8, 17),
        "medium": (17, 33),
        "high": (33, 65),
        "unlimited": (65, float("inf")),
    }

    def __init__(self, profile: SystemProfile):
        self.profile = profile
        self.tier = self._determine_tier()
        logger.info("内存分级: %s (可用%.1fGB/总%.1fGB)", self.tier, self.profile.available_memory_gb, self.profile.total_memory_gb)

    def _determine_tier(self):
        total_gb = self.profile.total_memory_gb
        for tier, (low, high) in self.MEMORY_TIERS.items():
            if low <= total_gb < high:
                return tier
        return "minimal"

    def compute_thread_params(self):
        cpu = self.profile.cpu_count_logical
        if self.tier == "minimal":
            threads = max(1, min(2, cpu))
        elif self.tier == "low":
            threads = max(2, min(cpu, 4))
        elif self.tier == "medium":
            threads = max(2, min(cpu, 6))
        elif self.tier == "high":
            threads = max(2, min(cpu, 8))
        else:
            threads = max(2, min(cpu, 8))

        if self.profile.is_high_load():
            threads = max(1, cpu // 4)

        val = str(threads)
        return {
            "CPU_NUM": val,
            "OMP_NUM_THREADS": val,
            "MKL_NUM_THREADS": val,
            "OPENBLAS_NUM_THREADS": val,
        }

    def compute_memory_params(self):
        tier_params = {
            "minimal": (0.35, 1000, 800, 500),
            "low": (0.45, 1400, 1200, 800),
            "medium": (0.55, 1800, 1600, 1000),
            "high": (0.60, 2600, 2400, 1500),
            "unlimited": (0.65, 3400, 3200, 2000),
        }
        factor, cap_layout, cap_table, cap_formula = tier_params[self.tier]

        if self.profile.is_high_load():
            factor *= 0.85
            cap_layout = int(cap_layout * 0.85)
            cap_table = int(cap_table * 0.85)
            cap_formula = int(cap_formula * 0.85)

        return {
            "memory_factor": round(factor, 2),
            "memory_cap_layout": cap_layout * 1024 * 1024,
            "memory_cap_table": cap_table * 1024 * 1024,
            "memory_cap_formula": cap_formula * 1024 * 1024,
        }

    def compute_render_dpi(self, user_dpi=None):
        if user_dpi is not None:
            return user_dpi
        tier_dpi = {
            "minimal": 100,
            "low": 120,
            "medium": 120,
            "high": 150,
            "unlimited": 150,
        }
        return tier_dpi[self.tier]

    def compute_timeout_params(self, page_count=1):
        tier_base_per_page = {
            "minimal": 120,
            "low": 90,
            "medium": 60,
            "high": 45,
            "unlimited": 30,
        }
        base_per_page = tier_base_per_page[self.tier]

        if self.profile.is_high_load():
            base_per_page = int(base_per_page * 1.5)

        tier_heartbeat_multiplier = {
            "minimal": 3,
            "low": 2,
            "medium": 2,
            "high": 2,
            "unlimited": 2,
        }
        heartbeat_timeout = max(90, base_per_page * tier_heartbeat_multiplier[self.tier])
        max_total_time = max(600, base_per_page * page_count * 2 + 300)

        return {
            "heartbeat_timeout": heartbeat_timeout,
            "max_total_time": max_total_time,
        }

    TIER_ORDER = ["minimal", "low", "medium", "high", "unlimited"]

    MODEL_NAMES = {
        "minimal": {
            "layout": "PP-DocLayout-S",
            "formula": "PP-FormulaNet_plus-S",
            "text_det": "PP-OCRv4_mobile_det",
            "text_rec": "PP-OCRv4_mobile_rec",
            "table": "SLANet",
        },
        "low": {
            "layout": "PP-DocLayout-M",
            "formula": "PP-FormulaNet_plus-S",
            "text_det": "PP-OCRv4_mobile_det",
            "text_rec": "PP-OCRv4_mobile_rec",
            "table": "SLANet_plus",
        },
        "medium": {
            "layout": "PP-DocLayout-M",
            "formula": "PP-FormulaNet_plus-M",
            "text_det": "PP-OCRv4_server_det",
            "text_rec": "PP-OCRv4_server_rec",
            "table": "SLANet_plus",
        },
        "high": {
            "layout": "PP-DocLayout-L",
            "formula": "PP-FormulaNet_plus-M",
            "text_det": "PP-OCRv4_server_det",
            "text_rec": "PP-OCRv4_server_rec",
            "table": "SLANet_plus",
        },
        "unlimited": {
            "layout": "PP-DocLayout-L",
            "formula": "PP-FormulaNet_plus-L",
            "text_det": "PP-OCRv4_server_det",
            "text_rec": "PP-OCRv4_server_rec",
            "table": "SLANet_plus",
        },
    }

    INFERENCE_PARAMS = {
        "minimal": {"text_recognition_batch_size": 4, "text_det_limit_side_len": 720},
        "low": {"text_recognition_batch_size": 6, "text_det_limit_side_len": 720},
        "medium": {"text_recognition_batch_size": 10, "text_det_limit_side_len": 960},
        "high": {"text_recognition_batch_size": 16, "text_det_limit_side_len": 960},
        "unlimited": {"text_recognition_batch_size": 16, "text_det_limit_side_len": 960},
    }

    def compute_model_names(self):
        tier = self.tier
        if self.compute_use_gpu():
            idx = self.TIER_ORDER.index(tier)
            if idx < len(self.TIER_ORDER) - 1:
                tier = self.TIER_ORDER[idx + 1]
        return dict(self.MODEL_NAMES[tier])

    def compute_inference_params(self):
        return dict(self.INFERENCE_PARAMS[self.tier])

    def compute_use_gpu(self):
        return self.profile.gpu_available and config.OCR_USE_GPU

    def should_skip_table(self):
        return self.profile.total_memory_gb <= 4

    def should_skip_formula(self):
        return self.profile.total_memory_gb <= 8

    def compute_all_params(self, page_count=1, user_dpi=None):
        thread_params = self.compute_thread_params()
        memory_params = self.compute_memory_params()
        timeout_params = self.compute_timeout_params(page_count)
        model_names = self.compute_model_names()
        inference_params = self.compute_inference_params()
        use_gpu = self.compute_use_gpu()
        result = {
            "tier": self.tier,
            "high_load": self.profile.is_high_load(),
            "low_memory": self.profile.is_low_memory(),
            "gpu_available": self.profile.gpu_available,
            "gpu_count": self.profile.gpu_count,
            "cpu_count": self.profile.cpu_count,
            "cpu_count_logical": self.profile.cpu_count_logical,
            "total_memory_gb": self.profile.total_memory_gb,
            "available_memory_gb": self.profile.available_memory_gb,
            "memory_percent": self.profile.memory_percent,
            "load_avg_1m": self.profile.load_avg_1m,
            "render_dpi": self.compute_render_dpi(user_dpi),
            "skip_table": self.should_skip_table(),
            "skip_formula": self.should_skip_formula(),
            "model_names": model_names,
            "inference_params": inference_params,
            "use_gpu": use_gpu,
            "thread_params": thread_params,
            "memory_params": memory_params,
            "timeout_params": timeout_params,
        }
        logger.info(
            "OCR参数计算完成: tier=%s, threads=%s, factor=%.2f, dpi=%d, "
            "heartbeat_timeout=%ds, max_total_time=%ds, skip_table=%s, skip_formula=%s, "
            "model_names=%s, inference_params=%s",
            self.tier,
            thread_params["CPU_NUM"],
            memory_params["memory_factor"],
            result["render_dpi"],
            timeout_params["heartbeat_timeout"],
            timeout_params["max_total_time"],
            result["skip_table"],
            result["skip_formula"],
            model_names,
            inference_params,
        )
        return result


def get_ocr_params(page_count=1, user_dpi=None):
    profile = SystemProfile()
    calculator = OcrParameterCalculator(profile)
    return calculator.compute_all_params(page_count=page_count, user_dpi=user_dpi)
