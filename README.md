# myprintx 🎨

一个轻量级 Python 库，为内置 `print()` 提供颜色、样式和前缀增强。

## 功能

* ✅ 彩色输出 — 支持前景色、背景色、内置颜色名、RGB 和十六进制颜色

* ✅ 文本样式 — 支持加粗、斜体和下划线

* ✅ 常用参数 — 支持 `sep`、`end`、`file` 和 `flush`

* ✅ 格式化输出 — `format="json"` 美化 JSON，`format="list"` 美化列表/元组，`format="auto"` 自动判断类型

* ✅ 全局接管 — 一行启用，让后续普通 `print()` 使用增强功能

* ✅ 自动前缀 — 显示日期、时间、进程 ID、自定义标签和调用位置

* ✅ 日志副本 — 保留终端输出，并同步追加一份纯文本日志

* ✅ 快捷输出 — 内置 `info()`、`warn()`、`error()`、`exception()`、`debug()`

* ✅ 运行计时 — 支持上下文管理器、手动开始/结束和函数装饰器

## 安装

    pip install myprintx

> 🧩 无额外运行时依赖
## 用法

    # 基本用法
    import myprintx

    myprintx.print("普通输出")
    myprintx.print("成功", fg_color="green", style="bold")
    myprintx.print("警告", fg_color="yellow", style="underline")
    myprintx.print("提示", style="italic")
    myprintx.print("错误", fg_color="white", bg_color="red")

    # 更多颜色
    myprintx.print("橙色", fg_color="orange")
    myprintx.print("十六进制颜色", fg_color="#FF8800")
    myprintx.print("RGB 颜色", fg_color=(255, 136, 0))
    myprintx.print("自定义背景", fg_color="white", bg_color=(16, 32, 48))

    # 格式化输出
    myprintx.print({"name": "demo", "items": [1, 2]}, format="json")
    myprintx.print('{"name":"demo","items":[1,2]}', format="json")
    myprintx.print(["apple", "banana", {"count": 2}], format="list")
    myprintx.print({"name": "demo", "items": [1, 2]}, format="auto")  # dict 自动按 JSON 美化
    myprintx.print(["apple", "banana"], format="auto")                 # list 自动按列表美化

    # 启用彩色全局打印
    myprintx.patch_color()
    print("绿色输出", fg_color="green", style="bold")
    print("错误输出", fg_color="white", bg_color="red")
    myprintx.info("快捷函数不会取消全局接管")
    print("继续使用增强打印", fg_color="orange")
    myprintx.unpatch_color()  # 恢复接管前的 print()

    # 启用前缀打印
    myprintx.patch_prefix(custom_prefix="应用", show_location=True)
    myprintx.print("启动成功", fg_color="green")
    myprintx.print("任务执行中", fg_color="cyan")
    myprintx.print("临时标签", prefix="任务", fg_color="#FF8800")
    myprintx.print("本次不显示前缀", prefix="", fg_color="orange")
    myprintx.print("继续使用自动前缀")
    myprintx.unpatch_prefix()  # 关闭自动前缀

    # 同步保存纯文本日志
    log_path = myprintx.patch_log(  # 返回日志的绝对路径
        max_bytes=10 * 1024 * 1024,
        backup_count=5,
    )
    myprintx.print("终端和日志都会保存这条内容", fg_color="green")
    myprintx.unpatch_log()
    myprintx.patch_log("logs/app.log")  # 指定路径，已有文件会继续追加
    myprintx.print("写入指定日志")
    myprintx.unpatch_log()

    # 默认日志文件可追加自定义后缀
    myprintx.patch_log(suffix="p1")
    myprintx.print("写入当前进程的 p1 日志")
    myprintx.unpatch_log()

    # 全局接管与自动前缀一起使用
    myprintx.patch_color()
    myprintx.patch_prefix(
        show_date=True,
        show_time=True,
        custom_prefix="应用",
        show_location=True,
        show_pid=None,
    )
    try:
        print("带前缀的普通打印", fg_color="green")
    finally:
        myprintx.unpatch_prefix()
        myprintx.unpatch_color()

    # 控制是否屏蔽增强输出
    myprintx.print("调试输出")
    myprintx.set_show(False)
    myprintx.print("这行不会输出")
    assert myprintx.is_show() is False
    myprintx.set_show(True)
    myprintx.print("恢复输出")

    # 简易快速调用
    myprintx.patch_prefix(show_location=True)
    myprintx.info("系统初始化完成")      # 青色
    myprintx.warn("配置文件缺少部分字段")  # 黄色加粗
    myprintx.error("数据库连接失败")     # 红色加粗
    myprintx.debug("缓存刷新完成")       # 白色
    myprintx.unpatch_prefix()

    # 输出当前异常及完整 traceback
    try:
        1 / 0
    except ZeroDivisionError:
        myprintx.exception("计算失败")

    # 上下文管理器计时
    with myprintx.timer("数据处理") as timing:
        data = sum(range(1000))
    print(timing.elapsed)  # 秒数 float

    # 手动开始和结束计时
    myprintx.timer_start("下载")
    result = sum(range(1000))
    elapsed = myprintx.timer_end("下载")

    # 装饰器计时
    @myprintx.timer("计算")
    def calculate():
        return sum(range(1000))

    calculate()

    # mode 用法与分类开关
    myprintx.print("模式调试输出", mode="debug")
    myprintx.debug("快捷调试输出")
    myprintx.show_debug(False)  # 只屏蔽 debug
    myprintx.debug("这行不会输出")
    myprintx.print("这行也不会输出", mode="debug")
    myprintx.info("这行仍然输出")
    myprintx.show_debug()  # 默认参数为 True，恢复 debug
    myprintx.debug("调试输出恢复了")

    # 其他分类也有独立开关
    myprintx.show_info(False)
    myprintx.show_warn(False)
    myprintx.show_error(False)
    myprintx.show_info()
    myprintx.show_warn()
    myprintx.show_error()

    # 显式颜色和样式覆盖模式默认值
    myprintx.warn("自定义警告", fg_color="orange", style="underline")
    # 普通打印参数
    import io

    output = io.StringIO()
    myprintx.print("a", "b", sep=None, end="!", file=output, flush=True)
    assert output.getvalue() == "a b!"

    # 总开关优先于分类开关
    myprintx.set_show(False)
    myprintx.error("这行也不会输出")
    myprintx.set_show(True)
内置颜色名（不区分大小写）：

* 基础色：黑色 `black`、红色 `red`、绿色 `green`、黄色 `yellow`、蓝色 `blue`、紫色 `purple`、品红色 `magenta`、青色 `cyan`、白色 `white`。当前 `magenta` 与 `purple` 使用相同颜色码。

* 扩展色：橙色 `orange`、粉色 `pink`、灰色 `gray`/`grey`、棕色 `brown`、鲜绿色 `lime`、蓝绿色 `teal`、藏青色 `navy`、金色 `gold`、紫罗兰色 `violet`、靛蓝色 `indigo`。

* 自定义颜色：`#RRGGBB` 或 `(R, G, B)`，前景色和背景色均支持。旧写法 `bg_color="bg_red"` 仍可使用。

颜色与参数说明：

* 十六进制颜色必须是 `#` 加六位 ASCII 十六进制字符；RGB 必须是三个 `0`～`255` 整数组成的元组，不接受布尔分量。
* 颜色格式或数值错误抛出 `ValueError`，不支持的颜色类型（如列表、整数）抛出 `TypeError`。未知颜色名和未知字符串样式被忽略。

* `style` 每次支持一种样式：加粗 `bold`、斜体 `italic`、下划线 `underline`。

* `mode` 支持 `info`、`warn`、`error`、`debug`，不区分大小写。不支持的非空模式会抛出 `ValueError`。使用模式时，`fg_color=None`、`style=None` 采用模式默认值。

* `format` 支持 `json`、`list` 和 `auto`，不区分大小写。`format="json"` 会用 2 空格缩进美化 Python JSON 可序列化对象，也会先解析 JSON 字符串；普通非 JSON 字符串保持原样。`format="list"` 会将列表或元组按元素分行显示，其他参数保持普通字符串输出。`format="auto"` 会对 `dict` 使用 JSON 美化，对 `list`/`tuple` 使用列表美化，对可解析的 JSON 字符串使用 JSON 美化，其他类型保持普通输出。不支持的非空格式会抛出 `ValueError`。

* `sep=None` 等同于空格，`end=None` 使用默认换行；`file=None` 使用当前标准输出，其他输出对象直接传给原生 `print()`。

* 颜色通过 ANSI 控制码输出，实际显示取决于终端支持和主题。RGB、十六进制及扩展颜色名需要真彩色支持；写入文件或管道时不会自动去除控制码。

前缀与开关说明：
* `patch_prefix()` 默认显示日期和时间，可用 `show_date=False`、`show_time=False` 分别关闭；`show_location` 默认关闭。位置显示第一个 `myprintx.core` 外部调用者的文件名、函数名和行号。

* `show_pid=None` 时，单进程默认不显示 PID；使用 `multiprocessing` 时，主进程存在活动子进程以及子进程自身都会显示黄色的 `pid=xxx`。`show_pid=True` 始终显示，`show_pid=False` 在主、子进程中都不显示；当前不检测 `subprocess.Popen` 和多线程。

* 自动前缀各部分使用 `|` 分隔，顺序为日期时间、进程 ID、自定义标签、调用位置；未启用的部分会被省略。

* 日期和时间为绿色，位置为蓝色。正文的颜色和样式不改变自动前缀颜色；手动 ANSI 前缀会在需要时补充重置码，避免颜色延续到正文。

* `prefix=None` 使用自动前缀，`prefix=""` 关闭本次前缀，其他值覆盖本次前缀，均不改变全局配置。
* `patch_prefix()` 本身不会接管普通 `print()`；使用普通打印显示前缀时，还需启用 `patch_color()`。`unpatch_prefix()` 仅清除前缀配置，`unpatch_color()` 仅恢复打印函数。

* 快捷函数无需全局接管即可使用。前缀和显示开关为全局共享配置；开关影响增强输出及接管后的普通 `print()`，不影响未接管的原生打印。

* `is_show()` 只查询总开关。恢复总开关不会自动恢复已关闭的分类开关；被屏蔽的输出提前返回，不进行颜色校验。

日志文件说明：

* `patch_log(file_path=None, max_bytes=10 * 1024 * 1024, backup_count=5, suffix=None)` 开启日志副本并返回日志文件的绝对路径。未传 `file_path` 时，第一个调用默认 `patch_log()` 的进程创建 `logs/YYYYMMDD_HHMMSS_pid<ROOT_PID>/` 日志会话目录，并写入 `ppid<PPID>_pid<PID>.log`。其后创建并继承环境的子进程分别调用 `patch_log()` 时会复用同一目录，但各自写入独立文件。传入相对路径时，会在调用时转换为绝对路径。
* 默认路径下可传 `suffix`，非 `None` 值会先通过 `str()` 转为字符串，非空后缀会追加在 `.log` 前。例如 `patch_log(suffix="p1")` 生成 `ppid9000_pid10000_p1.log`，`patch_log(suffix=1)` 生成 `ppid9000_pid10000_1.log`。显式传入 `file_path` 时，以用户路径为准，`suffix` 不修改文件名。
* 若父进程未调用默认 `patch_log()`，多个兄弟子进程各自首次调用时会分别创建自己的日志会话目录。日志会话目录通过 `MYPRINTX_LOG_ROOT` 向后代进程继承；`unpatch_log()` 只关闭当前进程的日志记录，不清除该会话信息。
* 日志以 UTF-8 追加写入，自动去除 ANSI 颜色和样式控制码，不影响终端原有输出。默认路径和指定路径缺少父目录时都会自动创建。

* 当前日志在写入下一条内容会超过 `max_bytes` 时轮转，备份依次命名为 `.1`、`.2`，最多保留 `backup_count` 份。传入 `max_bytes=None` 可关闭轮转；单条内容本身超过限制时仍会完整写入。

* `unpatch_log()` 关闭日志记录，不影响终端打印。总开关或分类开关屏蔽的内容不会写入日志；日志配置是进程内状态，多进程需要分别调用 `patch_log()`。如显式传入同一路径，多个进程会共同追加该文件，当前不提供跨进程写锁。

* `exception()` 使用 error 模式输出传入内容，并附加当前异常的完整 traceback；日志副本中会自动移除颜色控制码。

计时功能说明：

* `timer(name)` 同时支持上下文管理器和同步函数装饰器，使用 `time.perf_counter()` 计算耗时；上下文结束后可通过 `timing.elapsed` 读取秒数。
* `timer_start(name)` 启动命名计时器，`timer_end(name)` 输出结果并返回耗时秒数。重复启动同名计时器或结束未启动的计时器会抛出 `RuntimeError`。

* 计时结果格式为 `[TIMER] 名称 | 耗时 1.235 秒`。发生异常时仍会输出耗时，原异常继续抛出；计时输出同样受前缀、日志副本和 `set_show()` 控制。

* 手动计时状态保存在当前进程内，多进程需要分别开始和结束；装饰器当前仅支持同步函数。

> 全局接管与兼容性：`patch_color()` 可重复调用，快捷函数不会破坏接管状态。它会影响当前解释器后续通过 `builtins.print` 输出的调用，但不影响提前保存的函数引用、`sys.stdout.write()` 等独立输出。
>
> 支持常用原生参数，但不保证所有边界行为完全一致。关闭接管或移除库后，原生 `print()` 不接受 `fg_color`、`bg_color`、`style`、`prefix`、`mode`、`format` 等扩展参数；只使用原生参数的调用无需因此修改。
## 打包与发布

    # 在项目根目录运行测试
    python -m unittest discover -s tests -v

    # 安装构建与发布工具
    pip install build twine

    # 发布前同步更新版本号：
    # setup.py 中的 version
    # myprintx/__init__.py 中的 __version__

    # 确认 dist/ 中只有本次待发布产物，避免误上传旧版本
    python -m build
    twine check dist/*

    # 测试安装：将 VERSION 替换为本次版本号
    pip install dist/myprintx-VERSION-py3-none-any.whl --force-reinstall

    # 确认后手动发布到 PyPI
    twine upload dist/*

    # 从 PyPI 更新安装
    pip install myprintx --upgrade
## 博客

* [〖教程〗增强版 print 函数，支持彩色与样式化终端输出](https://blog.csdn.net/sxf1061700625/article/details/153268971) （早期教程，当前用法以本 README 为准）

## 后续计划

持续完善……
