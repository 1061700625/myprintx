import multiprocessing
import os
import sys


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import myprintx


PROCESS_COUNT = 4
LINES_PER_PROCESS = 10_000
COLORS = ("cyan", "green", "yellow", "magenta")


def worker(worker_id):
    myprintx.patch_color()
    myprintx.patch_prefix(
        show_date=False,
        show_time=True,
        custom_prefix=f"worker-{worker_id}",
        show_pid=True,
    )
    log_path = myprintx.patch_log()

    for line_number in range(1, LINES_PER_PROCESS + 1):
        print(
            f"第 {line_number:05d}/{LINES_PER_PROCESS} 条",
            fg_color=COLORS[worker_id],
        )

    myprintx.unpatch_log()
    return os.getpid(), log_path


def main():
    context = multiprocessing.get_context("spawn")
    pool = context.Pool(PROCESS_COUNT)
    result = pool.map_async(worker, range(PROCESS_COUNT))

    print(f"4 个进程将分别输出 {LINES_PER_PROCESS} 条，共 {PROCESS_COUNT * LINES_PER_PROCESS} 条。")
    print(f"日志目录：{os.path.abspath('logs')}")
    print("按 Ctrl+C 可随时停止。")

    try:
        log_files = result.get()
    except KeyboardInterrupt:
        print("\n收到 Ctrl+C，正在终止进程池……")
        pool.terminate()
        pool.join()
        print(f"已停止，已写入的日志保留在：{os.path.abspath('logs')}")
        return 130

    pool.close()
    pool.join()

    print("\n全部输出完成：")
    for pid, log_path in log_files:
        print(f"pid={pid} | {log_path}")
    return 0


if __name__ == "__main__":
    multiprocessing.freeze_support()
    raise SystemExit(main())
