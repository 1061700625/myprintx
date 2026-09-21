import builtins
import io
import json
import os
import tempfile
import unittest

import myprintx


class PrintFormatTest(unittest.TestCase):
    def setUp(self):
        self._original_print = builtins.print
        self._had_orig_print = hasattr(builtins, "__orig_print__")
        self._saved_orig_print = getattr(builtins, "__orig_print__", None)
        myprintx.unpatch_color()
        myprintx.unpatch_log()
        myprintx.set_show(True)

    def tearDown(self):
        myprintx.unpatch_log()
        myprintx.unpatch_color()
        builtins.print = self._original_print
        if self._had_orig_print:
            builtins.__orig_print__ = self._saved_orig_print
        elif hasattr(builtins, "__orig_print__"):
            del builtins.__orig_print__

    def test_json_format_pretty_prints_python_object(self):
        output = io.StringIO()
        value = {"name": "测试", "items": [1, 2]}

        myprintx.print(value, format="json", file=output)

        expected = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
        self.assertEqual(output.getvalue(), expected)

    def test_json_format_pretty_prints_json_string(self):
        output = io.StringIO()

        myprintx.print('{"name":"demo","items":[1,2]}', format="JSON", file=output)

        self.assertEqual(
            output.getvalue(),
            '{\n  "name": "demo",\n  "items": [\n    1,\n    2\n  ]\n}\n',
        )

    def test_json_format_keeps_plain_string(self):
        output = io.StringIO()

        myprintx.print("plain text", format="json", file=output)

        self.assertEqual(output.getvalue(), "plain text\n")

    def test_list_format_pretty_prints_list(self):
        output = io.StringIO()

        myprintx.print([1, "two", {"three": 3}], format="list", file=output)

        self.assertEqual(
            output.getvalue(),
            "[\n  1,\n  'two',\n  {'three': 3}\n]\n",
        )

    def test_list_format_pretty_prints_tuple(self):
        output = io.StringIO()

        myprintx.print((1, 2), format="LIST", file=output)

        self.assertEqual(output.getvalue(), "(\n  1,\n  2\n)\n")

    def test_list_format_keeps_non_list_argument(self):
        output = io.StringIO()

        myprintx.print("label", [1, 2], format="list", file=output)

        self.assertEqual(output.getvalue(), "label [\n  1,\n  2\n]\n")

    def test_unknown_format_raises_before_output(self):
        output = io.StringIO()

        with self.assertRaises(ValueError):
            myprintx.print({"a": 1}, format="yaml", file=output)

        self.assertEqual(output.getvalue(), "")

    def test_format_works_with_color_and_prefix(self):
        output = io.StringIO()

        myprintx.print(
            {"a": 1},
            format="json",
            fg_color="green",
            prefix="DATA",
            file=output,
        )

        self.assertEqual(
            output.getvalue(),
            "[DATA] \x1b[32m{\n  \"a\": 1\n}\x1b[0m\n",
        )

    def test_format_is_mirrored_to_log_without_ansi(self):
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as directory:
            log_path = os.path.join(directory, "app.log")
            myprintx.patch_log(log_path)
            myprintx.print({"a": [1, 2]}, format="json", fg_color="cyan", file=output)
            myprintx.unpatch_log()

            self.assertIn("\x1b[36m", output.getvalue())
            with open(log_path, encoding="utf-8") as log_file:
                self.assertEqual(
                    log_file.read(),
                    '{\n  "a": [\n    1,\n    2\n  ]\n}\n',
                )

    def test_patched_builtin_print_supports_format(self):
        output = io.StringIO()
        myprintx.patch_color()

        print([1, 2], format="list", file=output)

        self.assertEqual(output.getvalue(), "[\n  1,\n  2\n]\n")


if __name__ == "__main__":
    unittest.main()
