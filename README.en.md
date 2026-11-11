# PyScope — Python Codebase Explorer

PyScope is a local-first static analysis tool for Python repositories that generates interactive architecture reports. It helps developers understand unfamiliar codebases: structure, dependencies, coupling, circular imports, and maintainability hotspots.

## Features

- **AST-based static analysis** — reads and parses source files without importing or executing the target project's code.
- **Project discovery** — Python files, packages, modules, `__init__.py`, entry points, test directories, configuration, framework indicators.
- **File, function, and class metrics** — lines of code, comments, arguments, branches, cyclomatic complexity, nesting depth, docstring and type-annotation coverage.
- **Import and dependency analysis** — absolute and relative imports, classified as internal, standard library, third-party, or unresolved.
- **Dependency graph** — directed module graph with in/out degree, centrality, isolated and highly coupled modules.
- **Cycle detection** — Tarjan's strongly connected components (SCC) and circular dependency reporting.
- **Architecture recommendations** — large modules, complex functions/classes, high coupling, low documentation coverage, potential entry points.
- **Interactive HTML report** — SVG graph with zoom, pan, node selection, search, package filtering, cycle highlighting, light/dark themes, RU/EN language switch. Works locally without a server or network.
- **Exports** — JSON (versioned schema 1.0), Graphviz DOT, Mermaid, terminal summary.
- **Configuration** — `pyscope.toml`: include/exclude patterns, complexity thresholds, report and graph settings, ignored imports.
- **Safety** — target code is never executed or imported; no symlinks outside project root; path traversal protection; HTML escaping; one bad file does not stop analysis.
- **Localization** — Russian by default, English as a second language.

## Quick start

```bash
pip install pyscope
pyscope analyze /path/to/project --output report.html --open
pyscope analyze /path/to/project --format json --output analysis.json
pyscope version
```

### CLI commands

| Command | Description |
|---------|-------------|
| `pyscope analyze PATH` | Analyze a project and produce an HTML report |
| `pyscope analyze PATH --format json` | Export JSON |
| `pyscope analyze PATH --format dot` | Export Graphviz DOT |
| `pyscope analyze PATH --format mermaid` | Export Mermaid |
| `pyscope analyze PATH --output report.html` | Output destination |
| `pyscope analyze PATH --exclude "tests/**"` | Additional exclude globs |
| `pyscope analyze PATH --fail-on-cycles` | Exit code 2 when cycles are found |
| `pyscope analyze PATH --open` | Open report in the browser |
| `pyscope analyze PATH --language en` | Report language (ru/en) |
| `pyscope version` | Show version |

## Configuration (`pyscope.toml`)

Create `pyscope.toml` in the project root or pass `--config`:

```toml
exclude_patterns = ["tests/**", "migrations/**"]
respect_gitignore = true
max_file_size = 5000000
complexity_threshold = 10
function_length_threshold = 60
class_method_threshold = 20
docstring_coverage_threshold = 0.6
report_language = "ru"
report_theme = "light"
graph_max_nodes = 500
fail_on_cycles = false
```

## Metrics (how they are computed)

All metrics are heuristics, not definitive quality judgments.

- **Cyclomatic complexity**: 1 + number of branch points (`if`, `for`, `while`, `except`, `with`, `try`, `and`/`or`, comprehension conditions). Nested functions do not count toward the enclosing function.
- **Nesting depth**: maximum depth of control-flow constructs inside a definition.
- **Type annotation coverage**: share of function arguments with type annotations.
- **Docstring coverage**: share of public functions and classes with docstrings.

## Security

- Target project code is never imported or executed.
- No `setup.py` execution and no package installation from the target repository.
- Symlinks leading outside the project root are not followed.
- Path traversal protection.
- HTML content is escaped; source code is not injected into executable JavaScript.
- A single malformed file does not stop analysis; skipped and failed files are reported.

## Limitations

- Static analysis cannot fully determine runtime behavior or prove code correctness.
- Unresolved imports are not always errors (e.g., dynamic imports).
- Metrics are heuristics; thresholds are configurable.

## Development

```bash
git clone https://github.com/devilnevecry/PyScope.git
cd PyScope
python -m pip install -e ".[dev]"
python -m pytest tests/ -q
ruff check pyscope tests
ruff format pyscope tests
```

## License

MIT. See `LICENSE`.
