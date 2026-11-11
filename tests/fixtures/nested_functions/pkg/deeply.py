"""pkg.deeply module with nested functions."""


def outer(a: int) -> int:
    def middle(b: int) -> int:
        def inner(c: int) -> int:
            if c > 0:
                for i in range(c):
                    if i % 2 == 0:
                        a += 1
                    else:
                        a -= 1
            return a
        return inner(b)
    return middle(a)
