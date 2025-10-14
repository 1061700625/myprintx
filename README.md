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
>>> import myprintx
>>> myprintx.print("a", fg_color="green")   # ✅ 正常（未打补丁）
>>> myprintx.auto_patch_color()
>>> print("b", fg_color="red")              # ✅ 正常（已打补丁）
>>> myprintx.unpatch()
>>> print("c")                              # ✅ 恢复为普通print
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
