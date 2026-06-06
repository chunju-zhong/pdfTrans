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
    _assemble_extraction,
    STATUS_HEARTBEAT,
    STATUS_STEP_START,
    STATUS_STEP_PROGRESS,
    STATUS_STEP_COMPLETE,
    STATUS_PAGE_RESULT,
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
            ({1: {'text_blocks': [], 'tables': [], 'images': []}}, [1]),
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
            ({1: {'text_blocks': [], 'tables': [], 'images': []}}, [1]),
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
        mock_run_once.return_value = ({1: {'text_blocks': [], 'tables': [], 'images': []}}, [1])
        result = run_ocr_in_subprocess('test.pdf', max_retries=0)
        mock_get_params.assert_called_once()

    @patch('modules.ocr.ocr_worker._run_ocr_once')
    @patch('os.path.exists', return_value=True)
    def test_success_on_first_try(self, mock_exists, mock_run_once):
        from modules.ocr.ocr_worker import run_ocr_in_subprocess
        mock_return = ({1: {'text_blocks': [], 'tables': [], 'images': []}}, [1])
        mock_run_once.return_value = mock_return
        result = run_ocr_in_subprocess('test.pdf', max_retries=2, retry_backoff=0.1)
        assert mock_run_once.call_count == 1

    @patch('modules.ocr.ocr_worker._run_ocr_once')
    @patch('os.path.exists', return_value=True)
    def test_checkpoint_resume_merges_results(self, mock_exists, mock_run_once):
        """测试断点续传：首次返回部分结果，重试补充剩余页面"""
        from modules.ocr.ocr_worker import run_ocr_in_subprocess
        # 首次完成 1-3 页，重试完成 4-5 页
        mock_run_once.side_effect = [
            ({1: {'text_blocks': [], 'tables': [], 'images': []},
              2: {'text_blocks': [], 'tables': [], 'images': []},
              3: {'text_blocks': [], 'tables': [], 'images': []}}, [1, 2, 3]),
            ({4: {'text_blocks': [], 'tables': [], 'images': []},
              5: {'text_blocks': [], 'tables': [], 'images': []}}, [4, 5]),
        ]
        result = run_ocr_in_subprocess('test.pdf', pages=[1, 2, 3, 4, 5], max_retries=1, retry_backoff=0.1)
        assert len(result.pages) == 5
        assert mock_run_once.call_count == 2
        # 第二次调用应传入 skip_pages
        second_call_kwargs = mock_run_once.call_args_list[1]
        assert second_call_kwargs[1].get('skip_pages') == [1, 2, 3] or second_call_kwargs[0][8] == [1, 2, 3]

    @patch('modules.ocr.ocr_worker._run_ocr_once')
    @patch('os.path.exists', return_value=True)
    def test_all_pages_done_skips_retry(self, mock_exists, mock_run_once):
        """测试所有页面已通过流式回传完成时不再重试"""
        from modules.ocr.ocr_worker import run_ocr_in_subprocess
        mock_run_once.return_value = (
            {1: {'text_blocks': [], 'tables': [], 'images': []},
             2: {'text_blocks': [], 'tables': [], 'images': []}}, [1, 2])
        result = run_ocr_in_subprocess('test.pdf', pages=[1, 2], max_retries=2, retry_backoff=0.1)
        assert len(result.pages) == 2
        assert mock_run_once.call_count == 1


class TestAssembleExtraction:
    def test_assemble_empty_pages(self):
        """测试无页面结果时组装"""
        result = _assemble_extraction({}, 0, [])
        assert len(result.pages) == 0
        assert len(result.tables) == 0
        assert len(result.images) == 0

    def test_assemble_single_page(self):
        """测试单页结果组装"""
        from models.text_block import TextBlock
        tb_dict = TextBlock(block_no=0, text="Hello", bbox=[0, 0, 100, 20], page_num=1).to_dict()
        completed = {1: {'text_blocks': [tb_dict], 'tables': [], 'images': []}}
        result = _assemble_extraction(completed, 1, [1])
        assert len(result.pages) == 1
        assert result.pages[0].page_num == 1
        assert result.pages[0].text_blocks[0].block_text == "Hello"

    def test_assemble_multiple_pages_with_tables_and_images(self):
        """测试多页结果组装，含表格和图像"""
        from models.extraction import PdfTable, PdfImage
        table_dict = PdfTable(page_num=1, table_idx=0, cells=[], bbox=[0, 0, 100, 100]).to_dict()
        image_dict = PdfImage(page_num=2, image_idx=0, image_path="/tmp/test.png", bbox=[0, 0, 50, 50]).to_dict()
        completed = {
            1: {'text_blocks': [], 'tables': [table_dict], 'images': []},
            2: {'text_blocks': [], 'tables': [], 'images': [image_dict]},
        }
        result = _assemble_extraction(completed, 2, [1, 2])
        assert len(result.pages) == 2
        assert len(result.tables) == 1
        assert result.tables[0].table_idx == 0
        assert len(result.images) == 1
        assert result.images[0].image_idx == 0

    def test_assemble_missing_page_gets_empty_blocks(self):
        """测试缺失页面自动填充空 text_blocks"""
        completed = {1: {'text_blocks': [], 'tables': [], 'images': []}}
        result = _assemble_extraction(completed, 2, [1, 2])
        assert len(result.pages) == 2
        assert result.pages[1].page_num == 2
        assert len(result.pages[1].text_blocks) == 0

    def test_assemble_global_indexing(self):
        """测试全局 table_idx 和 image_idx 编号"""
        from models.extraction import PdfTable, PdfImage
        t1 = PdfTable(page_num=1, table_idx=0, cells=[], bbox=[0, 0, 100, 100]).to_dict()
        t2 = PdfTable(page_num=2, table_idx=0, cells=[], bbox=[0, 0, 100, 100]).to_dict()
        i1 = PdfImage(page_num=1, image_idx=0, image_path="/tmp/a.png", bbox=[0, 0, 50, 50]).to_dict()
        i2 = PdfImage(page_num=2, image_idx=0, image_path="/tmp/b.png", bbox=[0, 0, 50, 50]).to_dict()
        completed = {
            1: {'text_blocks': [], 'tables': [t1], 'images': [i1]},
            2: {'text_blocks': [], 'tables': [t2], 'images': [i2]},
        }
        result = _assemble_extraction(completed, 2, [1, 2])
        assert result.tables[0].table_idx == 0
        assert result.tables[1].table_idx == 1
        assert result.images[0].image_idx == 0
        assert result.images[1].image_idx == 1


class TestStatusPageResult:
    def test_page_result_constant_value(self):
        """测试 STATUS_PAGE_RESULT 常量值"""
        assert STATUS_PAGE_RESULT == 'page_result'

    def test_page_result_message_format(self):
        """测试 page_result 消息格式"""
        msg_type, payload = STATUS_PAGE_RESULT, {
            'page_num': 5,
            'text_blocks': [],
            'tables': [],
            'images': [],
        }
        assert msg_type == 'page_result'
        assert 'page_num' in payload
        assert 'text_blocks' in payload
        assert 'tables' in payload
        assert 'images' in payload
