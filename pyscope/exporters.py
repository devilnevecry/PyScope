"""Export formats: JSON, Graphviz DOT, Mermaid.

All exports use the same underlying analysis result so metrics never
contradict between formats.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .analysis import AnalysisResult

SCHEMA_VERSION = "1.0"


def to_json_dict(result: AnalysisResult) -> dict[str, Any]:
    """Return a versioned, JSON-serializable representation of the result."""
    return {
        "schema_version": SCHEMA_VERSION,
        "project_root": result.project_root,
        "language": result.summary.get("language", "ru"),
        "summary": result.summary,
        "files": [
            {
                "path": f.path,
                "module": f.module_name,
                "line_count": f.line_count,
                "code_line_count": f.code_line_count,
                "comment_count": f.comment_count,
                "blank_line_count": f.blank_line_count,
                "encoding": f.encoding,
                "syntax_error": f.syntax_error,
                "docstring": f.docstring,
                "decorators": f.decorators,
                "global_declarations": f.global_declarations,
                "exception_handlers": f.exception_handlers,
                "async_definitions": f.async_definitions,
                "nested_definitions": f.nested_definitions,
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
                    for imp in f.imports
                ],
                "classes": [
                    {
                        "name": c.name,
                        "line": c.line,
                        "end_line": c.end_line,
                        "bases": c.bases,
                        "public_method_count": c.public_method_count,
                        "decorators": c.decorators,
                        "has_docstring": c.has_docstring,
                        "is_nested": c.is_nested,
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
                    }
                    for c in f.classes
                ],
                "functions": [
                    {
                        "name": fn.name,
                        "line": fn.line,
                        "end_line": fn.end_line,
                        "is_async": fn.is_async,
                        "is_method": fn.is_method,
                        "args_count": fn.args_count,
                        "branch_count": fn.branch_count,
                        "complexity": fn.complexity,
                        "nesting_depth": fn.nesting_depth,
                        "return_count": fn.return_count,
                        "exception_handler_count": fn.exception_handler_count,
                        "has_docstring": fn.has_docstring,
                        "annotation_coverage": fn.annotation_coverage,
                        "decorators": fn.decorators,
                        "code_lines": fn.code_lines,
                        "is_nested": fn.is_nested,
                    }
                    for fn in f.functions
                ],
            }
            for f in result.files
        ],
        "dependency_graph": result.dependency_graph,
        "findings": result.findings,
        "skipped_files": result.skipped_files,
        "failed_files": result.failed_files,
    }


def export_json(result: AnalysisResult, path: str | Path) -> None:
    data = to_json_dict(result)
    text = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False)
    Path(path).write_text(text, encoding="utf-8")


def _dot_escape(label: str) -> str:
    return label.replace("\\", "\\\\").replace('"', '\\"')


def export_dot(result: AnalysisResult, path: str | Path) -> None:
    """Export the dependency graph as Graphviz DOT."""
    graph = result.dependency_graph
    edges = graph.get("edges", [])
    modules = graph.get("modules", {})

    lines: list[str] = []
    lines.append("digraph pyscope {")
    lines.append("  rankdir=LR;")
    lines.append('  node [shape=box, style=filled, fillcolor="#e8f0fe", color="#4285f4"];')
    lines.append('  edge [color="#666666", fontcolor="#666666", fontsize=10];')

    # Nodes: internal modules.
    for mod in sorted(modules):
        lines.append(f'  "{_dot_escape(mod)}";')

    # Edges: internal->internal only, deduplicated.
    seen: set[tuple[str, str]] = set()
    for e in edges:
        if e.get("classification") != "internal":
            continue
        key = (e["source"], e["target"])
        if key in seen:
            continue
        seen.add(key)
        lines.append(f'  "{_dot_escape(e["source"])}" -> "{_dot_escape(e["target"])}";')

    lines.append("}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_mermaid(result: AnalysisResult, path: str | Path) -> None:
    """Export the dependency graph as a Mermaid flowchart."""
    graph = result.dependency_graph
    edges = graph.get("edges", [])

    lines: list[str] = []
    lines.append("flowchart LR")
    seen: set[tuple[str, str]] = set()
    for e in edges:
        if e.get("classification") != "internal":
            continue
        key = (e["source"], e["target"])
        if key in seen:
            continue
        seen.add(key)
        src = _mermaid_id(e["source"])
        tgt = _mermaid_id(e["target"])
        lines.append(f"    {src} --> {tgt}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _mermaid_id(mod: str) -> str:
    safe = "".join(c if c.isalnum() else "_" for c in mod)
    if not safe or safe[0].isdigit():
        safe = "m_" + safe
    return f'{safe}["{html.escape(mod)}"]'
