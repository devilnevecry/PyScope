"""pkg.b imports pkg.a (cycle) and pkg.c."""

from .a import func_a


def func_b() -> str:
    return "b:" + func_a()
