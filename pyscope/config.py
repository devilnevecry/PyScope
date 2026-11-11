"""Configuration support for PyScope.

Reads an optional ``pyscope.toml`` file located in the project root being
analyzed (or passed explicitly).  All values are optional with sensible
defaults.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .exceptions import ConfigurationError

try:  # Python 3.11+
    import tomllib as _toml
except ModuleNotFoundError:  # pragma: no cover - fallback for older interpreters
    import tomli as _toml  # type: ignore


DEFAULT_EXCLUDES = [
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "build",
    "dist",
    "node_modules",
    ".tox",
    ".eggs",
    "*.egg-info",
]


@dataclass
class Config:
    include_patterns: list[str] = field(default_factory=lambda: ["**/*.py"])
    exclude_patterns: list[str] = field(default_factory=list)
    default_excludes: list[str] = field(default_factory=lambda: list(DEFAULT_EXCLUDES))
    respect_gitignore: bool = True
    follow_symlinks: bool = False
    max_file_size: int = 5_000_000  # bytes
    max_files: int = 50_000
    complexity_threshold: int = 10
    function_length_threshold: int = 60
    class_method_threshold: int = 20
    docstring_coverage_threshold: float = 0.6
    ignored_import_patterns: list[str] = field(default_factory=list)
    report_language: str = "ru"  # ru | en
    report_theme: str = "light"  # light | dark
    graph_max_nodes: int = 500
    graph_package_aggregation: bool = False
    fail_on_cycles: bool = False
    fail_on_syntax_errors: bool = False

    @classmethod
    def load(cls, path: str | None = None) -> "Config":
        """Load configuration from ``pyscope.toml`` if present.

        Returns a default config when no file is found or when the file is
        empty.  Raises :class:`ConfigurationError` on invalid TOML or
        unknown keys.
        """
        if path is None:
            return cls()
        import os

        if not os.path.isfile(path):
            return cls()
        try:
            with open(path, "rb") as handle:
                data = _toml.load(handle)
        except _toml.TOMLDecodeError as exc:  # type: ignore[attr-defined]
            raise ConfigurationError(f"Invalid TOML in {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigurationError(f"Cannot read config {path}: {exc}") from exc
        if not data:
            return cls()
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Config":
        known = {
            "include_patterns",
            "exclude_patterns",
            "default_excludes",
            "respect_gitignore",
            "follow_symlinks",
            "max_file_size",
            "max_files",
            "complexity_threshold",
            "function_length_threshold",
            "class_method_threshold",
            "docstring_coverage_threshold",
            "ignored_import_patterns",
            "report_language",
            "report_theme",
            "graph_max_nodes",
            "graph_package_aggregation",
            "fail_on_cycles",
            "fail_on_syntax_errors",
        }
        unknown = set(data) - known
        if unknown:
            raise ConfigurationError("Unknown configuration keys: " + ", ".join(sorted(unknown)))
        return cls(**data)  # type: ignore[arg-type]

    def to_dict(self) -> dict[str, Any]:
        return {
            "include_patterns": self.include_patterns,
            "exclude_patterns": self.exclude_patterns,
            "default_excludes": self.default_excludes,
            "respect_gitignore": self.respect_gitignore,
            "follow_symlinks": self.follow_symlinks,
            "max_file_size": self.max_file_size,
            "max_files": self.max_files,
            "complexity_threshold": self.complexity_threshold,
            "function_length_threshold": self.function_length_threshold,
            "class_method_threshold": self.class_method_threshold,
            "docstring_coverage_threshold": self.docstring_coverage_threshold,
            "ignored_import_patterns": self.ignored_import_patterns,
            "report_language": self.report_language,
            "report_theme": self.report_theme,
            "graph_max_nodes": self.graph_max_nodes,
            "graph_package_aggregation": self.graph_package_aggregation,
            "fail_on_cycles": self.fail_on_cycles,
            "fail_on_syntax_errors": self.fail_on_syntax_errors,
        }
