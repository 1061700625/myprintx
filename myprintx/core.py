import sys, os, builtins

def print(
    *args,
    sep=' ',
    end='\n',
    file=None,
    flush=False,
    fg_color=None,
    bg_color=None,
    style=None
):
    """
    myprintx.print() —— 彩色与样式增强版 print
    ==========================================
    参数：
        fg_color: 前景色 ['black','red','green','yellow','blue','purple','cyan','white']
        bg_color: 背景色（可加 'bg_' 前缀）
        style: 字体样式 ['bold','underline','italic']
    示例：
        print("成功", fg_color="green", style="bold")
        print("错误", fg_color="white", bg_color="red")
    """

    # 启用 Windows 终端颜色支持
    if sys.platform == "win32":
        os.system("")

    # ANSI 颜色映射表
    color_map = {
        # 前景色
        'black': 30, 'red': 31, 'green': 32, 'yellow': 33,
        'blue': 34, 'purple': 35, 'cyan': 36, 'white': 37,
        # 背景色
        'bg_black': 40, 'bg_red': 41, 'bg_green': 42, 'bg_yellow': 43,
        'bg_blue': 44, 'bg_purple': 45, 'bg_cyan': 46, 'bg_white': 47
    }

    # 样式映射表
    style_map = {
        'bold': 1,
        'underline': 4,
        'italic': 3
    }

    codes = []

    # 添加样式控制码
    if style and style in style_map:
        codes.append(str(style_map[style]))

    # 添加前景色控制码
    if fg_color:
        if fg_color in color_map:
            codes.append(str(color_map[fg_color]))
        elif f"fg_{fg_color}" in color_map:
            codes.append(str(color_map[f"fg_{fg_color}"]))

    # 添加背景色控制码
    if bg_color:
        bg_key = bg_color if bg_color.startswith("bg_") else f"bg_{bg_color}"
        if bg_key in color_map:
            codes.append(str(color_map[bg_key]))

    prefix = f"\033[{';'.join(codes)}m" if codes else ''
    suffix = "\033[0m" if codes else ''

    text = sep.join(map(str, args))
    output = f"{prefix}{text}{suffix}"

    # 安全调用原始 print（避免递归，同时兼容未打补丁的情况）
    if hasattr(builtins, "__orig_print__"):
        builtins.__orig_print__(output, sep=sep, end=end, file=file or sys.stdout, flush=flush)
    else:
        builtins.print(output, sep=sep, end=end, file=file or sys.stdout, flush=flush)



def patch_color():
    """
    自动为全局 print() 启用彩色增强功能
    -------------------------------------
    调用后，系统内所有 print() 均支持：
        fg_color / bg_color / style 参数。

    示例：
        >>> import myprintx
        >>> myprintx.auto_patch_color()
        >>> print("绿色文字", fg_color="green", style="bold")

    可随时通过 myprintx.unpatch() 恢复原始 print。
    """
    if not hasattr(builtins, "__orig_print__"):
        builtins.__orig_print__ = builtins.print
    builtins.print = print


def unpatch_color():
    """
    恢复原始 print()（撤销所有增强）
    --------------------------------
    若之前执行过 auto_patch_color()，可使用该函数恢复。
    """
    if hasattr(builtins, "__orig_print__"):
        builtins.print = builtins.__orig_print__
        del builtins.__orig_print__
