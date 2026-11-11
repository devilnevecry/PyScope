"""Tests for exporters: JSON, DOT, Mermaid."""

from __future__ import annotations

import json

from pyscope.analysis import AnalysisEngine
from pyscope.config import Config
from pyscope.exporters import export_dot, export_json, export_mermaid, to_json_dict


def _engine() -> AnalysisEngine:
    return AnalysisEngine(Config())


def test_json_export_schema(tmp_path, circular_imports):
    result = _engine().analyze(circular_imports)
    out = tmp_path / "out.json"
    export_json(result, out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert "project_root" in data
    assert "summary" in data
    assert "files" in data
    assert "dependency_graph" in data
    assert "findings" in data
    assert data["summary"]["cycles"] >= 1


def test_json_export_deterministic(tmp_path, circular_imports):
    result = _engine().analyze(circular_imports)
    a = json.dumps(to_json_dict(result), ensure_ascii=False, sort_keys=True)
    b = json.dumps(to_json_dict(result), ensure_ascii=False, sort_keys=True)
    assert a == b


def test_dot_export(tmp_path, circular_imports):
    result = _engine().analyze(circular_imports)
    out = tmp_path / "graph.dot"
    export_dot(result, out)
    text = out.read_text(encoding="utf-8")
    assert text.startswith("digraph pyscope {")
    assert "pkg.a" in text
    assert "pkg.b" in text


def test_mermaid_export(tmp_path, circular_imports):
    result = _engine().analyze(circular_imports)
    out = tmp_path / "graph.mmd"
    export_mermaid(result, out)
    text = out.read_text(encoding="utf-8")
    assert text.startswith("flowchart LR")
    assert "-->" in text


def test_to_json_dict_versioned(circular_imports):
    result = _engine().analyze(circular_imports)
    data = to_json_dict(result)
    assert data["schema_version"] == "1.0"
    for f in data["files"]:
        assert "path" in f and "module" in f
        for imp in f["imports"]:
            assert "classification" in imp
            assert imp["classification"] in ("internal", "stdlib", "third_party", "unresolved")
