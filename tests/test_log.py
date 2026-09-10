import os
import re

import myprintx


def main():
    directory = os.getcwd()
    log_directory = os.path.join(directory, "logs")
    print(f"默认日志目录：{log_directory}")

    try:
        # 测试 1：不传路径时，使用 logs/时间戳_pid<PID>.log
        myprintx.patch_log()
        myprintx.patch_prefix(
            show_date=False,
            show_time=False,
            custom_prefix="默认日志",
            show_pid=True,
        )
        myprintx.print("带颜色的内容", fg_color="green")
        myprintx.unpatch_log()
        myprintx.unpatch_prefix()

        log_paths = [
            os.path.join(log_directory, name)
            for name in os.listdir(log_directory)
            if re.fullmatch(rf"\d{{8}}_\d{{6}}_pid{os.getpid()}\.log", name)
        ]
        default_path = max(log_paths, key=os.path.getmtime)
        with open(default_path, encoding="utf-8") as log_file:
            default_content = log_file.read()
        assert "带颜色的内容" in default_content
        assert "\033[" not in default_content

        # 测试 2：指定文件路径，启用全局 print 接管并追加两条内容
        custom_path = os.path.join(log_directory, "app.log")
        previous_content = ""
        if os.path.exists(custom_path):
            with open(custom_path, encoding="utf-8") as log_file:
                previous_content = log_file.read()

        myprintx.patch_color()
        myprintx.patch_log(custom_path)
        print("第一条", fg_color="red")
        print("第二条", fg_color="cyan")
        myprintx.unpatch_log()

        # 日志关闭后仍输出到终端，但不再写文件
        print("日志已关闭")

        # 总开关关闭后，终端和日志都不输出
        myprintx.patch_log(custom_path)
        myprintx.set_show(False)
        print("这条不会输出")
        myprintx.set_show(True)
        myprintx.unpatch_log()
        myprintx.unpatch_color()

        with open(custom_path, encoding="utf-8") as log_file:
            custom_content = log_file.read()
        assert custom_content == previous_content + "第一条\n第二条\n"
    finally:
        myprintx.set_show(True)
        myprintx.unpatch_log()
        myprintx.unpatch_prefix()
        myprintx.unpatch_color()

    print(f"默认日志文件：{default_path}")
    print(f"指定日志文件：{custom_path}")
    print("日志功能测试通过")


if __name__ == "__main__":
    main()
