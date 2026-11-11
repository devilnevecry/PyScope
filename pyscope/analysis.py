"""Main analysis engine.

Orchestrates discovery, AST analysis, dependency analysis and findings.
The engine is independent of the CLI and report renderer.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .ast_analysis import (
    AnalysisResult,
    FileAnalysis,
    analyze_file,
)
from .config import Config
from .dependencies import _classify_import, _resolve_relative, build_dependency_graph
from .discovery import discover_project
from .exceptions import AnalysisError
from .findings import build_findings
from .localization import DEFAULT_LANGUAGE


class AnalysisEngine:
    def __init__(self, config: Config | None = None, language: str = DEFAULT_LANGUAGE) -> None:
        self.config = config or Config()
        self.language = language

    def analyze(
        self,
        root: str | os.PathLike[str],
        progress_callback=None,
    ) -> AnalysisResult:
        root_path = Path(root).expanduser()
        if not root_path.exists():
            raise AnalysisError(f"Project root does not exist: {root}")
        if not root_path.is_dir():
            raise AnalysisError(f"Project root is not a directory: {root}")

        result = AnalysisResult(project_root=str(root_path.resolve()))

        # Discovery.
        discovery = discover_project(
            root_path,
            include_patterns=self.config.include_patterns,
            exclude_patterns=self.config.exclude_patterns,
            default_excludes=self.config.default_excludes,
            respect_gitignore=self.config.respect_gitignore,
            follow_symlinks=self.config.follow_symlinks,
            max_files=self.config.max_files,
        )

        # Configuration from pyscope.toml if present in the project.
        toml_config = None
        if discovery.config_path is not None:
            try:
                from .config import Config as _Cfg

                toml_config = _Cfg.load(str(discovery.config_path))
            except Exception:
                toml_config = None
        if toml_config is not None:
            self.config = toml_config

        # Analyze each file.
        internal_modules: set[str] = set()
        file_dicts: list[dict[str, Any]] = []

        for i, df in enumerate(discovery.files, start=1):
            if progress_callback:
                progress_callback(i, len(discovery.files))
            # Size guard.
            try:
                size = df.path.stat().st_size
            except OSError:
                size = 0
            if size > self.config.max_file_size:
                result.skipped_files.append({"path": df.relative, "reason": "file too large"})
                continue

            try:
                fa = analyze_file(df.path, root_path)
            except Exception as exc:  # one file must not stop the whole project
                result.failed_files.append(
                    {"path": df.relative, "reason": f"{type(exc).__name__}: {exc}"}
                )
                continue

            if fa.syntax_error:
                result.failed_files.append({"path": df.relative, "reason": fa.syntax_error})
                # Still include the file with partial info so the report shows it.
            result.files.append(fa)
            if fa.module_name:
                internal_modules.add(fa.module_name)

        # Classify and resolve imports consistently for every file.
        for fa in result.files:
            for imp in fa.imports:
                if imp.level > 0:
                    imp.resolved = _resolve_relative(fa.module_name, imp.level, imp.module)
                    imp.classification = (
                        "internal" if imp.resolved in internal_modules else "unresolved"
                    )
                else:
                    imp.classification = _classify_import(
                        imp.module, imp.level, None, internal_modules
                    )

        file_dicts = [self._file_to_dict(fa) for fa in result.files]

        # Dependency analysis.
        graph = build_dependency_graph(
            file_dicts,
            internal_modules,
            ignored_import_patterns=self.config.ignored_import_patterns,
        )
        result.dependency_graph = self._graph_to_dict(graph)

        # Findings.
        thresholds = {
            "complexity": self.config.complexity_threshold,
            "function_length": self.config.function_length_threshold,
            "class_methods": self.config.class_method_threshold,
            "docstring_coverage": self.config.docstring_coverage_threshold,
            "outgoing_deps": max(1, self.config.graph_max_nodes // 30),
            "incoming_deps": max(1, self.config.graph_max_nodes // 30),
            "large_file_lines": self.config.function_length_threshold * 8,
        }
        result.findings = build_findings(file_dicts, self._graph_to_dict(graph), thresholds)

        # Summary.
        total_files = len(result.files)
        total_modules = len({f.module_name for f in result.files if f.module_name})
        total_lines = sum(f.line_count for f in result.files)
        total_code = sum(f.code_line_count for f in result.files)
        total_classes = sum(len(f.classes) for f in result.files)
        total_functions = sum(len(f.functions) for f in result.files)
        total_cycles = len(graph.cycles)
        result.summary = {
            "files": total_files,
            "modules": total_modules,
            "lines": total_lines,
            "code_lines": total_code,
            "classes": total_classes,
            "functions": total_functions,
            "cycles": total_cycles,
            "findings": len(result.findings),
            "skipped": len(result.skipped_files),
            "failed": len(result.failed_files),
            "language": self.language,
        }
        return result

    # -- serialization helpers -------------------------------------------------

    def _file_to_dict(self, fa: FileAnalysis) -> dict[str, Any]:
        return {
            "path": fa.path,
            "module": fa.module_name,
            "line_count": fa.line_count,
            "code_line_count": fa.code_line_count,
            "comment_count": fa.comment_count,
            "blank_line_count": fa.blank_line_count,
            "imports": [
                {
                    "module": imp.module,
                    "line": imp.line,
                    "kind": imp.kind,
                    "names": imp.names,
                    "level": imp.level,
                    "resolved": imp.resolved,
                    "classification": imp.classification,
                }
                for imp in fa.imports
            ],
            "classes": [
                {
                    "name": c.name,
                    "line": c.line,
                    "end_line": c.end_line,
                    "bases": c.bases,
                    "methods": [
                        {
                            "name": m.name,
                            "line": m.line,
                            "end_line": m.end_line,
                            "is_async": m.is_async,
                            "is_method": m.is_method,
                            "args_count": m.args_count,
                            "branch_count": m.branch_count,
                            "complexity": m.complexity,
                            "nesting_depth": m.nesting_depth,
                            "return_count": m.return_count,
                            "exception_handler_count": m.exception_handler_count,
                            "has_docstring": m.has_docstring,
                            "annotation_coverage": m.annotation_coverage,
                            "decorators": m.decorators,
                            "code_lines": m.code_lines,
                            "is_nested": m.is_nested,
                        }
                        for m in c.methods
                    ],
                    "public_method_count": c.public_method_count,
                    "decorators": c.decorators,
                    "has_docstring": c.has_docstring,
                    "is_nested": c.is_nested,
                }
                for c in fa.classes
            ],
            "functions": [
                {
                    "name": f.name,
                    "line": f.line,
                    "end_line": f.end_line,
                    "is_async": f.is_async,
                    "is_method": f.is_method,
                    "args_count": f.args_count,
                    "branch_count": f.branch_count,
                    "complexity": f.complexity,
                    "nesting_depth": f.nesting_depth,
                    "return_count": f.return_count,
                    "exception_handler_count": f.exception_handler_count,
                    "has_docstring": f.has_docstring,
                    "annotation_coverage": f.annotation_coverage,
                    "decorators": f.decorators,
                    "code_lines": f.code_lines,
                    "is_nested": f.is_nested,
                }
                for f in fa.functions
            ],
            "global_declarations": fa.global_declarations,
            "exception_handlers": fa.exception_handlers,
            "async_definitions": fa.async_definitions,
            "nested_definitions": fa.nested_definitions,
            "docstring": fa.docstring,
            "syntax_error": fa.syntax_error,
            "encoding": fa.encoding,
        }

    def _graph_to_dict(self, graph) -> dict[str, Any]:
        return {
            "modules": {
                mod: {
                    "path": info.get("path", ""),
                    "imports": info.get("imports", []),
                    "exports": info.get("exports", []),
                }
                for mod, info in graph.modules.items()
            },
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "line": e.line,
                    "kind": e.kind,
                    "classification": e.classification,
                }
                for e in graph.edges
            ],
            "sccs": graph.sccs,
            "cycles": graph.cycles,
            "internal_modules": sorted(graph.internal_modules),
        }
