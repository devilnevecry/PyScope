"""Tests for HTML report generation and HTML escaping."""

from __future__ import annotations

from pyscope.analysis import AnalysisEngine
from pyscope.config import Config
from pyscope.report import generate_report


def _engine() -> AnalysisEngine:
    return AnalysisEngine(Config())


def test_html_report_self_contained(tmp_path, circular_imports):
    result = _engine().analyze(circular_imports)
    html_text = generate_report(result, language="ru", theme="light")
    assert "<!DOCTYPE html>" in html_text
    assert "pyscope-data" in html_text
    assert "pyscope-config" in html_text
    # no external CDNs / remote resources (w3.org SVG namespace is not a fetch)
    assert "cdn" not in html_text.lower()
    assert "https://" not in html_text
    for m in __import__("re").findall(r"http://[^'\" ]+", html_text):
        assert m == "http://www.w3.org/2000/svg", m
    out = tmp_path / "report.html"
    out.write_text(html_text, encoding="utf-8")
    assert out.exists()


def test_html_report_english(tmp_path, circular_imports):
    result = _engine().analyze(circular_imports)
    html_text = generate_report(result, language="en", theme="dark")
    assert "Code Architecture Report" in html_text
    assert 'data-theme="dark"' in html_text


def test_html_escaping(tmp_path):
    from pyscope.analysis import AnalysisResult
    from pyscope.ast_analysis import FileAnalysis

    fa = FileAnalysis(
        path='<script>alert("x")</script>.py',
        module_name="bad&module",
        line_count=1,
        code_line_count=1,
        comment_count=0,
        blank_line_count=0,
    )
    res = AnalysisResult(project_root=str(tmp_path), files=[fa])
    html_text = generate_report(res, language="ru")
    # The embedded JSON must not contain a closing script tag (XSS protection).
    _head, _, data_part = html_text.partition('<script id="pyscope-data">')
    data_part, _, _ = data_part.partition("</script>")
    assert "</script>" not in data_part
    # The client-side esc function is present to render paths safely.
    assert "function esc(s)" in html_text
    # Module path is embedded raw in JSON (neutralized) but not as HTML.
    assert "bad&module" in html_text


def test_html_report_contains_sections(circular_imports):
    result = _engine().analyze(circular_imports)
    html_text = generate_report(result, language="ru")
    for section in [
        "Обзор проекта",
        "Статистика файлов",
        "Структура пакетов",
        "Граф зависимостей",
        "Циклические зависимости",
        "Сложность",
        "Самые большие файлы",
        "Рекомендации по архитектуре",
        "Подробности модуля",
    ]:
        assert section in html_text, section


def test_html_report_has_inventory_section(circular_imports):
    """Regression: inventory body element must exist so renderInventory() does not crash."""
    result = _engine().analyze(circular_imports)
    html_text = generate_report(result, language="ru")
    assert 'id="inventory-body"' in html_text
    assert 'id="tab-inventory"' in html_text
    assert "Инвентаризация функций и классов" in html_text


def test_html_report_tab_switching_wiring(circular_imports):
    """Regression: showTab() must reference tab- prefixed panel ids, not bare ids."""
    result = _engine().analyze(circular_imports)
    html_text = generate_report(result, language="ru")
    # panels are id="tab-<name>"
    for panel in ["overview", "files", "graph", "insights", "inventory"]:
        assert f'id="tab-{panel}"' in html_text, panel
    # showTab constructs '#tab-' + id
    assert "'#tab-'+id" in html_text
    # each tab button calls showTab with the matching name
    for name in ["overview", "files", "graph", "insights", "inventory"]:
        assert f"showTab('{name}')" in html_text, name
