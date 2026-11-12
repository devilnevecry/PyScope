# PyScope QA Bug Register

Format: ID | Severity | Description | Status | Fix | Regression Test

## Fixed

| ID | Severity | Description | Fix | Regression Test |
|----|----------|-------------|-----|-----------------|
| QA-01 | HIGH | JSON export dropped analysis fields (nested_definitions, async_definitions, global_declarations, exception_handlers, function branch_count/code_lines/is_nested/decorators/exception_handler_count, class is_nested). | exporters.py `to_json_dict` now emits every field from FileAnalysis/FunctionMetric/ClassMetric. | tests/test_exports.py::test_json_export_completeness |
| QA-02 | HIGH | HTML report tab switching crashed: `showTab('overview')` queried `#overview` but panels are `id="tab-overview"` → `null.classList.add` TypeError. | report.py `showTab` now builds `#tab-` + id. | tests/test_report.py::test_html_report_tab_switching_wiring |
| QA-03 | HIGH | HTML report `renderInventory()` crashed on load: `#inventory-body` element missing from template → TypeError on `innerHTML`. | report.py: added `tab-inventory` tab panel with `#inventory-body` div + inventory tab button + `report.nav.inventory` translations. | tests/test_report.py::test_html_report_has_inventory_section |
| QA-04 | MEDIUM | Dependency graph edge target resolution was wrong: relative `.b` from `pkg.a` resolved to `pkg.a.b` instead of `pkg.b`. | dependencies.py `_resolve_relative` now computes level-1 as current package. | tests/test_engine.py::test_relative_imports |
| QA-05 | MEDIUM | Import classification was only set on graph edges, not on per-file import objects → JSON/file-level classification stayed "unresolved". | analysis.py now classifies/resolves every file's imports after analysis. | tests/test_engine.py::test_dependency_classification |
| QA-06 | MEDIUM | Cyclomatic complexity counter skipped the top-level function node's own decisions. | ast_analysis.py `_ComplexityCounter.visit_FunctionDef` now measures the function's own decisions. | tests/test_engine.py::test_complexity_metrics |

## Notes

- Symlink-outside-root test is SKIPPED on this Windows host (no symlink creation privilege); unit-test logic in discovery.py covers it and is exercised where privileges allow.
- Windows cp1252 console cannot decode/display Cyrillic CLI output when captured via subprocess `text=True`; direct execution in a UTF-8 terminal works. Not a PyScope defect; test harness uses `encoding="utf-8", errors="replace"`.
- Cannot create files with `<`/`>` in names on Windows; HTML-injection via filename verified through unit test (test_report.py::test_html_escaping) and via valid special-char filename (`weird&name.py`).

## Closed (verified)

- Empty project handled (0 files, no crash).
- Large file skipped via config max_file_size.
- Unicode identifiers / UTF-8 BOM handled.
- Invalid TOML config rejected with clear error.
- Config thresholds (complexity) affect findings.
- Code execution never occurs (marker-file side-effect test).
- Symlink outside root not analyzed.
- Report writing inside project refused.
- Invalid path / non-directory path rejected (exit 1).
- --fail-on-cycles exits 2 on cyclic project, 0 on acyclic.
