import io
import sys
import builtins
import unittest
from datetime import datetime
import myprintx


class TestMyPrintX(unittest.TestCase):

    def setUp(self):
        """在每个测试前重定向 stdout"""
        self.output = io.StringIO()
        self._stdout = sys.stdout
        sys.stdout = self.output

    def tearDown(self):
        """测试后恢复原状"""
        sys.stdout = self._stdout
        if hasattr(builtins, "__orig_print__"):
            myprintx.unpatch_color()
        if hasattr(builtins, "__print_prefix__"):
            myprintx.unpatch_prefix()

    def get_output(self):
        """返回打印输出（不自动清除 ANSI）"""
        return self.output.getvalue().strip()

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
        # 自定义内容仍然存在
        self.assertIn("TRACE", out)
        self.assertIn("定位输出", out)

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

# python -m unittest discover -s tests -v
if __name__ == "__main__":
    unittest.main(verbosity=2)
