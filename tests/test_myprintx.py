import io
import sys
import builtins
import unittest
import inspect
import itertools
import os
from datetime import datetime
import myprintx


class TestMyPrintX(unittest.TestCase):

    def setUp(self):
        """保存调用环境，每项测试从独立的默认状态开始。"""
        self._state_names = (
            "print", "__orig_print__", "__print_prefix__", "__print_show__",
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
        for helper in (myprintx.info, myprintx.warn, myprintx.error, myprintx.debug):
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
