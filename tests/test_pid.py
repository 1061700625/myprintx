import multiprocessing
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import myprintx


def worker(ready, release, show_pid):
    myprintx.patch_prefix(
        show_date=True,
        show_time=False,
        custom_prefix="子进程",
        show_pid=show_pid,
    )

    ready.set()
    release.wait()
    myprintx.print("子进程输出")
    myprintx.unpatch_prefix()


def run_case(show_pid):
    context = multiprocessing.get_context("spawn")
    ready = context.Event()
    release = context.Event()
    process = context.Process(
        target=worker,
        args=(ready, release, show_pid),
    )
    process.start()
    ready.wait()

    myprintx.patch_prefix(
        show_date=True,
        show_time=False,
        custom_prefix="主进程",
        show_pid=show_pid,
    )

    myprintx.print(f"主进程输出，show_pid={show_pid!r}")
    release.set()
    process.join()

    myprintx.print("子进程结束后的主进程输出")
    myprintx.unpatch_prefix()


if __name__ == "__main__":
    multiprocessing.freeze_support()

    print("\n===== show_pid=None：多进程时自动显示 =====")
    run_case(None)

    print("\n===== show_pid=True：始终显示 =====")
    run_case(True)

    print("\n===== show_pid=False：始终隐藏 =====")
    run_case(False)
