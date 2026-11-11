"""Import and dependency analysis.

Builds a directed module dependency graph, classifies imports (internal /
stdlib / third-party / unresolved), and detects strongly connected
components (cycles) using Tarjan's algorithm.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DependencyEdge:
    source: str
    target: str
    line: int
    kind: str  # "import" | "from"
    classification: str  # internal | stdlib | third_party | unresolved


@dataclass
class DependencyGraph:
    modules: dict[str, dict[str, Any]] = field(default_factory=dict)
    edges: list[DependencyEdge] = field(default_factory=list)
    sccs: list[list[str]] = field(default_factory=list)  # cycles (size>1) + singletons
    cycles: list[list[str]] = field(default_factory=list)  # SCCs with size > 1
    internal_modules: set[str] = field(default_factory=set)


def _is_stdlib(module: str) -> bool:
    top = module.split(".")[0]
    if top in sys.stdlib_module_names:
        return True
    # Fallback for module names not listed (e.g. very old / platform).
    return False


def _is_third_party(module: str, internal_modules: set[str]) -> bool:
    top = module.split(".")[0]
    if top in internal_modules:
        return False
    if _is_stdlib(module):
        return False
    return True


def _classify_import(
    raw_module: str, level: int, resolved: str | None, internal_modules: set[str]
) -> str:
    """Classify an import as internal, stdlib, third-party or unresolved."""
    if level > 0:
        return "internal"
    if resolved:
        return "internal"
    top = raw_module.split(".")[0]
    if top in internal_modules:
        return "internal"
    if _is_stdlib(raw_module):
        return "stdlib"
    return "third_party"


def build_dependency_graph(
    files: list[dict[str, Any]],
    internal_modules: set[str],
    ignored_import_patterns: list[str] | None = None,
) -> DependencyGraph:
    """Build the dependency graph from per-file analysis results.

    ``files`` is a list of dicts with keys ``module``, ``path``, ``imports``
    where each import has ``module``, ``level``, ``classification``.
    """
    ignored = ignored_import_patterns or []
    graph = DependencyGraph(internal_modules=set(internal_modules))

    for f in files:
        mod = f.get("module") or ""
        if not mod:
            continue
        graph.modules.setdefault(mod, {"path": f.get("path", ""), "imports": [], "exports": []})

    for f in files:
        source = f.get("module") or ""
        if not source:
            continue
        for imp in f.get("imports", []):
            raw_module = imp.get("module", "")
            level = imp.get("level", 0)
            if _matches_ignored(raw_module, ignored):
                continue
            resolved_mod = imp.get("resolved")
            classification = _classify_import(raw_module, level, resolved_mod, internal_modules)
            target = raw_module
            # Relative imports resolve against the source module's package.
            if level > 0:
                target = _resolve_relative(source, level, raw_module)
            elif resolved_mod:
                target = resolved_mod
            elif classification == "internal":
                target = raw_module
            edge = DependencyEdge(
                source=source,
                target=target,
                line=imp.get("line", 0),
                kind=imp.get("kind", "from"),
                classification=classification,
            )
            graph.edges.append(edge)
            graph.modules.setdefault(source, {"imports": [], "exports": []})["imports"].append(
                target
            )
            graph.modules.setdefault(target, {"imports": [], "exports": []})["exports"].append(
                source
            )

    graph.sccs = _tarjan(graph)
    graph.cycles = [scc for scc in graph.sccs if len(scc) > 1]
    return graph


def _matches_ignored(module: str, patterns: list[str]) -> bool:
    import fnmatch

    return any(fnmatch.fnmatch(module, pat) for pat in patterns)


def _resolve_relative(source: str, level: int, module: str) -> str:
    """Resolve a relative import against the source module.

    Level 1 refers to the current package; higher levels go up from there.
    """
    parts = source.split(".")
    package = parts[:-1] if len(parts) > 1 else parts
    up = max(0, level - 1)
    base = package[: max(0, len(package) - up)]
    if module:
        base = base + module.split(".")
    return ".".join(base) if base else module


def _tarjan(graph: DependencyGraph) -> list[list[str]]:
    """Tarjan's strongly connected components algorithm."""
    index_counter = [0]
    stack: list[str] = []
    lowlink: dict[str, int] = {}
    index: dict[str, int] = {}
    on_stack: dict[str, bool] = {}
    result: list[list[str]] = []

    nodes = list(graph.modules.keys())
    # Include nodes that appear only as targets.
    for edge in graph.edges:
        if edge.target not in graph.modules:
            nodes.append(edge.target)
    nodes = list(dict.fromkeys(nodes))

    sys.setrecursionlimit(max(1000, len(nodes) * 10 + 1000))

    def strongconnect(v: str) -> None:
        index[v] = index_counter[0]
        lowlink[v] = index_counter[0]
        index_counter[0] += 1
        stack.append(v)
        on_stack[v] = True

        targets = graph.modules.get(v, {}).get("imports", [])
        # Deduplicate while preserving order.
        seen: set[str] = set()
        ordered: list[str] = []
        for t in targets:
            if t not in seen:
                seen.add(t)
                ordered.append(t)

        for w in ordered:
            if w not in index:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif on_stack.get(w):
                lowlink[v] = min(lowlink[v], index[w])

        if lowlink[v] == index[v]:
            component: list[str] = []
            while True:
                w = stack.pop()
                on_stack[w] = False
                component.append(w)
                if w == v:
                    break
            result.append(component)

    for v in nodes:
        if v not in index:
            strongconnect(v)

    return result
