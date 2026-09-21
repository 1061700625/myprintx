import io
import os
import sys
import tempfile
import unittest
from unittest import mock

import myprintx


class TestTiming(unittest.TestCase):

    def setUp(self):
        self.original_stdout = sys.stdout
        self.original_show = myprintx.is_show()
        self.output = io.StringIO()
        sys.stdout = self.output
        myprintx.set_show(True)
        self.addCleanup(self.restore_environment)

    def restore_environment(self):
        myprintx.unpatch_log()
        myprintx.set_show(self.original_show)
        sys.stdout = self.original_stdout

    def test_context_manager_reports_and_exposes_elapsed_seconds(self):
        with mock.patch("myprintx.timing.time.perf_counter", side_effect=(10.0, 11.25)):
            with myprintx.timer("数据处理") as timing:
                pass

        self.assertEqual(timing.elapsed, 1.25)
        self.assertEqual(self.output.getvalue(), "[TIMER] 数据处理 | 耗时 1.250 秒\n")
    def test_manual_timer_returns_elapsed_seconds(self):
        with mock.patch("myprintx.timing.time.perf_counter", side_effect=(20.0, 22.5)):
            myprintx.timer_start("下载")
            elapsed = myprintx.timer_end("下载")

        self.assertEqual(elapsed, 2.5)
        self.assertEqual(self.output.getvalue(), "[TIMER] 下载 | 耗时 2.500 秒\n")

    def test_decorator_preserves_function_and_return_value(self):
        with mock.patch("myprintx.timing.time.perf_counter", side_effect=(30.0, 30.75)):
            @myprintx.timer("计算")
            def add(left, right):
                return left + right

            result = add(2, 3)

        self.assertEqual(result, 5)
        self.assertEqual(add.__name__, "add")
        self.assertEqual(self.output.getvalue(), "[TIMER] 计算 | 耗时 0.750 秒\n")

    def test_decorator_reports_elapsed_time_without_swallowing_exception(self):
        with mock.patch("myprintx.timing.time.perf_counter", side_effect=(40.0, 40.5)):
            @myprintx.timer("失败任务")
            def fail():
                raise ValueError("boom")

            with self.assertRaisesRegex(ValueError, "boom"):
                fail()

        self.assertEqual(self.output.getvalue(), "[TIMER] 失败任务 | 耗时 0.500 秒\n")

    def test_manual_timer_rejects_duplicate_and_missing_names(self):
        with mock.patch("myprintx.timing.time.perf_counter", side_effect=(50.0, 51.0)):
            myprintx.timer_start("重复")
            with self.assertRaisesRegex(RuntimeError, "already running"):
                myprintx.timer_start("重复")
            myprintx.timer_end("重复")

        with self.assertRaisesRegex(RuntimeError, "was not started"):
            myprintx.timer_end("不存在")

    def test_hidden_output_still_calculates_elapsed_time(self):
        myprintx.set_show(False)
        with mock.patch("myprintx.timing.time.perf_counter", side_effect=(60.0, 61.5)):
            myprintx.timer_start("静默")
            elapsed = myprintx.timer_end("静默")

        self.assertEqual(elapsed, 1.5)
        self.assertEqual(self.output.getvalue(), "")

    def test_timer_output_is_written_to_log(self):
        with tempfile.TemporaryDirectory() as directory:
            log_path = os.path.join(directory, "timing.log")
            myprintx.patch_log(log_path)
            with mock.patch("myprintx.timing.time.perf_counter", side_effect=(70.0, 72.0)):
                with myprintx.timer("日志任务"):
                    pass

            with open(log_path, encoding="utf-8") as log_file:
                self.assertEqual(log_file.read(), "[TIMER] 日志任务 | 耗时 2.000 秒\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
