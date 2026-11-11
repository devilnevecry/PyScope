"""PyScope - Python Codebase Explorer.

A local-first static analysis tool for Python repositories.
"""

__version__ = "0.1.0"
__author__ = "devilnevecry"
__license__ = "MIT"

from .analysis import AnalysisEngine, AnalysisResult
from .discovery import discover_project
from .exceptions import PyScopeError

__all__ = [
    "AnalysisEngine",
    "AnalysisResult",
    "PyScopeError",
    "__author__",
    "__license__",
    "__version__",
    "discover_project",
]
