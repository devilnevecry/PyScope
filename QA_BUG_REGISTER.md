# PyScope QA Bug Register

Format: ID | Severity | Description | Status | Fix | Regression Test

## Fixed — Phase 2

| ID | Severity | Description | Fix | Regression Test |
|----|----------|-------------|-----|-----------------|
| QA-01 | HIGH | JSON export dropped analysis fields (nested_definitions, async_definitions, global_declarations, exception_handlers, function branch_count/code_lines/is_nested/decorators/exception_handler_count, class is_nested). | exporters.py `to_json_dict` now emits every field from FileAnalysis/FunctionMetric/ClassMetric. | tests/test_exports.py::test_json_export_completeness |
| QA-02 | HIGH | HTML report tab switching crashed: `showTab('overview')` queried `#overview` but panels are `id="tab-overview"` → `null.classList.add` TypeError. | report.py `showTab` now builds `#tab-` + id. | tests/test_report.py::test_html_report_tab_switching_wiring |
| QA-03 | HIGH | HTML report `renderInventory()` crashed on load: `#inventory-body` element missing from template → TypeError on `innerHTML`. | report.py: added `tab-inventory` tab panel with `#inventory-body` div + inventory tab button + `report.nav.inventory` translations. | tests/test_report.py::test_html_report_has_inventory_section |
| QA-04 | MEDIUM | Dependency graph edge target resolution was wrong: relative `.b` from `pkg.a` resolved to `pkg.a.b` instead of `pkg.b`. | dependencies.py `_resolve_relative` now computes level-1 as current package. | tests/test_engine.py::test_relative_imports |
| QA-05 | MEDIUM | Import classification was only set on graph edges, not on per-file import objects → JSON/file-level classification stayed "unresolved". | analysis.py now classifies/resolves every file's imports after analysis. | tests/test_engine.py::test_dependency_classification |
| QA-06 | MEDIUM | Cyclomatic complexity counter skipped the top-level function node's own decisions. | ast_analysis.py `_ComplexityCounter.visit_FunctionDef` now measures the function's own decisions. | tests/test_engine.py::test_complexity_metrics |

## Fixed — Phase 3

| ID | Severity | Description | Fix | Regression Test |
|----|----------|-------------|-----|-----------------|
| QA-07 | HIGH | HTML report stat cards showed raw translation keys (e.g. "overview.total_files") instead of labels ("Всего файлов"). | report.py `renderOverview` now uses `report.overview.*` prefixed keys matching translations. | tests/test_report.py::test_html_report_contains_sections |
| QA-08 | HIGH | HTML report table headers showed raw translation keys (e.g. "report.packages.files", "report.inventory.type", "report.largest.classes"). | report.py: added missing translation keys to both `ru` and `en` sections of `REPORT_TRANSLATIONS`. | tests/test_report.py::test_html_report_contains_sections |
| QA-09 | HIGH | `escJs()` regex was broken by Python string escaping in non-raw triple-quoted string → `/\\/g` became `/\g` (invalid regex), causing JS parse error. | report.py: `JS` and `TEMPLATE` strings changed to raw strings (`r"""..."""`). | tests/test_report.py::test_html_report_self_contained (no JS errors) |
| QA-10 | MEDIUM | `<script id="pyscope-config">` and `<script id="pyscope-data">` contained JSON but lacked `type="application/json"`, causing browsers to parse them as JS ("Unexpected token ':'" page errors). | report.py: added `type="application/json"` to both script tags. | tests/test_report.py::test_html_report_self_contained (no page errors) |
| QA-11 | MEDIUM | Language/theme selection did not persist across page reloads: `setLang()`/`setTheme()` saved to localStorage but page load read only from embedded config. | report.py: `LANG` now reads `localStorage.getItem('pyscope-lang')` first; theme reads `localStorage.getItem('pyscope-theme')` and applies to both `<html>` and `<body>`. | Manual Playwright test (EN/RU switch, dark/light switch, reload persistence) |
| QA-12 | LOW | Symlink creation not possible on this Windows host (missing `SeCreateSymbolicLinkPrivilege`). Symlink safety test skipped. | Documented limitation; symlink safety logic in `discovery.py` reviewed and verified correct. | N/A (environment limitation) |

## Closed (verified)

- Empty project handled (0 files, no crash).
- Large file skipped via config max_file_size.
- Unicode identifiers / UTF-8 BOM handled.
- Invalid TOML config rejected with clear error.
- Config thresholds (complexity) affect findings.
- Code execution never occurs (marker-file side-effect test).
- Symlink outside root not analyzed (code reviewed; test skipped on this host).
- Report writing inside project refused.
- Invalid path / non-directory path rejected (exit 1).
- --fail-on-cycles exits 2 on cyclic project, 0 on acyclic.
