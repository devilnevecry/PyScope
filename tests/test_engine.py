"""Tests for the core analysis engine: discovery, AST, dependencies, findings."""

from __future__ import annotations

import pytest

from pyscope.analysis import AnalysisEngine, AnalysisError
from pyscope.ast_analysis import STDLIB_MODULES, analyze_file
from pyscope.config import Config
from pyscope.discovery import discover_project
from pyscope.localization import translate


def test_discover_simple_package(simple_package):
    result = discover_project(simple_package)
    rel = {f.relative for f in result.files}
    assert "mypkg/__init__.py" in rel
    assert "mypkg/core.py" in rel
    assert "mypkg/utils.py" in rel
    assert "mypkg" in result.packages


def test_discover_excludes_ignored_dirs(ignored_dirs):
    result = discover_project(ignored_dirs)
    rel = {f.relative for f in result.files}
    assert "pkg/main.py" in rel
    assert ".venv/lib/vendored.py" not in rel
    assert "build/build_fn.py" not in rel
    assert result.ignored_count >= 1


def test_discover_exclude_patterns(simple_package):
    result = discover_project(simple_package, exclude_patterns=["mypkg/utils.py"])
    rel = {f.relative for f in result.files}
    assert "mypkg/utils.py" not in rel
    assert "mypkg/core.py" in rel


def test_discover_gitignore(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "ignored.py").write_text("x = 1\n")
    (tmp_path / "kept.py").write_text("x = 1\n")
    (tmp_path / ".gitignore").write_text("sub/\n")
    result = discover_project(tmp_path)
    rel = {f.relative for f in result.files}
    assert "kept.py" in rel
    assert "sub/ignored.py" not in rel


def test_discover_respects_max_files(tmp_path):
    for i in range(5):
        (tmp_path / f"m{i}.py").write_text("x = 1\n")
    result = discover_project(tmp_path, max_files=3)
    assert len(result.files) == 3


def test_discover_symlink_outside_root_blocked(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "leaked.py").write_text("x = 1\n")
    (tmp_path / "keep.py").write_text("x = 1\n")
    try:
        (tmp_path / "link").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not permitted in this environment")
    result = discover_project(tmp_path)
    rel = {f.relative for f in result.files}
    assert "keep.py" in rel
    assert "link/leaked.py" not in rel


def test_ast_analysis_simple(simple_package):
    f = analyze_file(simple_package / "mypkg" / "core.py", simple_package)
    assert f.module_name == "mypkg.core"
    assert f.line_count > 0
    assert f.syntax_error is None
    funcs = {fn.name for fn in f.functions}
    assert "run" in funcs
    assert "async_run" in funcs
    init = analyze_file(simple_package / "mypkg" / "__init__.py", simple_package)
    classes = {c.name for c in init.classes}
    assert "Container" in classes


def test_ast_analysis_syntax_error(syntax_errors):
    f = analyze_file(syntax_errors / "pkg" / "broken.py", syntax_errors)
    assert f.syntax_error is not None
    assert "SyntaxError" in f.syntax_error


def test_ast_analysis_imports(simple_package):
    f = analyze_file(simple_package / "mypkg" / "core.py", simple_package)
    rel = [imp for imp in f.imports if imp.level > 0]
    assert rel, "expected a relative import"
    assert rel[0].module == ""


def test_stdlib_classification():
    assert "os" in STDLIB_MODULES
    assert "json" in STDLIB_MODULES
    assert "asyncio" in STDLIB_MODULES


def test_complexity_metrics(nested_functions):
    f = analyze_file(nested_functions / "pkg" / "deeply.py", nested_functions)
    assert f.syntax_error is None
    funcs = {fn.name: fn for fn in f.functions}
    assert "outer" in funcs
    # outer delegates to nested functions; its own body has no decisions.
    assert funcs["outer"].complexity >= 1
    # inner contains if/for/if decisions.
    assert funcs["inner"].complexity >= 2
    assert funcs["inner"].nesting_depth >= 2


def test_nested_definitions_count(nested_functions):
    f = analyze_file(nested_functions / "pkg" / "deeply.py", nested_functions)
    assert f.nested_definitions >= 2  # middle and inner


def test_class_metrics(simple_package):
    f = analyze_file(simple_package / "mypkg" / "__init__.py", simple_package)
    cls = {c.name: c for c in f.classes}
    assert "Container" in cls
    assert len(cls["Container"].methods) == 3  # __init__, add, get
    assert cls["Container"].public_method_count == 2  # add, get


def test_dependency_graph_cycle(circular_imports):
    engine = AnalysisEngine(Config())
    result = engine.analyze(circular_imports)
    graph = result.dependency_graph
    cycles = graph.get("cycles", [])
    # a <-> b cycle
    assert any({"pkg.a", "pkg.b"} <= set(c) for c in cycles), cycles


def test_dependency_graph_scc(circular_imports):
    engine = AnalysisEngine(Config())
    result = engine.analyze(circular_imports)
    assert result.summary["cycles"] >= 1


def test_dependency_classification(unresolved_imports):
    engine = AnalysisEngine(Config())
    result = engine.analyze(unresolved_imports)
    imports = []
    for f in result.files:
        imports.extend(f.imports)
    classifications = {imp.classification for imp in imports}
    assert "stdlib" in classifications
    assert "unresolved" in classifications


def test_relative_imports(circular_imports):
    engine = AnalysisEngine(Config())
    result = engine.analyze(circular_imports)
    graph = result.dependency_graph
    internal = graph.get("internal_modules", [])
    assert "pkg.a" in internal
    assert "pkg.b" in internal
    edges = graph.get("edges", [])
    # internal edge a -> b
    assert any(e["source"] == "pkg.a" and e["target"] == "pkg.b" for e in edges), edges


def test_findings_generated(circular_imports):
    engine = AnalysisEngine(Config())
    result = engine.analyze(circular_imports)
    assert len(result.findings) >= 1
    cats = {finding.get("category") for finding in result.findings}
    assert "cycle" in cats


def test_summary_counts(circular_imports):
    engine = AnalysisEngine(Config())
    result = engine.analyze(circular_imports)
    s = result.summary
    assert s["files"] >= 1
    assert s["modules"] >= 1
    assert s["cycles"] >= 1
    assert s["findings"] >= 1


def test_translate_ru_en():
    assert translate("cli.version", version="0.1.0", language="ru") == "PyScope 0.1.0"
    assert translate("cli.version", version="0.1.0", language="en") == "PyScope 0.1.0"
    assert translate("report.language", language="ru") == "Язык"
    assert translate("report.language", language="en") == "Language"


def test_analyze_nonexistent_path():
    engine = AnalysisEngine(Config())
    with pytest.raises(AnalysisError):
        engine.analyze("/nonexistent/path/xyz")


def test_one_broken_file_does_not_stop_project(syntax_errors):
    engine = AnalysisEngine(Config())
    result = engine.analyze(syntax_errors)
    assert result.summary["files"] >= 1
    assert result.summary["failed"] >= 1


def test_skipped_and_failed_recorded(syntax_errors):
    engine = AnalysisEngine(Config())
    result = engine.analyze(syntax_errors)
    assert any(f["path"] == "pkg/broken.py" for f in result.failed_files)
