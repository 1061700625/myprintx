# myprintx 🎨

一个轻量级 Python 库，为内置 `print()` 提供颜色、样式和前缀增强。

## 功能

* ✅ 彩色输出 — 支持前景色、背景色、内置颜色名、RGB 和十六进制颜色

* ✅ 文本样式 — 支持加粗、斜体和下划线

* ✅ 常用参数 — 支持 `sep`、`end`、`file` 和 `flush`

* ✅ 全局接管 — 一行启用，让后续普通 `print()` 使用增强功能

* ✅ 自动前缀 — 显示日期、时间、自定义标签和调用位置

* ✅ 快捷输出 — 内置 `info()`、`warn()`、`error()`、`debug()`

## 安装

```bash
pip install myprintx
```

> 🧩 无额外运行时依赖

## 用法

```python
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

# 全局接管与自动前缀一起使用
myprintx.patch_color()
myprintx.patch_prefix(
    show_date=True,
    show_time=True,
    custom_prefix="应用",
    show_location=True,
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
```

内置颜色名（不区分大小写）：

* 基础色：黑色 `black`、红色 `red`、绿色 `green`、黄色 `yellow`、蓝色 `blue`、紫色 `purple`、品红色 `magenta`、青色 `cyan`、白色 `white`。当前 `magenta` 与 `purple` 使用相同颜色码。

* 扩展色：橙色 `orange`、粉色 `pink`、灰色 `gray`/`grey`、棕色 `brown`、鲜绿色 `lime`、蓝绿色 `teal`、藏青色 `navy`、金色 `gold`、紫罗兰色 `violet`、靛蓝色 `indigo`。

* 自定义颜色：`#RRGGBB` 或 `(R, G, B)`，前景色和背景色均支持。旧写法 `bg_color="bg_red"` 仍可使用。

颜色与参数说明：

* 十六进制颜色必须是 `#` 加六位 ASCII 十六进制字符；RGB 必须是三个 `0`～`255` 整数组成的元组，不接受布尔分量。

* 颜色格式或数值错误抛出 `ValueError`，不支持的颜色类型（如列表、整数）抛出 `TypeError`。未知颜色名和未知字符串样式被忽略。

* `style` 每次支持一种样式：加粗 `bold`、斜体 `italic`、下划线 `underline`。

* `mode` 支持 `info`、`warn`、`error`、`debug`，不区分大小写。不支持的非空模式会抛出 `ValueError`。使用模式时，`fg_color=None`、`style=None` 采用模式默认值。

* `sep=None` 等同于空格，`end=None` 使用默认换行；`file=None` 使用当前标准输出，其他输出对象直接传给原生 `print()`。

* 颜色通过 ANSI 控制码输出，实际显示取决于终端支持和主题。RGB、十六进制及扩展颜色名需要真彩色支持；写入文件或管道时不会自动去除控制码。

前缀与开关说明：

* `patch_prefix()` 默认显示日期和时间，可用 `show_date=False`、`show_time=False` 分别关闭；`show_location` 默认关闭。位置显示第一个 `myprintx.core` 外部调用者的文件名、函数名和行号。

* 日期和时间为绿色，位置为蓝色。正文的颜色和样式不改变自动前缀颜色；手动 ANSI 前缀会在需要时补充重置码，避免颜色延续到正文。

* `prefix=None` 使用自动前缀，`prefix=""` 关闭本次前缀，其他值覆盖本次前缀，均不改变全局配置。

* `patch_prefix()` 本身不会接管普通 `print()`；使用普通打印显示前缀时，还需启用 `patch_color()`。`unpatch_prefix()` 仅清除前缀配置，`unpatch_color()` 仅恢复打印函数。

* 快捷函数无需全局接管即可使用。前缀和显示开关为全局共享配置；开关影响增强输出及接管后的普通 `print()`，不影响未接管的原生打印。

* `is_show()` 只查询总开关。恢复总开关不会自动恢复已关闭的分类开关；被屏蔽的输出提前返回，不进行颜色校验。

> 全局接管与兼容性：`patch_color()` 可重复调用，快捷函数不会破坏接管状态。它会影响当前解释器后续通过 `builtins.print` 输出的调用，但不影响提前保存的函数引用、`sys.stdout.write()` 等独立输出。
>
> 支持常用原生参数，但不保证所有边界行为完全一致。关闭接管或移除库后，原生 `print()` 不接受 `fg_color`、`bg_color`、`style`、`prefix`、`mode` 等扩展参数；只使用原生参数的调用无需因此修改。

## 打包与发布

```bash
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
```

## 博客

* [【教程】增强版 print 函数，支持彩色与样式化终端输出](https://blog.csdn.net/sxf1061700625/article/details/153268971)（早期教程，当前用法以本 README 为准）

## 后续计划

持续完善……
