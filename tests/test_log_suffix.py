import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import myprintx


_LOG_ROOT_ENV = "MYPRINTX_LOG_ROOT"


class LogSuffixTest(unittest.TestCase):
    def setUp(self):
        self._old_log_root = os.environ.pop(_LOG_ROOT_ENV, None)
        myprintx.unpatch_log()

    def tearDown(self):
        myprintx.unpatch_log()
        os.environ.pop(_LOG_ROOT_ENV, None)
        if self._old_log_root is not None:
            os.environ[_LOG_ROOT_ENV] = self._old_log_root

    def test_suffix_is_appended_before_log_extension(self):
        with tempfile.TemporaryDirectory() as workdir:
            old_cwd = os.getcwd()
            try:
                os.chdir(workdir)
                path = myprintx.patch_log(suffix="p1")
                myprintx.print("suffix test")
                myprintx.unpatch_log()

                self.assertEqual(
                    os.path.basename(path),
                    f"ppid{os.getppid()}_pid{os.getpid()}_p1.log",
                )
                with open(path, encoding="utf-8") as log_file:
                    self.assertIn("suffix test", log_file.read())
            finally:
                os.chdir(old_cwd)

    def test_numeric_suffix_is_converted_to_string_and_terminal_output_remains(self):
        import io
        from contextlib import redirect_stdout

        with tempfile.TemporaryDirectory() as workdir:
            old_cwd = os.getcwd()
            output = io.StringIO()
            try:
                os.chdir(workdir)
                with redirect_stdout(output):
                    print("a")
                    path = myprintx.patch_log(suffix=1)
                    myprintx.print("b")
                    myprintx.unpatch_log()

                self.assertEqual(output.getvalue(), "a\nb\n")
                self.assertEqual(
                    os.path.basename(path),
                    f"ppid{os.getppid()}_pid{os.getpid()}_1.log",
                )
                with open(path, encoding="utf-8") as log_file:
                    self.assertEqual(log_file.read(), "b\n")
            finally:
                os.chdir(old_cwd)

    def test_empty_suffix_keeps_default_filename(self):
        with tempfile.TemporaryDirectory() as workdir:
            old_cwd = os.getcwd()
            try:
                os.chdir(workdir)
                path = myprintx.patch_log(suffix="")
                myprintx.unpatch_log()
            finally:
                os.chdir(old_cwd)

        self.assertEqual(
            os.path.basename(path),
            f"ppid{os.getppid()}_pid{os.getpid()}.log",
        )

    def test_suffix_does_not_persist_between_patch_calls(self):
        with tempfile.TemporaryDirectory() as workdir:
            old_cwd = os.getcwd()
            try:
                os.chdir(workdir)
                first_path = myprintx.patch_log(suffix="p1")
                myprintx.unpatch_log()
                second_path = myprintx.patch_log(suffix="p2")
                myprintx.unpatch_log()
                third_path = myprintx.patch_log()
                myprintx.unpatch_log()
            finally:
                os.chdir(old_cwd)

        self.assertEqual(os.path.dirname(first_path), os.path.dirname(second_path))
        self.assertEqual(os.path.dirname(first_path), os.path.dirname(third_path))
        self.assertTrue(first_path.endswith("_p1.log"))
        self.assertTrue(second_path.endswith("_p2.log"))
        self.assertEqual(
            os.path.basename(third_path),
            f"ppid{os.getppid()}_pid{os.getpid()}.log",
        )

    def test_explicit_path_is_not_modified_by_suffix(self):
        with tempfile.TemporaryDirectory() as workdir:
            explicit_path = os.path.join(workdir, "app.log")
            returned_path = myprintx.patch_log(explicit_path, suffix="p1")
            myprintx.unpatch_log()

        self.assertEqual(returned_path, os.path.abspath(explicit_path))
        self.assertNotIn(_LOG_ROOT_ENV, os.environ)

    def test_invalid_suffix_is_rejected_before_session_creation(self):
        with tempfile.TemporaryDirectory() as workdir:
            old_cwd = os.getcwd()
            try:
                os.chdir(workdir)
                for suffix in ("a/b", "a\\b", "a\x00b"):
                    with self.subTest(suffix=repr(suffix)):
                        with self.assertRaises(ValueError):
                            myprintx.patch_log(suffix=suffix)
                self.assertNotIn(_LOG_ROOT_ENV, os.environ)
            finally:
                os.chdir(old_cwd)


if __name__ == "__main__":
    unittest.main()
