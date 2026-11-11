"""pkg.a imports pkg.b."""

from .b import func_b


def func_a() -> str:
    return "a:" + func_b()
