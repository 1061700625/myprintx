# colorprintx 🎨
A lightweight Python library that enhances the built-in `print()` function.

## Features
- ✅ Foreground & background color control  
- ✅ Text styles: **bold**, _italic_, underline  
- ✅ Compatible with built-in `print` behavior  
- ✅ Optional global patch (one line activation)

## Install
```bash
pip install myprint
```

## Usage
```bash
# 基本用法
from myprintx import print
print("普通输出")
print("成功", fg_color="green", style="bold")
print("警告", fg_color="yellow", style="underline")
print("错误", fg_color="white", bg_color="red")

# 启用彩色全局打印
import myprintx
myprintx.patch_color()
print("绿色输出", fg_color="green", style="bold")
print("错误输出", fg_color="white", bg_color="red")
myprintx.unpatch_color()  # 恢复原始 print()

# 启用前缀打印
import myprintx
## 启用：日期、时间、自定义标签、位置信息
myprintx.patch_prefix(custom_prefix="INFO", show_location=True)
myprintx.print("启动成功", fg_color="green")
myprintx.print("任务执行中", fg_color="cyan")
myprintx.unpatch_prefix()  # 关闭前缀
```

## Publish
```bash
pip install build twine
python -m build
twine upload dist/*
```

## Blog
- [【教程】增强版 print 函数，支持彩色与样式化终端输出](https://blog.csdn.net/sxf1061700625/article/details/153268971)

## TODO
more ...
