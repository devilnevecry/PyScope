"""core module."""

from . import Container


def run(container: Container) -> str:
    container.add("a")
    container.add("b")
    return container.get()[0]


async def async_run(container: Container) -> str:
    return container.name
