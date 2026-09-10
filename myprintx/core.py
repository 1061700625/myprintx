import sys, os, builtins
from datetime import datetime
import inspect
import multiprocessing
import re

_ANSI_ESCAPE_RE = re.compile(r"\033\[[0-9;]*m")

_ANSI_COLORS = {
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "purple": 35,
    "magenta": 35,
    "cyan": 36,
    "white": 37,
}

_NAMED_RGB_COLORS = {
    "orange": (255, 165, 0),
    "pink": (255, 192, 203),
    "gray": (128, 128, 128),
    "grey": (128, 128, 128),
    "brown": (165, 42, 42),
    "lime": (0, 255, 0),
    "teal": (0, 128, 128),
    "navy": (0, 0, 128),
    "gold": (255, 215, 0),
    "violet": (238, 130, 238),
    "indigo": (75, 0, 130),
}

# 全局开关：是否显示 print 输出
builtins.__print_show__ = True
builtins.__show_debug__ = True
builtins.__show_info__ = True
builtins.__show_warn__ = True
builtins.__show_error__ = True


def _color_code(color, background=False):
    if color is None:
        return None
    if isinstance(color, tuple):
        if (
            len(color) != 3
            or any(isinstance(value, bool) or not isinstance(value, int) for value in color)
            or any(value < 0 or value > 255 for value in color)
        ):
            raise ValueError("RGB color must contain three integers from 0 to 255")
        channel = 48 if background else 38
        return f"{channel};2;{color[0]};{color[1]};{color[2]}"

    if not isinstance(color, str):
        raise TypeError("Color must be a name, #RRGGBB string, RGB tuple, or None")

    name = color.lower()
    explicit_background = name.startswith("bg_")
    if explicit_background:
        name = name[3:]
    use_background = background or explicit_background

    if name in _ANSI_COLORS:
        code = _ANSI_COLORS[name]
        return str(code + 10 if use_background else code)

    if name.startswith("#"):
        if len(name) != 7 or any(char not in "0123456789abcdef" for char in name[1:]):
            raise ValueError("Hex color must use #RRGGBB format")
        rgb = tuple(int(name[index:index + 2], 16) for index in (1, 3, 5))
    else:
        rgb = _NAMED_RGB_COLORS.get(name)

    if rgb is None:
        return None

    channel = 48 if use_background else 38
    return f"{channel};2;{rgb[0]};{rgb[1]};{rgb[2]}"


def print(
    *args,
    sep=' ',
    end='\n',
    file=None,
    flush=False,
    fg_color=None,
    bg_color=None,
    style=None,
    prefix=None,
    mode=None,
):
    # 是否允许打印
    if hasattr(builtins, "__print_show__") and not builtins.__print_show__:
        return
    """增强版 print，支持颜色、样式、前缀、位置信息"""
    if sys.platform == "win32":
        os.system("")
    
    if mode:
        mode = str(mode).lower()
        if mode == "debug" and not getattr(builtins, "__show_debug__", True): return
        if mode == "info" and not getattr(builtins, "__show_info__", True): return
        if mode == "warn" and not getattr(builtins, "__show_warn__", True): return
        if mode == "error" and not getattr(builtins, "__show_error__", True): return
        mode_map = {
            "info":  ("[INFO]",  "cyan",   None),
            "warn":  ("[WARN]",  "yellow", "bold"),
            "error": ("[ERROR]", "red",    "bold"),
            "debug": ("[DEBUG]", "white",  None),
        }
        if mode not in mode_map: raise ValueError(f"Unknown print mode: {mode}")
        tag, default_fg, default_style = mode_map[mode]
        args = (tag, *args)
        if fg_color is None and default_fg: fg_color = default_fg
        if style is None and default_style: style = default_style

    style_map = {'bold': 1, 'underline': 4, 'italic': 3}

    codes = []
    if style and style in style_map:
        codes.append(str(style_map[style]))
    fg_code = _color_code(fg_color)
    if fg_code:
        codes.append(fg_code)
    bg_code = _color_code(bg_color, background=True)
    if bg_code:
        codes.append(bg_code)

    prefix_code = f"\033[{';'.join(codes)}m" if codes else ''
    suffix_code = "\033[0m" if codes else ''

    if sep is None:
        sep = ' '
    text = sep.join(map(str, args))

    # ---------- 彩色前缀逻辑 ----------
    prefix_text = ""
    if prefix is None and hasattr(builtins, "__print_prefix__") and builtins.__print_prefix__:
        cfg = builtins.__print_prefix__
        parts = []

        # 🟢 日期 + 时间（绿色）
        green = "\033[32m"
        blue = "\033[34m"
        yellow = "\033[33m"
        reset = "\033[0m"

        dt_parts = []
        if cfg.get("show_date", True):
            dt_parts.append(datetime.now().strftime("%Y-%m-%d"))
        if cfg.get("show_time", True):
            dt_parts.append(datetime.now().strftime("%H:%M:%S"))
        if dt_parts:
            parts.append(f"{green}{' '.join(dt_parts)}{reset}")

        show_pid = cfg.get("show_pid")
        if show_pid is None:
            parent_process = getattr(multiprocessing, "parent_process", None)
            is_child_process = (
                parent_process() is not None
                if parent_process
                else multiprocessing.current_process().name != "MainProcess"
            )
            show_pid = is_child_process or bool(multiprocessing.active_children())
        if show_pid:
            parts.append(f"{yellow}pid={os.getpid()}{reset}")

        # ⚪ 自定义前缀（默认颜色）
        if cfg.get("custom_prefix"):
            parts.append(str(cfg["custom_prefix"]))

        # 🔵 位置信息（蓝色）
        if cfg.get("show_location", False):
            frame = inspect.currentframe()
            try:
                caller = frame.f_back if frame else None
                while caller and caller.f_globals.get("__name__") == __name__:
                    caller = caller.f_back
                if caller:
                    file_name = os.path.basename(caller.f_code.co_filename)
                    func_name = caller.f_code.co_name
                    line_no = caller.f_lineno
                    parts.append(f"{blue}{file_name}:{func_name}():{line_no}{reset}")
            finally:
                del frame

        prefix_text = " | ".join(parts)

    # 手动 prefix 参数优先
    if prefix is not None: prefix_text = str(prefix)
    # 分离前缀和正文的颜色区域
    if prefix_text:
        # 自动前缀的彩色段已自行重置；仅为手动 ANSI 前缀补重置码
        prefix_reset = (
            "\033[0m"
            if prefix is not None and "\033[" in prefix_text and not prefix_text.endswith("\033[0m")
            else ""
        )
        text = f"[{prefix_text}{prefix_reset}] {prefix_code}{text}{suffix_code}"
    else:
        # 没有前缀时，正常加色
        text = f"{prefix_code}{text}{suffix_code}"

    output = text



    native_print = getattr(builtins, "__orig_print__", builtins.print)
    native_print(output, sep=sep, end=end, file=file, flush=flush)

    log_path = getattr(builtins, "__print_log__", None)
    if log_path:
        with open(log_path, "a", encoding="utf-8") as log_file:
            native_print(
                _ANSI_ESCAPE_RE.sub("", output),
                sep=sep,
                end=end,
                file=log_file,
                flush=flush,
            )


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


def patch_log(file_path=None):
    """开启日志文件记录；默认在当前目录的 logs 中按时间和 PID 命名。"""
    if file_path is None:
        file_name = datetime.now().strftime(f"%Y%m%d_%H%M%S_pid{os.getpid()}.log")
        file_path = os.path.join("logs", file_name)
    log_path = os.path.abspath(os.fspath(file_path))
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    builtins.__print_log__ = log_path


def unpatch_log():
    """关闭日志文件记录。"""
    if hasattr(builtins, "__print_log__"):
        del builtins.__print_log__


def patch_prefix(show_date=True, show_time=True, custom_prefix=None, show_location=False, show_pid=None):
    """
    启用自动前缀（日期/时间/进程 ID/自定义/位置信息）
    --------------------------------------
    参数：
        show_date: 是否显示日期（默认 True）
        show_time: 是否显示时间（默认 True）
        custom_prefix: 自定义前缀文字（默认 None）
        show_location: 是否显示调用位置（文件、函数、行号，默认 False）
        show_pid: 是否显示进程 ID。None 时仅在 multiprocessing 多进程中显示
    示例：
        >>> import myprintx
        >>> myprintx.patch_prefix(custom_prefix="INFO", show_location=True)
        >>> print("启动完成")
        [2025-10-14 21:55:07 | INFO | main.py:<module>():8] 启动完成
    """
    builtins.__print_prefix__ = {
        "show_date": show_date,
        "show_time": show_time,
        "custom_prefix": custom_prefix,
        "show_location": show_location,
        "show_pid": show_pid,
    }


def unpatch_prefix():
    """
    关闭自动前缀功能
    ----------------
    """
    if hasattr(builtins, "__print_prefix__"):
        del builtins.__print_prefix__
     

def info(*args, **kwargs):
    """信息输出（蓝色）"""
    kwargs.setdefault("mode", "info")
    print(*args, **kwargs)

def warn(*args, **kwargs):
    """警告输出（黄色加粗）"""
    kwargs.setdefault("mode", "warn")
    print(*args, **kwargs)

def error(*args, **kwargs):
    """错误输出（红色加粗）"""
    kwargs.setdefault("mode", "error")
    print(*args, **kwargs)

def debug(*args, **kwargs):
    """调试输出（青色）"""
    kwargs.setdefault("mode", "debug")
    print(*args, **kwargs)


def show_debug(enable: bool=True): builtins.__show_debug__ = bool(enable)
def show_info(enable: bool=True): builtins.__show_info__   = bool(enable)
def show_warn(enable: bool=True): builtins.__show_warn__   = bool(enable)
def show_error(enable: bool=True): builtins.__show_error__ = bool(enable)

def set_show(enable: bool):
    """设置是否显示 print 输出，总开关。可用于开发环境正常输出，生产环境屏蔽输出，包括所有的mode"""
    builtins.__print_show__ = bool(enable)

def is_show() -> bool:
    """返回当前 print 显示状态"""
    return getattr(builtins, "__print_show__", True)

