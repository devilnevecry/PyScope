"""Shared fixtures for the PyScope test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def simple_package() -> Path:
    return FIXTURES / "simple_package"


@pytest.fixture
def circular_imports() -> Path:
    return FIXTURES / "circular_imports"


@pytest.fixture
def unresolved_imports() -> Path:
    return FIXTURES / "unresolved_imports"


@pytest.fixture
def syntax_errors() -> Path:
    return FIXTURES / "syntax_errors"


@pytest.fixture
def nested_functions() -> Path:
    return FIXTURES / "nested_functions"


@pytest.fixture
def many_modules() -> Path:
    return FIXTURES / "many_modules"


@pytest.fixture
def ignored_dirs() -> Path:
    return FIXTURES / "ignored_dirs"


@pytest.fixture
def engine():
    from pyscope.analysis import AnalysisEngine
    from pyscope.config import Config

    return AnalysisEngine(Config())
