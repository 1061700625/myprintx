import time
from functools import wraps

from .core import print as _print


_START_TIMES = {}


def _report(name, elapsed):
    _print(f"[TIMER] {name} | 耗时 {elapsed:.3f} 秒")


class _Timer:

    def __init__(self, name):
        self.name = name
        self.elapsed = None
        self._started_at = None

    def __enter__(self):
        self._started_at = time.perf_counter()
        self.elapsed = None
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.elapsed = time.perf_counter() - self._started_at
        _report(self.name, self.elapsed)

    def __call__(self, function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            started_at = time.perf_counter()
            try:
                return function(*args, **kwargs)
            finally:
                _report(self.name, time.perf_counter() - started_at)

        return wrapper


def timer(name):
    """创建可用作上下文管理器或装饰器的计时器。"""
    return _Timer(name)


def timer_start(name):
    """启动一个命名计时器。"""
    if name in _START_TIMES:
        raise RuntimeError(f"Timer {name!r} is already running")
    _START_TIMES[name] = time.perf_counter()


def timer_end(name):
    """结束命名计时器，输出并返回耗时秒数。"""
    if name not in _START_TIMES:
        raise RuntimeError(f"Timer {name!r} was not started")
    elapsed = time.perf_counter() - _START_TIMES.pop(name)
    _report(name, elapsed)
    return elapsed
