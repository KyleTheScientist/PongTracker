from typing import Any


def ratio_safe(a, b, default=0, percent=False):
    if b == 0:
        return default
    return a / b * (100 if percent else 1)

class CallLater:

    def __init__(self, func, *args, **kwargs) -> None:
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        result = self.func(*self.args, **self.kwargs)
        # print(self.func.__name__, *self.args, self.kwargs, '-> \n', result)
        # print("=" * 100)
        return result
