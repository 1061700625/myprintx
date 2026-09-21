import io
import sys
import builtins
import unittest
import inspect
import itertools
import multiprocessing
import os
import tempfile
from datetime import datetime
from unittest import mock
import myprintx


def _print_prefix_in_child(output_queue, ready, release, show_pid):
    """在真实 multiprocessing 子进程中生成一条前缀输出。"""
    output = io.StringIO()
    myprintx.patch_prefix(
        show_date=False,
        show_time=False,
        custom_prefix="子进程",
        show_pid=show_pid,
    )
    ready.set()
    release.wait(5)
    myprintx.print("正文", file=output)
    output_queue.put((os.getpid(), output.getvalue()))


class TestMyPrintX(unittest.TestCase):

    def setUp(self):
        """保存调用环境，每项测试从独立的默认状态开始。"""
        self._state_names = (
            "print", "__orig_print__", "__print_prefix__", "__print_show__",
            "__print_log__",
            "__show_debug__", "__show_info__", "__show_warn__", "__show_error__",
        )
        self._saved_state = {
            name: getattr(builtins, name) for name in self._state_names
            if hasattr(builtins, name)
        }
        self._stdout = sys.stdout
        self.addCleanup(self.restore_environment)
        myprintx.unpatch_color()
        myprintx.unpatch_prefix()
        myprintx.unpatch_log()
        myprintx.set_show(True)
        for setter in (myprintx.show_debug, myprintx.show_info,
                       myprintx.show_warn, myprintx.show_error):
            setter(True)
        self.output = io.StringIO()
        sys.stdout = self.output

    def restore_environment(self):
        """即使测试失败，也恢复原有接管、前缀和显示开关。"""
        sys.stdout = self._stdout
        for name in self._state_names:
            if name in self._saved_state:
                setattr(builtins, name, self._saved_state[name])
            elif hasattr(builtins, name):
                delattr(builtins, name)

    def get_output(self):
        """返回打印输出（不自动清除 ANSI）"""
        return self.output.getvalue().strip()

    # ---------- 基本功能测试 ----------

    def test_basic_print(self):
        """测试基本打印功能"""
        myprintx.print("Hello World")
        out = self.get_output()
        self.assertIn("Hello World", out)

    def test_windows_ansi_initialization_runs_only_once(self):
        """Windows ANSI 初始化不应为每条输出重复启动 cmd.exe。"""
        with mock.patch.object(sys, "platform", "win32"), \
             mock.patch.object(os, "system") as system:
            myprintx.print("第一条")
            myprintx.print("第二条")

        system.assert_called_once_with("")

    def test_color_and_style(self):
        """测试彩色和样式打印"""
        myprintx.patch_color()
        myprintx.print("Success", fg_color="green", style="bold")
        out = self.get_output()
        # 验证包含 ANSI 控制码（粗体和绿色）
        self.assertRegex(out, r"\033\[[0-9;]*1;?32")

    def test_hex_foreground_and_background_colors(self):
        """测试十六进制前景色和背景色"""
        myprintx.print("Custom", fg_color="#FF8800", bg_color="#102030")
        out = self.get_output()

        self.assertIn("\033[38;2;255;136;0;48;2;16;32;48m", out)

    def test_rgb_foreground_and_background_colors(self):
        """测试 RGB 元组前景色和背景色"""
        myprintx.print("Custom", fg_color=(1, 2, 3), bg_color=(4, 5, 6))
        out = self.get_output()

        self.assertIn("\033[38;2;1;2;3;48;2;4;5;6m", out)

    def test_extended_named_colors(self):
        """测试常用内置颜色名"""
        expected_codes = {
            "magenta": "35",
            "orange": "38;2;255;165;0",
            "pink": "38;2;255;192;203",
            "gray": "38;2;128;128;128",
            "grey": "38;2;128;128;128",
            "brown": "38;2;165;42;42",
            "lime": "38;2;0;255;0",
            "teal": "38;2;0;128;128",
            "navy": "38;2;0;0;128",
            "gold": "38;2;255;215;0",
            "violet": "38;2;238;130;238",
            "indigo": "38;2;75;0;130",
        }
        for color, code in expected_codes.items():
            with self.subTest(color=color):
                output = io.StringIO()
                myprintx.print("Named", fg_color=color, file=output)
                self.assertIn(f"\033[{code}m", output.getvalue())

        output = io.StringIO()
        myprintx.print("Named background", bg_color="orange", file=output)
        self.assertIn("\033[48;2;255;165;0m", output.getvalue())

    def test_invalid_colors_raise_before_output(self):
        for argument in ("fg_color", "bg_color"):
            for color in ("#-10000", "#+10000", "# 10000", "#１２３４５６", "#GG0000", "#123",
                          "#12345678", "#ff\n000", (-1, 0, 0), (256, 0, 0),
                          (True, 0, 0), (1.5, 0, 0), ("1", 0, 0), (), (1, 2), (1, 2, 3, 4)):
                with self.subTest(argument=argument, color=color):
                    output = io.StringIO()
                    with self.assertRaises(ValueError):
                        myprintx.print("BODY", file=output, **{argument: color})
                    self.assertEqual(output.getvalue(), "")
            for color in ([255, 0, 0], 123, False):
                with self.subTest(argument=argument, color=color):
                    with self.assertRaises(TypeError):
                        myprintx.print("BODY", **{argument: color})

    def test_unknown_color_name_keeps_plain_output(self):
        myprintx.print("BODY", fg_color="unknown", bg_color=None)
        self.assertEqual(self.output.getvalue(), "BODY\n")

    def test_none_separator_matches_native_print(self):
        original_print = builtins.print
        for patched in (False, True):
            with self.subTest(patched=patched):
                if patched:
                    myprintx.patch_color()
                output = io.StringIO()
                expected = io.StringIO()
                original_print("a", "b", sep=None, end=None, file=expected)
                printer = builtins.print if patched else myprintx.print
                printer("a", "b", sep=None, end=None, file=output)
                self.assertEqual(output.getvalue(), expected.getvalue())

    def test_falsey_output_object_is_used(self):
        class Sink(io.StringIO):
            def __bool__(self):
                return False

        for patched in (False, True):
            with self.subTest(patched=patched):
                if patched:
                    myprintx.patch_color()
                output = Sink()
                printer = builtins.print if patched else myprintx.print
                printer("BODY", file=output)
                self.assertEqual(output.getvalue(), "BODY\n")
                self.assertEqual(self.output.getvalue(), "")

    def test_patch_log_mirrors_plain_text_and_appends(self):
        """日志应保留终端输出，同时以纯文本追加到指定文件。"""
        with tempfile.TemporaryDirectory() as directory:
            log_path = os.path.join(directory, "nested", "app.log")
            myprintx.patch_log(log_path)
            self.assertTrue(os.path.isdir(os.path.dirname(log_path)))
            myprintx.patch_prefix(
                show_date=False,
                show_time=False,
                custom_prefix="应用",
                show_pid=True,
            )

            myprintx.print("第一条", fg_color="red")
            myprintx.print("第二条", fg_color="green")

            self.assertIn("\033[31m第一条\033[0m", self.output.getvalue())
            self.assertIn("\033[32m第二条\033[0m", self.output.getvalue())
            with open(log_path, encoding="utf-8") as log_file:
                self.assertEqual(
                    log_file.read(),
                    f"[pid={os.getpid()} | 应用] 第一条\n"
                    f"[pid={os.getpid()} | 应用] 第二条\n",
                )

    def test_patch_log_default_path_uses_logs_directory_timestamp_and_pid(self):
        """默认日志应放入日志会话目录，文件名包含 PPID 和 PID。"""
        with tempfile.TemporaryDirectory() as directory:
            previous_directory = os.getcwd()
            old_root = os.environ.pop("MYPRINTX_LOG_ROOT", None)
            try:
                os.chdir(directory)
                returned_path = myprintx.patch_log()
                myprintx.print("默认日志")
            finally:
                os.chdir(previous_directory)
                os.environ.pop("MYPRINTX_LOG_ROOT", None)
                if old_root is not None:
                    os.environ["MYPRINTX_LOG_ROOT"] = old_root
            log_directory = os.path.join(directory, "logs")
            self.assertTrue(os.path.isdir(log_directory))
            run_names = os.listdir(log_directory)
            self.assertEqual(len(run_names), 1)
            self.assertRegex(
                run_names[0],
                rf"^\d{{8}}_\d{{6}}_pid{os.getpid()}$",
            )
            run_directory = os.path.join(log_directory, run_names[0])
            log_names = os.listdir(run_directory)
            self.assertEqual(log_names, [f"ppid{os.getppid()}_pid{os.getpid()}.log"])
            log_path = os.path.join(run_directory, log_names[0])
            self.assertEqual(os.path.realpath(returned_path), os.path.realpath(log_path))
            with open(log_path, encoding="utf-8") as log_file:
                self.assertEqual(log_file.read(), "默认日志\n")

    def test_patch_log_rotates_by_size_and_backup_count(self):
        """超过 max_bytes 时应轮转，并且只保留指定数量的备份。"""
        with tempfile.TemporaryDirectory() as directory:
            log_path = os.path.join(directory, "app.log")
            myprintx.patch_log(log_path, max_bytes=7, backup_count=2)

            myprintx.print("111111")
            myprintx.print("222222")
            myprintx.print("333333")

            with open(log_path, encoding="utf-8") as log_file:
                self.assertEqual(log_file.read(), "333333\n")
            with open(f"{log_path}.1", encoding="utf-8") as log_file:
                self.assertEqual(log_file.read(), "222222\n")
            with open(f"{log_path}.2", encoding="utf-8") as log_file:
                self.assertEqual(log_file.read(), "111111\n")

    def test_exception_outputs_traceback_to_terminal_and_plain_log(self):
        """exception() 应使用 error 样式，并把无 ANSI traceback 写入日志。"""
        with tempfile.TemporaryDirectory() as directory:
            log_path = os.path.join(directory, "app.log")
            myprintx.patch_log(log_path)

            try:
                raise RuntimeError("测试异常")
            except RuntimeError:
                myprintx.exception("处理失败")

            terminal_output = self.output.getvalue()
            self.assertIn("\033[1;31m[ERROR] 处理失败", terminal_output)
            self.assertIn("Traceback (most recent call last):", terminal_output)
            self.assertIn("RuntimeError: 测试异常", terminal_output)
            with open(log_path, encoding="utf-8") as log_file:
                log_output = log_file.read()
            self.assertNotIn("\033[", log_output)
            self.assertIn("[ERROR] 处理失败", log_output)
            self.assertIn("RuntimeError: 测试异常", log_output)

    def test_unpatch_log_and_hidden_output_do_not_write(self):
        """关闭日志或关闭总输出后，都不应继续写入文件。"""
        with tempfile.TemporaryDirectory() as directory:
            log_path = os.path.join(directory, "app.log")
            myprintx.patch_log(log_path)
            myprintx.print("保留")
            myprintx.unpatch_log()
            myprintx.print("日志已关闭")
            myprintx.patch_log(log_path)
            myprintx.set_show(False)
            myprintx.print("总开关已关闭")

            with open(log_path, encoding="utf-8") as log_file:
                self.assertEqual(log_file.read(), "保留\n")

    def test_empty_prefix_only_disables_current_prefix(self):
        myprintx.patch_prefix(show_date=False, show_time=False, custom_prefix="AUTO")
        myprintx.print("BODY", prefix="", fg_color="red")
        myprintx.print("NEXT", prefix=None)
        self.assertEqual(self.output.getvalue(), "\033[31mBODY\033[0m\n[AUTO] NEXT\n")

    # ---------- 前缀功能测试 ----------

    def test_patch_prefix_default(self):
        """测试默认前缀（日期+时间）"""
        myprintx.patch_prefix()
        myprintx.print("启动成功")
        out = self.get_output()
        now = datetime.now().strftime("%Y-%m-%d")
        self.assertIn(now, out)
        self.assertIn("启动成功", out)

    def test_patch_prefix_custom(self):
        """测试自定义前缀"""
        myprintx.patch_prefix(custom_prefix="INFO")
        myprintx.print("初始化完成")
        out = self.get_output()
        self.assertIn("INFO", out)
        self.assertIn("初始化完成", out)

    def test_show_pid_true_uses_yellow_segment_and_pipe_separator(self):
        """显式开启时，PID 应作为黄色独立段插入前缀。"""
        myprintx.patch_prefix(
            show_date=False,
            show_time=False,
            custom_prefix="应用",
            show_pid=True,
        )
        myprintx.print("正文")

        self.assertEqual(
            self.output.getvalue(),
            f"[\033[33mpid={os.getpid()}\033[0m | 应用] 正文\n",
        )

    def test_show_pid_none_hides_in_single_process(self):
        """默认自动模式在没有活动子进程时不显示 PID。"""
        myprintx.patch_prefix(
            show_date=False,
            show_time=False,
            custom_prefix="应用",
            show_pid=None,
        )
        myprintx.print("正文")
        self.assertEqual(self.output.getvalue(), "[应用] 正文\n")

    def test_show_pid_none_displays_in_main_and_child_process(self):
        """默认自动模式在 multiprocessing 主、子进程中都显示 PID。"""
        context = multiprocessing.get_context("spawn")
        output_queue = context.Queue()
        ready = context.Event()
        release = context.Event()
        process = context.Process(
            target=_print_prefix_in_child,
            args=(output_queue, ready, release, None),
        )
        process.start()
        self.addCleanup(lambda: process.is_alive() and process.terminate())
        self.assertTrue(ready.wait(5))

        myprintx.patch_prefix(
            show_date=False,
            show_time=False,
            custom_prefix="主进程",
            show_pid=None,
        )
        myprintx.print("正文")
        release.set()
        child_pid, child_output = output_queue.get(timeout=5)
        process.join(5)

        self.assertEqual(process.exitcode, 0)
        self.assertEqual(
            self.output.getvalue(),
            f"[\033[33mpid={os.getpid()}\033[0m | 主进程] 正文\n",
        )
        self.assertEqual(
            child_output,
            f"[\033[33mpid={child_pid}\033[0m | 子进程] 正文\n",
        )

    def test_show_pid_false_hides_in_main_and_child_process(self):
        """显式关闭时，multiprocessing 主、子进程都不显示 PID。"""
        context = multiprocessing.get_context("spawn")
        output_queue = context.Queue()
        ready = context.Event()
        release = context.Event()
        process = context.Process(
            target=_print_prefix_in_child,
            args=(output_queue, ready, release, False),
        )
        process.start()
        self.addCleanup(lambda: process.is_alive() and process.terminate())
        self.assertTrue(ready.wait(5))

        myprintx.patch_prefix(
            show_date=False,
            show_time=False,
            custom_prefix="主进程",
            show_pid=False,
        )
        myprintx.print("正文")
        release.set()
        _, child_output = output_queue.get(timeout=5)
        process.join(5)

        self.assertEqual(process.exitcode, 0)
        self.assertEqual(self.output.getvalue(), "[主进程] 正文\n")
        self.assertEqual(child_output, "[子进程] 正文\n")

    def test_manual_prefix_argument(self):
        """测试手动 prefix 参数（覆盖自动前缀）"""
        myprintx.patch_prefix(custom_prefix="DEBUG")
        myprintx.print("直接指定", prefix="MANUAL")
        out = self.get_output()
        self.assertIn("[MANUAL]", out)
        self.assertNotIn("DEBUG", out)

    def test_manual_colored_prefix_does_not_affect_body(self):
        """手动彩色前缀应在正文开始前重置颜色"""
        myprintx.print("BODY", prefix="\033[31mPREFIX")
        out = self.get_output()

        self.assertIn("[\033[31mPREFIX\033[0m] BODY", out)

    def test_unpatch_prefix(self):
        """测试关闭前缀"""
        myprintx.patch_prefix(custom_prefix="TEST")
        myprintx.unpatch_prefix()
        myprintx.print("关闭前缀")
        out = self.get_output()
        self.assertNotIn("TEST", out)

    def test_prefix_with_location(self):
        """测试前缀中包含位置信息（蓝色）"""
        myprintx.patch_prefix(custom_prefix="TRACE", show_location=True)
        myprintx.print("定位输出")
        out = self.get_output()

        # 🔵 检查是否包含蓝色 ANSI 码 (34m)
        self.assertIn("\033[34m", out)
        # 检查输出包含文件名 + 行号
        self.assertRegex(out, r"[a-zA-Z0-9_.]+\.py:[a-zA-Z0-9_<>]+\(.*\):\d+")
        self.assertIn("test_prefix_with_location()", out)
        # 自定义内容仍然存在
        self.assertIn("TRACE", out)
        self.assertIn("定位输出", out)

    def test_prefix_location_with_global_print_patch(self):
        """全局接管后的普通 print 应定位到真实调用者"""
        myprintx.patch_color()
        myprintx.patch_prefix(custom_prefix="TRACE", show_location=True)
        print("全局定位输出")
        out = self.get_output()
        self.assertIn("test_prefix_location_with_global_print_patch()", out)
        self.assertIn("全局定位输出", out)

    def test_prefix_color_segments(self):
        """测试前缀中不同部分的颜色（绿色时间 + 蓝色位置）"""
        myprintx.patch_prefix(custom_prefix="DEBUG", show_location=True)
        myprintx.print("多彩前缀测试")
        out = self.get_output()

        # 🟢 检查绿色时间 (32m)
        self.assertIn("\033[32m", out)
        # 🔵 检查蓝色位置信息 (34m)
        self.assertIn("\033[34m", out)
        # ⚪ 检查自定义部分保持原色（在绿色和蓝色之间）
        self.assertIn("DEBUG", out)
        self.assertIn("多彩前缀测试", out)

    # ---------- 新增测试：颜色与前缀分离 ----------

    def test_color_does_not_affect_prefix(self):
        """验证正文颜色不会污染前缀部分"""
        myprintx.patch_prefix(show_location=True)
        myprintx.print("系统初始化完成", fg_color="red")

        out = self.get_output()

        # 检查前缀部分颜色（绿色与蓝色）存在
        self.assertIn("\033[32m", out)
        self.assertIn("\033[34m", out)
        # 正文部分应为红色
        self.assertIn("\033[31m", out)
        # 确认前缀颜色没有被红色覆盖（红色出现在后面）
        prefix_index = out.find("\033[32m")
        red_index = out.find("\033[31m")
        self.assertGreater(red_index, prefix_index, "红色应在前缀之后出现")

    # ---------- 快捷日志函数 ----------

    def test_info_output(self):
        """测试 info() 输出为青色"""
        myprintx.patch_prefix(show_location=True)
        myprintx.info("系统启动")
        out = self.get_output()
        self.assertIn("[INFO]", out)
        self.assertIn("\033[36m", out)
        self.assertIn("test_info_output()", out)

    def test_info_keeps_global_print_patch_active(self):
        """快捷日志不应破坏已启用的全局 print patch"""
        original_print = builtins.print
        try:
            myprintx.patch_color()
            myprintx.info("系统启动")

            self.assertIs(builtins.print, myprintx.print)
            self.assertTrue(hasattr(builtins, "__orig_print__"))

            print("后续普通输出")
            self.assertIn("后续普通输出", self.get_output())

            myprintx.unpatch_color()
            self.assertIs(builtins.print, original_print)
        finally:
            builtins.print = original_print
            if hasattr(builtins, "__orig_print__"):
                del builtins.__orig_print__

    def test_warn_output(self):
        """测试 warn() 输出为黄色加粗"""
        myprintx.patch_prefix()
        myprintx.warn("网络异常")
        out = self.get_output()
        self.assertIn("[WARN]", out)
        self.assertRegex(out, r"\033\[[0-9;]*33")  # 黄色 (允许带样式)
        self.assertRegex(out, r"\033\[[0-9;]*1")   # 加粗

    def test_error_output(self):
        """测试 error() 输出为红色加粗"""
        myprintx.patch_prefix()
        myprintx.error("数据库连接失败")
        out = self.get_output()
        self.assertIn("[ERROR]", out)
        self.assertRegex(out, r"\033\[[0-9;]*31")  # 红色 (允许带样式)
        self.assertRegex(out, r"\033\[[0-9;]*1")   # 加粗
    def test_debug_output(self):
        """测试 debug() 输出为白色"""
        myprintx.patch_prefix()
        myprintx.debug("缓存刷新完成")
        out = self.get_output()
        self.assertIn("[DEBUG]", out)
        self.assertIn("\033[37", out)  # 白色

    def test_native_arguments_and_flush(self):
        """比较真实原生输出，检查空参数、分隔符、换行及刷新。"""
        native_print = builtins.print

        class FlushSink(io.StringIO):
            def __init__(self):
                super().__init__()
                self.flush_count = 0

            def flush(self):
                self.flush_count += 1
                super().flush()

        for args, sep, end in (((), " ", "\n"), (("a", 2, None), "|", "!"),
                               ((" a ", "b"), None, None), (("a", "b"), "", "")):
            for patched in (False, True):
                with self.subTest(args=args, sep=sep, end=end, patched=patched):
                    expected, actual = io.StringIO(), FlushSink()
                    native_print(*args, sep=sep, end=end, file=expected)
                    if patched:
                        myprintx.patch_color()
                    printer = builtins.print if patched else myprintx.print
                    printer(*args, sep=sep, end=end, file=actual, flush=True)
                    self.assertEqual(actual.getvalue(), expected.getvalue())
                    self.assertEqual(actual.flush_count, 1)
                    myprintx.unpatch_color()
    def test_color_boundaries_and_legacy_background(self):
        """基础色、大小写、RGB 边界及旧背景写法使用精确输出断言。"""
        cases = (
            ({"fg_color": "BLACK"}, "30"),
            ({"fg_color": "purple", "bg_color": "bg_red"}, "35;41"),
            ({"fg_color": "grey", "bg_color": "NAVY"}, "38;2;128;128;128;48;2;0;0;128"),
            ({"fg_color": "#aBcDeF"}, "38;2;171;205;239"),
            ({"fg_color": (0, 0, 0), "bg_color": (255, 255, 255)},
             "38;2;0;0;0;48;2;255;255;255"),
        )
        for kwargs, code in cases:
            with self.subTest(kwargs=kwargs):
                output = io.StringIO()
                myprintx.print("正文", file=output, **kwargs)
                self.assertEqual(output.getvalue(), f"\033[{code}m正文\033[0m\n")

    def test_prefix_color_style_mode_combinations(self):
        """组合检查完整前缀与正文边界，而非仅查找某个颜色码。"""
        foregrounds = (("red", "31"), ("#FF8800", "38;2;255;136;0"),
                       ((1, 2, 3), "38;2;1;2;3"))
        backgrounds = ((None, None), ("teal", "48;2;0;128;128"),
                       ((4, 5, 6), "48;2;4;5;6"))
        styles = (("bold", "1"), ("italic", "3"), ("underline", "4"))
        modes = ((None, ""), ("info", "[INFO] "), ("warn", "[WARN] "),
                 ("error", "[ERROR] "), ("debug", "[DEBUG] "))
        myprintx.patch_prefix(show_date=False, show_time=False, custom_prefix="应用")
        for patched, fg, bg, style, mode in itertools.product(
                (False, True), foregrounds, backgrounds, styles, modes):
            with self.subTest(patched=patched, fg=fg[0], bg=bg[0], style=style[0], mode=mode[0]):
                if patched:
                    myprintx.patch_color()
                output = io.StringIO()
                printer = builtins.print if patched else myprintx.print
                printer("正文", fg_color=fg[0], bg_color=bg[0], style=style[0],
                        mode=mode[0], file=output)
                codes = ";".join(code for code in (style[1], fg[1], bg[1]) if code)
                self.assertEqual(output.getvalue(),
                                 f"[应用] \033[{codes}m{mode[1]}正文\033[0m\n")
                myprintx.unpatch_color()

    def test_manual_prefix_reset_and_global_config(self):
        """已有重置码不重复添加，手动前缀不改变下一次自动前缀。"""
        myprintx.patch_prefix(show_date=False, show_time=False, custom_prefix="应用")
        for prefix in ("\033[31m任务", "\033[31m任务\033[0m"):
            with self.subTest(prefix=prefix):
                output = io.StringIO()
                myprintx.print("正文", prefix=prefix, bg_color="#102030", file=output)
                myprintx.print("下一条", file=output)
                self.assertEqual(output.getvalue(),
                    "[\033[31m任务\033[0m] \033[48;2;16;32;48m正文\033[0m\n[应用] 下一条\n")

    def test_all_entry_points_report_exact_call_site(self):
        """直接、全局接管和全部快捷函数应报告文件、函数及真实行号。"""
        myprintx.patch_color()
        myprintx.patch_prefix(show_date=False, show_time=False, show_location=True)
        for printer in (myprintx.print, builtins.print, myprintx.info, myprintx.warn,
                        myprintx.error, myprintx.debug):
            with self.subTest(printer=printer.__name__):
                output = io.StringIO()
                line = inspect.currentframe().f_lineno + 1
                printer("正文", file=output)
                location = f"{os.path.basename(__file__)}:test_all_entry_points_report_exact_call_site():{line}"
                self.assertTrue(output.getvalue().startswith(f"[\033[34m{location}\033[0m] "))

    def test_all_helpers_preserve_repeated_patch_and_restore(self):
        """重复接管和快捷日志混用后，仍能输出并恢复原函数。"""
        original = builtins.print
        myprintx.patch_color()
        myprintx.patch_color()
        for helper in (
            myprintx.info,
            myprintx.warn,
            myprintx.error,
            myprintx.exception,
            myprintx.debug,
        ):
            with self.subTest(helper=helper.__name__):
                helper("消息")
                self.assertIs(builtins.print, myprintx.print)
                self.assertIs(builtins.__orig_print__, original)
                output = io.StringIO()
                print("后续", file=output)
                self.assertEqual(output.getvalue(), "后续\n")
        myprintx.unpatch_color()
        myprintx.unpatch_color()
        self.assertIs(builtins.print, original)

    def test_mode_defaults_and_individual_switches(self):
        """全部模式的默认样式及独立开关，覆盖快捷与 mode 两种入口。"""
        cases = (("info", myprintx.info, myprintx.show_info, "36"),
                 ("warn", myprintx.warn, myprintx.show_warn, "1;33"),
                 ("error", myprintx.error, myprintx.show_error, "1;31"),
                 ("debug", myprintx.debug, myprintx.show_debug, "37"))
        for mode, helper, setter, code in cases:
            with self.subTest(mode=mode):
                output = io.StringIO()
                setter(False)
                helper("隐藏", file=output)
                myprintx.print("隐藏", mode=mode.upper(), file=output)
                myprintx.print("普通", file=output)
                self.assertEqual(output.getvalue(), "普通\n")
                setter()
                helper("恢复", file=output)
                myprintx.print("模式", mode=mode.upper(), file=output)
                self.assertEqual(output.getvalue(),
                    f"普通\n\033[{code}m[{mode.upper()}] 恢复\033[0m\n"
                    f"\033[{code}m[{mode.upper()}] 模式\033[0m\n")

    def test_hidden_output_skips_color_validation(self):
        myprintx.patch_color()
        myprintx.set_show(False)
        print("隐藏", fg_color="#invalid")
        myprintx.error("隐藏", bg_color=[])
        self.assertFalse(myprintx.is_show())
        self.assertEqual(self.output.getvalue(), "")
        myprintx.show_debug(False)
        myprintx.set_show(True)
        myprintx.debug("仍然隐藏", fg_color="#invalid")
        self.assertEqual(self.output.getvalue(), "")
        self.assertTrue(myprintx.is_show())

    def test_invalid_mode_has_no_output(self):
        with self.assertRaises(ValueError):
            myprintx.print("正文", mode="unsupported")
        self.assertEqual(self.output.getvalue(), "")

    def test_prefix_configuration_does_not_patch_print(self):
        original = builtins.print
        myprintx.patch_prefix(show_date=False, show_time=False, custom_prefix="应用")
        self.assertIs(builtins.print, original)
        print("原生")
        myprintx.patch_color()
        myprintx.unpatch_prefix()
        self.assertIs(builtins.print, myprintx.print)
        print("无前缀", fg_color="red")
        self.assertEqual(self.output.getvalue(), "原生\n\033[31m无前缀\033[0m\n")

    def test_show_toggle(self):
        """测试 print 输出开关"""
        myprintx.set_show(False)
        myprintx.print("这行不应出现")
        out = self.get_output()
        self.assertEqual(out, "")  # 应无输出

        myprintx.set_show(True)
        myprintx.print("这行应该出现")
        out = self.get_output()
        self.assertIn("这行应该出现", out)



# 运行所有测试
if __name__ == "__main__":
    unittest.main(verbosity=2)
