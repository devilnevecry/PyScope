"""mypkg package."""

__version__ = "0.1.0"


class Container:
    """A simple container class."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.items: list[str] = []

    def add(self, item: str) -> None:
        self.items.append(item)

    def get(self) -> list[str]:
        return list(self.items)


def process(data: list[str]) -> int:
    """Process some data and return a count."""
    return len(data)


def helper() -> str:
    return "helper"
