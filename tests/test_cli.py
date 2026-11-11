"""Tests for the Typer CLI."""

from __future__ import annotations

from typer.testing import CliRunner

from pyscope.cli import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Analyze a Python project" in result.output or "analyze" in result.output


def test_cli_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "PyScope" in result.output


def test_cli_analyze_html(circular_imports, tmp_path):
    out = tmp_path / "report.html"
    result = runner.invoke(
        app, ["analyze", str(circular_imports), "--output", str(out), "--format", "html"]
    )
    assert result.exit_code == 0
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in text


def test_cli_analyze_json(circular_imports, tmp_path):
    out = tmp_path / "report.json"
    result = runner.invoke(
        app, ["analyze", str(circular_imports), "--output", str(out), "--format", "json"]
    )
    assert result.exit_code == 0
    import json

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"


def test_cli_analyze_dot(circular_imports, tmp_path):
    out = tmp_path / "graph.dot"
    result = runner.invoke(
        app, ["analyze", str(circular_imports), "--output", str(out), "--format", "dot"]
    )
    assert result.exit_code == 0
    assert out.read_text(encoding="utf-8").startswith("digraph pyscope")


def test_cli_analyze_mermaid(circular_imports, tmp_path):
    out = tmp_path / "graph.mmd"
    result = runner.invoke(
        app, ["analyze", str(circular_imports), "--output", str(out), "--format", "mermaid"]
    )
    assert result.exit_code == 0
    assert out.read_text(encoding="utf-8").startswith("flowchart LR")


def test_cli_analyze_exclude(simple_package, tmp_path):
    out = tmp_path / "report.html"
    result = runner.invoke(
        app,
        [
            "analyze",
            str(simple_package),
            "--output",
            str(out),
            "--format",
            "json",
            "--exclude",
            "mypkg/utils.py",
        ],
    )
    assert result.exit_code == 0
    import json

    data = json.loads(out.read_text(encoding="utf-8"))
    paths = {f["path"] for f in data["files"]}
    assert "mypkg/utils.py" not in paths


def test_cli_analyze_invalid_path():
    result = runner.invoke(app, ["analyze", "/nonexistent/path/xyz"])
    assert result.exit_code == 1


def test_cli_analyze_not_a_directory(tmp_path):
    file = tmp_path / "afile.py"
    file.write_text("x = 1\n")
    result = runner.invoke(app, ["analyze", str(file)])
    assert result.exit_code == 1


def test_cli_fail_on_cycles(circular_imports, tmp_path):
    out = tmp_path / "report.html"
    result = runner.invoke(
        app,
        [
            "analyze",
            str(circular_imports),
            "--output",
            str(out),
            "--format",
            "html",
            "--fail-on-cycles",
        ],
    )
    assert result.exit_code == 2


def test_cli_refuses_output_inside_project(circular_imports, tmp_path):
    # Try to write the report inside the analyzed project -> should refuse.
    inside = circular_imports / "report.html"
    result = runner.invoke(
        app, ["analyze", str(circular_imports), "--output", str(inside), "--format", "html"]
    )
    assert result.exit_code == 1
