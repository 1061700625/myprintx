import multiprocessing
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import myprintx


_LOG_ROOT_ENV = "MYPRINTX_LOG_ROOT"


def _worker_patch_log(workdir, queue, suffix=None):
    os.chdir(workdir)
    path = myprintx.patch_log(suffix=suffix)
    message = f"child pid={os.getpid()}"
    myprintx.print(message)
    myprintx.unpatch_log()
    with open(path, encoding="utf-8") as log_file:
        content = log_file.read()
    queue.put((os.getpid(), os.getppid(), path, os.environ.get(_LOG_ROOT_ENV), message, content))


def _worker_spawn_grandchild(workdir, queue):
    os.chdir(workdir)
    path = myprintx.patch_log()
    queue.put(("child", os.getpid(), os.getppid(), path, os.environ.get(_LOG_ROOT_ENV)))

    ctx = multiprocessing.get_context("spawn")
    grandchild = ctx.Process(target=_grandchild_patch_log, args=(workdir, queue))
    grandchild.start()
    grandchild.join(timeout=10)
    if grandchild.exitcode != 0:
        raise RuntimeError(f"grandchild exit code: {grandchild.exitcode}")
    myprintx.unpatch_log()


def _grandchild_patch_log(workdir, queue):
    os.chdir(workdir)
    path = myprintx.patch_log()
    myprintx.print(f"grandchild pid={os.getpid()}")
    myprintx.unpatch_log()
    queue.put(("grandchild", os.getpid(), os.getppid(), path, os.environ.get(_LOG_ROOT_ENV)))


class LogMultiprocessTest(unittest.TestCase):
    def setUp(self):
        self._old_log_root = os.environ.pop(_LOG_ROOT_ENV, None)
        myprintx.unpatch_log()

    def tearDown(self):
        myprintx.unpatch_log()
        os.environ.pop(_LOG_ROOT_ENV, None)
        if self._old_log_root is not None:
            os.environ[_LOG_ROOT_ENV] = self._old_log_root

    def test_default_path_and_repatch_reuse_same_session(self):
        with tempfile.TemporaryDirectory() as workdir:
            old_cwd = os.getcwd()
            try:
                os.chdir(workdir)
                first_path = myprintx.patch_log()
                myprintx.unpatch_log()
                second_path = myprintx.patch_log()
                myprintx.unpatch_log()
            finally:
                os.chdir(old_cwd)

        self.assertEqual(first_path, second_path)
        self.assertEqual(
            os.path.basename(first_path),
            f"ppid{os.getppid()}_pid{os.getpid()}.log",
        )
        self.assertTrue(
            os.path.basename(os.path.dirname(first_path)).endswith(f"_pid{os.getpid()}")
        )

    def test_explicit_path_does_not_create_log_session(self):
        with tempfile.TemporaryDirectory() as workdir:
            explicit_path = os.path.join(workdir, "app.log")
            returned_path = myprintx.patch_log(explicit_path)
            myprintx.unpatch_log()

        self.assertEqual(returned_path, os.path.abspath(explicit_path))
        self.assertNotIn(_LOG_ROOT_ENV, os.environ)

    def test_default_path_with_suffix(self):
        with tempfile.TemporaryDirectory() as workdir:
            old_cwd = os.getcwd()
            try:
                os.chdir(workdir)
                path = myprintx.patch_log(suffix="p1")
                myprintx.unpatch_log()
            finally:
                os.chdir(old_cwd)

        self.assertEqual(
            os.path.basename(path),
            f"ppid{os.getppid()}_pid{os.getpid()}_p1.log",
        )

    def test_explicit_path_ignores_suffix(self):
        with tempfile.TemporaryDirectory() as workdir:
            explicit_path = os.path.join(workdir, "app.log")
            returned_path = myprintx.patch_log(explicit_path, suffix="p1")
            myprintx.unpatch_log()

        self.assertEqual(returned_path, os.path.abspath(explicit_path))
        self.assertNotIn(_LOG_ROOT_ENV, os.environ)

    def test_invalid_suffix_rejects_path_separator(self):
        with tempfile.TemporaryDirectory() as workdir:
            old_cwd = os.getcwd()
            try:
                os.chdir(workdir)
                with self.assertRaises(ValueError):
                    myprintx.patch_log(suffix="a/b")
                with self.assertRaises(ValueError):
                    myprintx.patch_log(suffix="a\\b")
                self.assertNotIn(_LOG_ROOT_ENV, os.environ)
            finally:
                os.chdir(old_cwd)

    def test_children_can_use_different_suffixes(self):
        ctx = multiprocessing.get_context("spawn")
        with tempfile.TemporaryDirectory() as workdir:
            old_cwd = os.getcwd()
            try:
                os.chdir(workdir)
                parent_path = myprintx.patch_log()
                parent_root = os.path.dirname(parent_path)

                queue = ctx.Queue()
                suffixes = ["p1", "p2"]
                processes = [
                    ctx.Process(target=_worker_patch_log, args=(workdir, queue, suffix))
                    for suffix in suffixes
                ]
                for process in processes:
                    process.start()
                results = [queue.get(timeout=10) for _ in processes]
                for process in processes:
                    process.join(timeout=10)
                    self.assertEqual(process.exitcode, 0)
                myprintx.unpatch_log()
            finally:
                os.chdir(old_cwd)

        names = {os.path.basename(item[2]) for item in results}
        self.assertEqual({os.path.dirname(item[2]) for item in results}, {parent_root})
        self.assertEqual({name.rsplit("_", 1)[-1] for name in names}, {"p1.log", "p2.log"})

    def test_children_share_parent_log_directory(self):
        ctx = multiprocessing.get_context("spawn")
        with tempfile.TemporaryDirectory() as workdir:
            old_cwd = os.getcwd()
            try:
                os.chdir(workdir)
                parent_path = myprintx.patch_log()
                parent_root = os.path.dirname(parent_path)

                queue = ctx.Queue()
                processes = [
                    ctx.Process(target=_worker_patch_log, args=(workdir, queue))
                    for _ in range(2)
                ]
                for process in processes:
                    process.start()
                results = [queue.get(timeout=10) for _ in processes]
                for process in processes:
                    process.join(timeout=10)
                    self.assertEqual(process.exitcode, 0)
                myprintx.unpatch_log()
            finally:
                os.chdir(old_cwd)

        for pid, ppid, child_path, child_root_env, message, content in results:
            self.assertEqual(os.path.dirname(child_path), parent_root)
            self.assertEqual(child_root_env, parent_root)
            self.assertEqual(os.path.basename(child_path), f"ppid{ppid}_pid{pid}.log")
            self.assertIn(message, content)

    def test_grandchild_inherits_same_log_directory(self):
        ctx = multiprocessing.get_context("spawn")
        with tempfile.TemporaryDirectory() as workdir:
            old_cwd = os.getcwd()
            try:
                os.chdir(workdir)
                parent_path = myprintx.patch_log()
                parent_root = os.path.dirname(parent_path)

                queue = ctx.Queue()
                child = ctx.Process(target=_worker_spawn_grandchild, args=(workdir, queue))
                child.start()
                results = [queue.get(timeout=10) for _ in range(2)]
                child.join(timeout=10)
                self.assertEqual(child.exitcode, 0)
                myprintx.unpatch_log()
            finally:
                os.chdir(old_cwd)

        by_role = {item[0]: item for item in results}
        child_result = by_role["child"]
        grandchild_result = by_role["grandchild"]
        self.assertEqual(os.path.dirname(child_result[3]), parent_root)
        self.assertEqual(os.path.dirname(grandchild_result[3]), parent_root)
        self.assertEqual(child_result[4], parent_root)
        self.assertEqual(grandchild_result[4], parent_root)
        self.assertEqual(grandchild_result[2], child_result[1])

    def test_sibling_children_create_separate_sessions_without_parent_patch(self):
        ctx = multiprocessing.get_context("spawn")
        with tempfile.TemporaryDirectory() as workdir:
            queue = ctx.Queue()
            processes = [
                ctx.Process(target=_worker_patch_log, args=(workdir, queue))
                for _ in range(2)
            ]
            for process in processes:
                process.start()
            results = [queue.get(timeout=10) for _ in processes]
            for process in processes:
                process.join(timeout=10)
                self.assertEqual(process.exitcode, 0)

        roots = {os.path.dirname(path) for _, _, path, _, _, _ in results}
        self.assertEqual(len(roots), 2)
        for pid, ppid, child_path, child_root_env, message, content in results:
            self.assertEqual(child_root_env, os.path.dirname(child_path))
            self.assertTrue(
                os.path.basename(os.path.dirname(child_path)).endswith(f"_pid{pid}")
            )
            self.assertEqual(os.path.basename(child_path), f"ppid{ppid}_pid{pid}.log")
            self.assertIn(message, content)


if __name__ == "__main__":
    unittest.main()
