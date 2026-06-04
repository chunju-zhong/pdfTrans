# -*- coding: utf-8 -*-
import os
import time
import queue
import threading
import multiprocessing
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

from modules.ocr.ocr_worker import (
    OcrRetryableError,
    OcrFatalError,
    _degrade_params,
    _estimate_page_count,
    _heartbeat_sender,
    STATUS_HEARTBEAT,
    STATUS_STEP_START,
    STATUS_STEP_PROGRESS,
    STATUS_STEP_COMPLETE,
)


class TestOcrErrorTypes:
    def test_retryable_error_is_runtime(self):
        err = OcrRetryableError("test")
        assert isinstance(err, RuntimeError)
        assert str(err) == "test"

    def test_fatal_error_is_runtime(self):
        err = OcrFatalError("fatal")
        assert isinstance(err, RuntimeError)
        assert str(err) == "fatal"


class TestHeartbeatSender:
    def test_heartbeat_sends_status(self):
        mock_queue = MagicMock()
        stop_event = threading.Event()
        stop_event.set()
        _heartbeat_sender(mock_queue, stop_event)
        mock_queue.put.assert_not_called()

    @patch('psutil.Process')
    def test_heartbeat_sends_memory_info(self, mock_process_cls):
        mock_queue = MagicMock()
        stop_event = threading.Event()

        mock_process = MagicMock()
        mock_process.memory_info.return_value = MagicMock(rss=1024 * 1024 * 500)
        mock_process_cls.return_value = mock_process

        def stop_after_one(iteration_count=[0]):
            iteration_count[0] += 1
            if iteration_count[0] >= 1:
                stop_event.set()
            return False

        original_wait = stop_event.wait

        def mock_wait(timeout=None):
            stop_after_one()
            return stop_event.is_set()

        stop_event.wait = mock_wait

        _heartbeat_sender(mock_queue, stop_event)

        mock_queue.put.assert_called_once()
        call_args = mock_queue.put.call_args[0][0]
        assert call_args[0] == STATUS_HEARTBEAT
        assert 'pid' in call_args[1]
        assert 'memory_mb' in call_args[1]
        assert 'timestamp' in call_args[1]


class TestDegradeParams:
    @patch('modules.ocr.system_profiler.get_ocr_params')
    def test_degrade_none_params_creates_defaults(self, mock_get_params):
        mock_get_params.return_value = {
            'thread_params': {'CPU_NUM': '4', 'OMP_NUM_THREADS': '4',
                              'MKL_NUM_THREADS': '4', 'OPENBLAS_NUM_THREADS': '4'},
            'memory_params': {'memory_factor': 0.55,
                              'memory_cap_layout': 1600 * 1024 * 1024,
                              'memory_cap_table': 1600 * 1024 * 1024,
                              'memory_cap_formula': 1000 * 1024 * 1024},
            'render_dpi': 120,
            'skip_table': False,
            'skip_formula': False,
        }
        result = _degrade_params(None, 0)
        assert result['thread_params']['CPU_NUM'] == '3'
        assert result['render_dpi'] == 100
        assert result['skip_table'] is False

    def test_degrade_reduces_threads(self):
        params = {
            'thread_params': {'CPU_NUM': '4', 'OMP_NUM_THREADS': '4',
                              'MKL_NUM_THREADS': '4', 'OPENBLAS_NUM_THREADS': '4'},
            'memory_params': {'memory_factor': 0.55,
                              'memory_cap_layout': 1600 * 1024 * 1024,
                              'memory_cap_table': 1600 * 1024 * 1024,
                              'memory_cap_formula': 1000 * 1024 * 1024},
            'render_dpi': 120,
            'skip_table': False,
            'skip_formula': False,
        }
        result = _degrade_params(params, 0)
        assert result['thread_params']['CPU_NUM'] == '3'
        assert result['memory_params']['memory_factor'] == pytest.approx(0.44, abs=0.01)
        assert result['render_dpi'] == 100

    def test_degrade_skips_table_on_second_attempt(self):
        params = {
            'thread_params': {'CPU_NUM': '4', 'OMP_NUM_THREADS': '4',
                              'MKL_NUM_THREADS': '4', 'OPENBLAS_NUM_THREADS': '4'},
            'memory_params': {'memory_factor': 0.55,
                              'memory_cap_layout': 1600 * 1024 * 1024,
                              'memory_cap_table': 1600 * 1024 * 1024,
                              'memory_cap_formula': 1000 * 1024 * 1024},
            'render_dpi': 120,
            'skip_table': False,
            'skip_formula': False,
        }
        result = _degrade_params(params, 1)
        assert result['skip_table'] is True
        assert result['skip_formula'] is False

    def test_degrade_skips_formula_on_third_attempt(self):
        params = {
            'thread_params': {'CPU_NUM': '4', 'OMP_NUM_THREADS': '4',
                              'MKL_NUM_THREADS': '4', 'OPENBLAS_NUM_THREADS': '4'},
            'memory_params': {'memory_factor': 0.55,
                              'memory_cap_layout': 1600 * 1024 * 1024,
                              'memory_cap_table': 1600 * 1024 * 1024,
                              'memory_cap_formula': 1000 * 1024 * 1024},
            'render_dpi': 120,
            'skip_table': False,
            'skip_formula': False,
        }
        result = _degrade_params(params, 2)
        assert result['skip_table'] is True
        assert result['skip_formula'] is True

    def test_degrade_does_not_reduce_threads_below_1(self):
        params = {
            'thread_params': {'CPU_NUM': '1', 'OMP_NUM_THREADS': '1',
                              'MKL_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1'},
            'memory_params': {'memory_factor': 0.35,
                              'memory_cap_layout': 800 * 1024 * 1024,
                              'memory_cap_table': 800 * 1024 * 1024,
                              'memory_cap_formula': 500 * 1024 * 1024},
            'render_dpi': 80,
            'skip_table': True,
            'skip_formula': True,
        }
        result = _degrade_params(params, 0)
        assert result['thread_params']['CPU_NUM'] == '1'
        assert result['render_dpi'] == 72

    def test_degrade_does_not_reduce_dpi_below_72(self):
        params = {
            'thread_params': {'CPU_NUM': '2', 'OMP_NUM_THREADS': '2',
                              'MKL_NUM_THREADS': '2', 'OPENBLAS_NUM_THREADS': '2'},
            'memory_params': {'memory_factor': 0.35,
                              'memory_cap_layout': 800 * 1024 * 1024,
                              'memory_cap_table': 800 * 1024 * 1024,
                              'memory_cap_formula': 500 * 1024 * 1024},
            'render_dpi': 72,
            'skip_table': True,
            'skip_formula': True,
        }
        result = _degrade_params(params, 0)
        assert result['render_dpi'] == 72


class TestEstimatePageCount:
    @patch('fitz.open')
    def test_estimate_from_valid_pdf(self, mock_fitz_open):
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 42
        mock_doc.__enter__.return_value = mock_doc
        mock_doc.__exit__.return_value = None
        mock_fitz_open.return_value = mock_doc
        assert _estimate_page_count('test.pdf') == 42

    def test_estimate_on_error(self):
        assert _estimate_page_count('/nonexistent.pdf') == 10


class TestRunOcrInSubprocess:
    def test_fatal_error_on_missing_file(self):
        from modules.ocr.ocr_worker import run_ocr_in_subprocess
        with pytest.raises(OcrFatalError, match="PDF文件不存在"):
            run_ocr_in_subprocess('/nonexistent.pdf', max_retries=0, retry_backoff=0.1)

    @patch('modules.ocr.ocr_worker._run_ocr_once')
    @patch('os.path.exists', return_value=True)
    def test_retry_on_retryable_error(self, mock_exists, mock_run_once):
        from modules.ocr.ocr_worker import run_ocr_in_subprocess
        mock_run_once.side_effect = [
            OcrRetryableError("第一次失败"),
            MagicMock(total_pages=1),
        ]
        result = run_ocr_in_subprocess('test.pdf', max_retries=1, retry_backoff=0.1)
        assert mock_run_once.call_count == 2

    @patch('modules.ocr.ocr_worker._run_ocr_once')
    @patch('os.path.exists', return_value=True)
    def test_fatal_error_no_retry(self, mock_exists, mock_run_once):
        from modules.ocr.ocr_worker import run_ocr_in_subprocess
        mock_run_once.side_effect = OcrFatalError("不可重试")
        with pytest.raises(OcrFatalError, match="不可重试"):
            run_ocr_in_subprocess('test.pdf', max_retries=2, retry_backoff=0.1)
        assert mock_run_once.call_count == 1

    @patch('modules.ocr.ocr_worker._run_ocr_once')
    @patch('os.path.exists', return_value=True)
    def test_max_retries_exhausted(self, mock_exists, mock_run_once):
        from modules.ocr.ocr_worker import run_ocr_in_subprocess
        mock_run_once.side_effect = OcrRetryableError("持续失败")
        with pytest.raises(OcrRetryableError, match="持续失败"):
            run_ocr_in_subprocess('test.pdf', max_retries=2, retry_backoff=0.1)
        assert mock_run_once.call_count == 3

    @patch('modules.ocr.ocr_worker._degrade_params')
    @patch('modules.ocr.ocr_worker._run_ocr_once')
    @patch('os.path.exists', return_value=True)
    def test_retry_with_degraded_params(self, mock_exists, mock_run_once, mock_degrade):
        from modules.ocr.ocr_worker import run_ocr_in_subprocess
        degraded = {
            'thread_params': {'CPU_NUM': '2', 'OMP_NUM_THREADS': '2',
                              'MKL_NUM_THREADS': '2', 'OPENBLAS_NUM_THREADS': '2'},
            'memory_params': {'memory_factor': 0.44,
                              'memory_cap_layout': 1280 * 1024 * 1024,
                              'memory_cap_table': 1280 * 1024 * 1024,
                              'memory_cap_formula': 800 * 1024 * 1024},
            'render_dpi': 100,
            'skip_table': False,
            'skip_formula': False,
            'timeout_params': {'heartbeat_timeout': 90, 'max_total_time': 1800},
        }
        mock_degrade.return_value = degraded
        mock_run_once.side_effect = [
            OcrRetryableError("失败"),
            MagicMock(total_pages=1),
        ]
        result = run_ocr_in_subprocess('test.pdf', max_retries=1, retry_backoff=0.1)
        mock_degrade.assert_called_once()

    @patch('modules.ocr.ocr_worker._run_ocr_once')
    @patch('os.path.exists', return_value=True)
    @patch('modules.ocr.system_profiler.get_ocr_params')
    def test_dynamic_params_auto_compute(self, mock_get_params, mock_exists, mock_run_once):
        from modules.ocr.ocr_worker import run_ocr_in_subprocess
        mock_get_params.return_value = {
            'thread_params': {'CPU_NUM': '4'},
            'memory_params': {'memory_factor': 0.55},
            'timeout_params': {'heartbeat_timeout': 120, 'max_total_time': 900},
            'render_dpi': 120,
            'skip_table': False,
            'skip_formula': False,
        }
        mock_run_once.return_value = MagicMock(total_pages=1)
        result = run_ocr_in_subprocess('test.pdf', max_retries=0)
        mock_get_params.assert_called_once()

    @patch('modules.ocr.ocr_worker._run_ocr_once')
    @patch('os.path.exists', return_value=True)
    def test_success_on_first_try(self, mock_exists, mock_run_once):
        from modules.ocr.ocr_worker import run_ocr_in_subprocess
        mock_result = MagicMock(total_pages=5)
        mock_run_once.return_value = mock_result
        result = run_ocr_in_subprocess('test.pdf', max_retries=2, retry_backoff=0.1)
        assert result == mock_result
        assert mock_run_once.call_count == 1
