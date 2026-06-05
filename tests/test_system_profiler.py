# -*- coding: utf-8 -*-
import pytest
from unittest.mock import patch, MagicMock

from modules.ocr.system_profiler import SystemProfile, OcrParameterCalculator, get_ocr_params


def _make_profile(cpu_count=8, cpu_count_logical=16, total_memory_gb=16.0,
                  available_memory_gb=8.0, memory_percent=50.0,
                  gpu_available=False, gpu_count=0, load_avg_1m=2.0):
    profile = MagicMock(spec=SystemProfile)
    profile.cpu_count = cpu_count
    profile.cpu_count_logical = cpu_count_logical
    profile.total_memory_gb = total_memory_gb
    profile.available_memory_gb = available_memory_gb
    profile.memory_percent = memory_percent
    profile.gpu_available = gpu_available
    profile.gpu_count = gpu_count
    profile.load_avg_1m = load_avg_1m
    profile.is_high_load.return_value = memory_percent > 85 or load_avg_1m > cpu_count * 0.8
    profile.is_low_memory.return_value = available_memory_gb < 4.0
    return profile


class TestSystemProfile:
    @patch('modules.ocr.system_profiler.psutil')
    def test_profile_detection(self, mock_psutil):
        mock_mem = MagicMock()
        mock_mem.total = 16 * 1024 ** 3
        mock_mem.available = 8 * 1024 ** 3
        mock_mem.percent = 50.0
        mock_psutil.virtual_memory.return_value = mock_mem
        mock_psutil.cpu_count.side_effect = [8, 16]

        profile = SystemProfile()
        assert profile.cpu_count == 8
        assert profile.cpu_count_logical == 16
        assert profile.total_memory_gb == 16.0
        assert profile.available_memory_gb == 8.0
        assert profile.memory_percent == 50.0

    @patch('modules.ocr.system_profiler.psutil')
    def test_high_load_detection(self, mock_psutil):
        mock_mem = MagicMock()
        mock_mem.total = 16 * 1024 ** 3
        mock_mem.available = 2 * 1024 ** 3
        mock_mem.percent = 90.0
        mock_psutil.virtual_memory.return_value = mock_mem
        mock_psutil.cpu_count.side_effect = [4, 8]

        profile = SystemProfile()
        assert profile.is_high_load() is True

    @patch('modules.ocr.system_profiler.psutil')
    def test_low_memory_detection(self, mock_psutil):
        mock_mem = MagicMock()
        mock_mem.total = 4 * 1024 ** 3
        mock_mem.available = 1 * 1024 ** 3
        mock_mem.percent = 75.0
        mock_psutil.virtual_memory.return_value = mock_mem
        mock_psutil.cpu_count.side_effect = [2, 4]

        profile = SystemProfile()
        assert profile.is_low_memory() is True


class TestOcrParameterCalculator:
    def test_minimal_tier(self):
        profile = _make_profile(total_memory_gb=4.0, available_memory_gb=4.0, cpu_count=2, cpu_count_logical=4)
        calc = OcrParameterCalculator(profile)
        assert calc.tier == 'minimal'

        params = calc.compute_all_params(page_count=10)
        assert params['skip_formula'] is True
        assert int(params['thread_params']['CPU_NUM']) <= 2

    def test_low_tier(self):
        profile = _make_profile(total_memory_gb=12.0, available_memory_gb=12.0, cpu_count=4, cpu_count_logical=8)
        calc = OcrParameterCalculator(profile)
        assert calc.tier == 'low'

        params = calc.compute_all_params()
        assert params['skip_formula'] is False
        assert int(params['thread_params']['CPU_NUM']) <= 4

    def test_medium_tier(self):
        profile = _make_profile(total_memory_gb=24.0, available_memory_gb=24.0, cpu_count=8, cpu_count_logical=16)
        calc = OcrParameterCalculator(profile)
        assert calc.tier == 'medium'

        params = calc.compute_all_params(page_count=20)
        assert params['skip_table'] is False
        assert params['skip_formula'] is False
        assert params['timeout_params']['max_total_time'] > 600

    def test_high_tier(self):
        profile = _make_profile(total_memory_gb=48.0, available_memory_gb=48.0, cpu_count=16, cpu_count_logical=32)
        calc = OcrParameterCalculator(profile)
        assert calc.tier == 'high'

        params = calc.compute_all_params()
        assert int(params['thread_params']['CPU_NUM']) <= 8
        assert params['render_dpi'] == 150

    def test_high_load_reduces_params(self):
        profile = _make_profile(
            total_memory_gb=24.0, available_memory_gb=24.0, cpu_count=8, cpu_count_logical=16,
            memory_percent=90.0, load_avg_1m=10.0,
        )
        calc = OcrParameterCalculator(profile)
        assert profile.is_high_load() is True

        params = calc.compute_all_params()
        normal_profile = _make_profile(total_memory_gb=24.0, available_memory_gb=24.0, cpu_count=8, cpu_count_logical=16)
        normal_calc = OcrParameterCalculator(normal_profile)
        normal_params = normal_calc.compute_all_params()

        assert int(params['thread_params']['CPU_NUM']) < int(normal_params['thread_params']['CPU_NUM'])
        assert params['memory_params']['memory_factor'] < normal_params['memory_params']['memory_factor']

    def test_memory_params_in_bytes(self):
        profile = _make_profile(available_memory_gb=24.0, cpu_count=8, cpu_count_logical=16)
        calc = OcrParameterCalculator(profile)
        params = calc.compute_all_params()

        for cap_key in ('memory_cap_layout', 'memory_cap_table', 'memory_cap_formula'):
            assert params['memory_params'][cap_key] > 100 * 1024 * 1024

    def test_user_dpi_overrides(self):
        profile = _make_profile(available_memory_gb=4.0, cpu_count=2, cpu_count_logical=4)
        calc = OcrParameterCalculator(profile)
        assert calc.compute_render_dpi(user_dpi=200) == 200

    def test_timeout_scales_with_pages(self):
        profile = _make_profile(available_memory_gb=24.0, cpu_count=8, cpu_count_logical=16)
        calc = OcrParameterCalculator(profile)
        small = calc.compute_timeout_params(page_count=1)
        large = calc.compute_timeout_params(page_count=100)
        assert large['max_total_time'] > small['max_total_time']

    def test_skip_table_minimal_under_6gb(self):
        profile = _make_profile(available_memory_gb=4.0, total_memory_gb=5.0, cpu_count=2, cpu_count_logical=4)
        calc = OcrParameterCalculator(profile)
        assert calc.should_skip_table() is True

    def test_no_skip_table_minimal_over_6gb(self):
        profile = _make_profile(available_memory_gb=7.0, total_memory_gb=8.0, cpu_count=2, cpu_count_logical=4)
        calc = OcrParameterCalculator(profile)
        assert calc.should_skip_table() is False


class TestGetOcrParams:
    @patch('modules.ocr.system_profiler.SystemProfile')
    def test_get_ocr_params_returns_dict(self, mock_profile_cls):
        mock_profile = _make_profile(available_memory_gb=24.0, cpu_count=8, cpu_count_logical=16)
        mock_profile_cls.return_value = mock_profile

        params = get_ocr_params(page_count=10)
        assert isinstance(params, dict)
        assert 'thread_params' in params
        assert 'memory_params' in params
        assert 'timeout_params' in params
        assert 'render_dpi' in params
        assert 'skip_table' in params
        assert 'skip_formula' in params
