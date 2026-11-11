"""Architecture findings.

Produces transparent, heuristic-based findings from an analysis result.
Every finding carries a title, severity, location, explanation, rationale
and a practical recommendation.  Thresholds are configurable.
"""

from __future__ import annotations

from typing import Any

DEFAULT_THRESHOLDS = {
    "complexity": 10,
    "function_length": 60,
    "class_methods": 20,
    "docstring_coverage": 0.6,
    "outgoing_deps": 15,
    "incoming_deps": 15,
    "large_file_lines": 500,
}


def _sev(score: float) -> str:
    if score >= 0.7:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


def build_findings(
    files: list[dict[str, Any]],
    graph: dict[str, Any],
    thresholds: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    findings: list[dict[str, Any]] = []

    modules = graph.get("modules", {})
    edges = graph.get("edges", [])
    cycles = graph.get("cycles", [])

    # Index modules.
    mod_info: dict[str, dict[str, Any]] = {}
    for m in modules.values():
        mod_info[m.get("module", m.get("name", ""))] = m

    # Incoming / outgoing counts per module.
    outgoing: dict[str, int] = {}
    incoming: dict[str, int] = {}
    for e in edges:
        src = e.get("source")
        tgt = e.get("target")
        if src:
            outgoing[src] = outgoing.get(src, 0) + 1
        if tgt:
            incoming[tgt] = incoming.get(tgt, 0) + 1

    # --- Largest modules ---
    sorted_by_lines = sorted(files, key=lambda f: f.get("line_count", 0), reverse=True)[:5]
    for f in sorted_by_lines:
        if f.get("line_count", 0) >= thresholds["large_file_lines"]:
            findings.append(
                {
                    "title": "Large module",
                    "severity": _sev(min(f.get("line_count", 0) / 1000.0, 1.0)),
                    "file": f.get("path", ""),
                    "line": 1,
                    "explanation": f"Module contains {f.get('line_count', 0)} lines.",
                    "rationale": "Large modules are harder to maintain and test.",
                    "recommendation": "Consider splitting into smaller, focused modules.",
                    "category": "size",
                }
            )

    # --- Most complex functions ---
    for f in files:
        for fn in f.get("functions", []):
            if fn.get("complexity", 0) >= thresholds["complexity"]:
                findings.append(
                    {
                        "title": "Complex function",
                        "severity": _sev(min(fn.get("complexity", 0) / 30.0, 1.0)),
                        "file": f.get("path", ""),
                        "line": fn.get("line", 0),
                        "explanation": f"Function '{fn.get('name')}' has cyclomatic complexity {fn.get('complexity')}.",
                        "rationale": "High complexity makes code harder to test and reason about.",
                        "recommendation": "Refactor into smaller, single-purpose functions.",
                        "category": "complexity",
                    }
                )
        for cls in f.get("classes", []):
            if len(cls.get("methods", [])) >= thresholds["class_methods"]:
                findings.append(
                    {
                        "title": "Large class",
                        "severity": _sev(min(len(cls.get("methods", [])) / 50.0, 1.0)),
                        "file": f.get("path", ""),
                        "line": cls.get("line", 0),
                        "explanation": f"Class '{cls.get('name')}' has {len(cls.get('methods', []))} methods.",
                        "rationale": "Classes with many methods may violate single responsibility.",
                        "recommendation": "Consider splitting the class or extracting collaborators.",
                        "category": "size",
                    }
                )
            for m in cls.get("methods", []):
                if m.get("complexity", 0) >= thresholds["complexity"]:
                    findings.append(
                        {
                            "title": "Complex method",
                            "severity": _sev(min(m.get("complexity", 0) / 30.0, 1.0)),
                            "file": f.get("path", ""),
                            "line": m.get("line", 0),
                            "explanation": f"Method '{cls.get('name')}.{m.get('name')}' has complexity {m.get('complexity')}.",
                            "rationale": "Complex methods are harder to maintain and test.",
                            "recommendation": "Refactor the method into smaller units.",
                            "category": "complexity",
                        }
                    )

    # --- Highly coupled modules ---
    for mod, count in sorted(outgoing.items(), key=lambda x: -x[1])[:5]:
        if count >= thresholds["outgoing_deps"]:
            findings.append(
                {
                    "title": "Many outgoing dependencies",
                    "severity": _sev(min(count / 40.0, 1.0)),
                    "file": mod_info.get(mod, {}).get("path", mod),
                    "line": 1,
                    "explanation": f"Module '{mod}' depends on {count} other modules.",
                    "rationale": "Many outgoing dependencies indicate high coupling.",
                    "recommendation": "Reduce dependencies or introduce abstractions.",
                    "category": "coupling",
                }
            )
    for mod, count in sorted(incoming.items(), key=lambda x: -x[1])[:5]:
        if count >= thresholds["incoming_deps"]:
            findings.append(
                {
                    "title": "Many incoming dependencies",
                    "severity": _sev(min(count / 40.0, 1.0)),
                    "file": mod_info.get(mod, {}).get("path", mod),
                    "line": 1,
                    "explanation": f"Module '{mod}' is imported by {count} other modules.",
                    "rationale": "Many incoming dependencies make the module a core coupling point.",
                    "recommendation": "Ensure the module has a stable, well-documented interface.",
                    "category": "coupling",
                }
            )
    # --- Circular dependencies ---
    for cycle in cycles:
        findings.append(
            {
                "title": "Circular dependency",
                "severity": "high",
                "file": " | ".join(cycle),
                "line": 1,
                "explanation": "Modules form a circular import group: " + " -> ".join(cycle),
                "rationale": "Circular imports can cause initialization errors and tight coupling.",
                "recommendation": "Break the cycle by moving shared code to a third module.",
                "category": "cycle",
            }
        )
    # --- Low documentation coverage ---
    for f in files:
        total = len(f.get("functions", [])) + len(f.get("classes", []))
        if total == 0:
            continue
        documented = sum(1 for fn in f.get("functions", []) if fn.get("has_docstring")) + sum(
            1 for c in f.get("classes", []) if c.get("has_docstring")
        )
        coverage = documented / total
        if coverage < thresholds["docstring_coverage"]:
            findings.append(
                {
                    "title": "Low documentation coverage",
                    "severity": _sev(1.0 - coverage),
                    "file": f.get("path", ""),
                    "line": 1,
                    "explanation": f"Module has docstring coverage {coverage:.0%}.",
                    "rationale": "Undocumented code is harder for new developers to understand.",
                    "recommendation": "Add docstrings to public functions and classes.",
                    "category": "documentation",
                }
            )
    # --- Potential entry points ---
    for f in files:
        if f.get("path", "").endswith(("__main__.py", "cli.py", "main.py")):
            findings.append(
                {
                    "title": "Potential entry point",
                    "severity": "info",
                    "file": f.get("path", ""),
                    "line": 1,
                    "explanation": "Module looks like an application entry point.",
                    "rationale": "Entry points are natural starting points for understanding a project.",
                    "recommendation": "Document the module's purpose and invocation.",
                    "category": "entrypoint",
                }
            )
    return findings
