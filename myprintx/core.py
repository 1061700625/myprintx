import sys, os, builtins
from datetime import datetime
import inspect
# 全局开关：是否显示 print 输出
builtins.__print_show__ = True

def print(
    *args,
    sep=' ',
    end='\n',
    file=None,
    flush=False,
    fg_color=None,
    bg_color=None,
    style=None,
    prefix=None
):
    # 是否允许打印
    if hasattr(builtins, "__print_show__") and not builtins.__print_show__:
        return
    """增强版 print，支持颜色、样式、前缀、位置信息"""
    if sys.platform == "win32":
        os.system("")

    # ANSI 颜色映射表
    color_map = {
        'black': 30, 'red': 31, 'green': 32, 'yellow': 33,
        'blue': 34, 'purple': 35, 'cyan': 36, 'white': 37,
        'bg_black': 40, 'bg_red': 41, 'bg_green': 42, 'bg_yellow': 43,
        'bg_blue': 44, 'bg_purple': 45, 'bg_cyan': 46, 'bg_white': 47
    }
    style_map = {'bold': 1, 'underline': 4, 'italic': 3}

    codes = []
    if style and style in style_map:
        codes.append(str(style_map[style]))
    if fg_color and fg_color in color_map:
        codes.append(str(color_map[fg_color]))
    if bg_color:
        bg_key = bg_color if bg_color.startswith("bg_") else f"bg_{bg_color}"
        if bg_key in color_map:
            codes.append(str(color_map[bg_key]))

    prefix_code = f"\033[{';'.join(codes)}m" if codes else ''
    suffix_code = "\033[0m" if codes else ''

    text = sep.join(map(str, args))

    # ---------- 彩色前缀逻辑 ----------
    prefix_text = ""
    if hasattr(builtins, "__print_prefix__") and builtins.__print_prefix__:
        cfg = builtins.__print_prefix__
        parts = []

        # 🟢 日期 + 时间（绿色）
        green = "\033[32m"
        blue = "\033[34m"
        reset = "\033[0m"

        dt_parts = []
        if cfg.get("show_date", True):
            dt_parts.append(datetime.now().strftime("%Y-%m-%d"))
        if cfg.get("show_time", True):
            dt_parts.append(datetime.now().strftime("%H:%M:%S"))
        if dt_parts:
            parts.append(f"{green}{' '.join(dt_parts)}{reset}")

        # ⚪ 自定义前缀（默认颜色）
        if cfg.get("custom_prefix"):
            parts.append(str(cfg["custom_prefix"]))

        # 🔵 位置信息（蓝色）
        if cfg.get("show_location", False):
            frame = inspect.currentframe()
            caller = frame.f_back.f_back if frame and frame.f_back else None
            if caller:
                file_name = os.path.basename(caller.f_code.co_filename)
                func_name = caller.f_code.co_name
                line_no = caller.f_lineno
                parts.append(f"{blue}{file_name}:{func_name}():{line_no}{reset}")

        prefix_text = " ".join(parts)

    # 手动 prefix 参数优先
    if prefix: prefix_text = str(prefix)
    # 分离前缀和正文的颜色区域
    if prefix_text:
        # 保持前缀原有颜色（由 patch_prefix 内部定义）
        text = f"[{prefix_text}] {prefix_code}{text}{suffix_code}"
    else:
        # 没有前缀时，正常加色
        text = f"{prefix_code}{text}{suffix_code}"

    output = text



    if hasattr(builtins, "__orig_print__"):
        builtins.__orig_print__(output, sep=sep, end=end, file=file or sys.stdout, flush=flush)
    else:
        builtins.print(output, sep=sep, end=end, file=file or sys.stdout, flush=flush)


def patch_color():
    """启用彩色增强"""
    if not hasattr(builtins, "__orig_print__"):
        builtins.__orig_print__ = builtins.print
    builtins.print = print


def unpatch_color():
    """恢复原始 print()"""
    if hasattr(builtins, "__orig_print__"):
        builtins.print = builtins.__orig_print__
        del builtins.__orig_print__


def patch_prefix(show_date=True, show_time=True, custom_prefix=None, show_location=False):
    """
    启用自动前缀（日期/时间/自定义/位置信息）
    --------------------------------------
    参数：
        show_date: 是否显示日期（默认 True）
        show_time: 是否显示时间（默认 True）
        custom_prefix: 自定义前缀文字（默认 None）
        show_location: 是否显示调用位置（文件、函数、行号，默认 False）
    示例：
        >>> import myprintx
        >>> myprintx.patch_prefix(custom_prefix="INFO", show_location=True)
        >>> print("启动完成")
        [2025-10-14 21:55:07 INFO main.py:<module>():8] 启动完成
    """
    builtins.__print_prefix__ = {
        "show_date": show_date,
        "show_time": show_time,
        "custom_prefix": custom_prefix,
        "show_location": show_location
    }


def unpatch_prefix():
    """
    关闭自动前缀功能
    ----------------
    """
    if hasattr(builtins, "__print_prefix__"):
        del builtins.__print_prefix__
     

def _with_temp_color(func):
    """装饰器：在调用前启用 patch_color()，调用后恢复"""
    def wrapper(*args, **kwargs):
        # 保存当前 print
        orig_print = builtins.print
        try:
            # 临时启用彩色打印
            patch_color()
            return func(*args, **kwargs)
        finally:
            # 恢复原始 print
            unpatch_color()
            builtins.print = orig_print
    return wrapper

@_with_temp_color
def info(*args, **kwargs):
    """信息输出（蓝色）"""
    print("[INFO]", *args, fg_color="cyan", **kwargs)

@_with_temp_color
def warn(*args, **kwargs):
    """警告输出（黄色加粗）"""
    print("[WARN]", *args, fg_color="yellow", style="bold", **kwargs)

@_with_temp_color
def error(*args, **kwargs):
    """错误输出（红色加粗）"""
    print("[ERROR]", *args, fg_color="red", style="bold", **kwargs)

@_with_temp_color
def debug(*args, **kwargs):
    """调试输出（青色）"""
    print("[DEBUG]", *args, fg_color="white", **kwargs)


def set_show(enable: bool):
    """设置是否显示 print 输出。可用于开发环境正常输出，生产环境屏蔽输出"""
    builtins.__print_show__ = bool(enable)

def is_show() -> bool:
    """返回当前 print 显示状态"""
    return getattr(builtins, "__print_show__", True)

