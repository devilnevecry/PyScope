"""Static AST analysis engine.

Reads and parses Python source files without importing or executing them.
Collects module-level and function/class-level metrics.
"""

from __future__ import annotations

import ast
import tokenize
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

STDLIB_MODULES: frozenset[str] = frozenset(
    {
        "__future__",
        "_thread",
        "abc",
        "argparse",
        "array",
        "ast",
        "asyncio",
        "base64",
        "bdb",
        "binascii",
        "binhex",
        "bisect",
        "builtins",
        "bz2",
        "cProfile",
        "calendar",
        "cgi",
        "cgitb",
        "chunk",
        "cmath",
        "cmd",
        "code",
        "codecs",
        "codeop",
        "collections",
        "colorsys",
        "compileall",
        "concurrent",
        "configparser",
        "contextlib",
        "contextvars",
        "copy",
        "copyreg",
        "crypt",
        "csv",
        "ctypes",
        "curses",
        "dataclasses",
        "datetime",
        "dbm",
        "decimal",
        "difflib",
        "dis",
        "distutils",
        "doctest",
        "dummy_threading",
        "email",
        "encodings",
        "ensurepip",
        "enum",
        "errno",
        "faulthandler",
        "fcntl",
        "filecmp",
        "fileinput",
        "fnmatch",
        "formatter",
        "fpectl",
        "fractions",
        "ftplib",
        "functools",
        "gc",
        "genericpath",
        "getopt",
        "getpass",
        "gettext",
        "glob",
        "graphlib",
        "grp",
        "gzip",
        "hashlib",
        "heapq",
        "hmac",
        "html",
        "http",
        "imaplib",
        "imghdr",
        "imp",
        "importlib",
        "inspect",
        "io",
        "ipaddress",
        "itertools",
        "json",
        "keyword",
        "lib2to3",
        "linecache",
        "locale",
        "logging",
        "lzma",
        "mailbox",
        "mailcap",
        "marshal",
        "math",
        "mimetypes",
        "mmap",
        "modulefinder",
        "multiprocessing",
        "netrc",
        "nis",
        "nntplib",
        "nt",
        "ntpath",
        "numbers",
        "opcode",
        "operator",
        "optparse",
        "os",
        "pathlib",
        "pdb",
        "pickle",
        "pickletools",
        "pipes",
        "pkgutil",
        "platform",
        "plistlib",
        "poplib",
        "posix",
        "posixpath",
        "pprint",
        "profile",
        "pstats",
        "pty",
        "pwd",
        "py_compile",
        "pyclbr",
        "pydoc",
        "queue",
        "quopri",
        "re",
        "readline",
        "reprlib",
        "resource",
        "rlcompleter",
        "runpy",
        "sched",
        "secrets",
        "select",
        "selectors",
        "shelve",
        "shlex",
        "shutil",
        "signal",
        "site",
        "smtpd",
        "smtplib",
        "sndhdr",
        "socket",
        "socketserver",
        "sqlite3",
        "sre",
        "sre_compile",
        "sre_constants",
        "sre_parse",
        "ssl",
        "stat",
        "statistics",
        "string",
        "stringprep",
        "struct",
        "subprocess",
        "sunau",
        "symtable",
        "sys",
        "sysconfig",
        "syslog",
        "tabnanny",
        "tarfile",
        "telnetlib",
        "tempfile",
        "termios",
        "test",
        "textwrap",
        "threading",
        "time",
        "timeit",
        "tkinter",
        "token",
        "tokenize",
        "trace",
        "traceback",
        "tracemalloc",
        "tty",
        "turtle",
        "turtledemo",
        "types",
        "typing",
        "unicodedata",
        "unittest",
        "urllib",
        "uu",
        "uuid",
        "venv",
        "warnings",
        "wave",
        "weakref",
        "webbrowser",
        "winreg",
        "winsound",
        "wsgiref",
        "xdrlib",
        "xml",
        "xmlrpc",
        "zipapp",
        "zipfile",
        "zipimport",
        "zlib",
        "zoneinfo",
    }
)


@dataclass
class ImportInfo:
    module: str
    line: int
    kind: str  # "import" or "from"
    names: list[str] = field(default_factory=list)
    level: int = 0  # relative import level
    resolved: str | None = None  # resolved internal module name
    classification: str = "unresolved"  # internal | stdlib | third_party | unresolved


@dataclass
class FunctionMetric:
    name: str
    line: int
    end_line: int
    is_async: bool
    is_method: bool
    args_count: int
    branch_count: int
    complexity: int
    nesting_depth: int
    return_count: int
    exception_handler_count: int
    has_docstring: bool
    annotation_coverage: float
    decorators: list[str] = field(default_factory=list)
    code_lines: int = 0
    is_nested: bool = False


@dataclass
class ClassMetric:
    name: str
    line: int
    end_line: int
    bases: list[str] = field(default_factory=list)
    methods: list[FunctionMetric] = field(default_factory=list)
    public_method_count: int = 0
    decorators: list[str] = field(default_factory=list)
    has_docstring: bool = False
    is_nested: bool = False


@dataclass
class FileAnalysis:
    path: str
    module_name: str
    line_count: int
    code_line_count: int
    comment_count: int
    blank_line_count: int
    imports: list[ImportInfo] = field(default_factory=list)
    classes: list[ClassMetric] = field(default_factory=list)
    functions: list[FunctionMetric] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    global_declarations: int = 0
    exception_handlers: int = 0
    async_definitions: int = 0
    nested_definitions: int = 0
    docstring: str | None = None
    syntax_error: str | None = None
    encoding: str = "utf-8"
    skipped: bool = False
    skip_reason: str | None = None


@dataclass
class AnalysisResult:
    schema_version: str = "1.0"
    project_root: str = ""
    files: list[FileAnalysis] = field(default_factory=list)
    dependency_graph: dict[str, dict[str, Any]] = field(default_factory=dict)
    findings: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    skipped_files: list[dict[str, str]] = field(default_factory=list)
    failed_files: list[dict[str, str]] = field(default_factory=list)


def _decode_source(path: Path) -> tuple[str, str]:
    """Read file, detect encoding via tokenize, return (source, encoding)."""
    try:
        with tokenize.open(path) as handle:
            return handle.read(), handle.encoding
    except (tokenize.TokenError, SyntaxError):
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
            return source, "utf-8"
        except OSError:
            raise


def _count_lines(source: str) -> tuple[int, int, int, int]:
    """Return (total, code, comments, blanks)."""
    lines = source.splitlines()
    total = len(lines)
    comments = 0
    blanks = 0
    try:
        readline = iter(lines).__next__
        for tok in tokenize.generate_tokens(readline):
            if tok.type == tokenize.COMMENT:
                comments += 1
    except (tokenize.TokenError, IndentationError):
        pass
    for line in lines:
        if not line.strip():
            blanks += 1
    code = total - blanks
    return total, code, comments, blanks


def _node_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_node_name(node.value)}.{node.attr}"
    return ""


def _decorator_names(node: ast.AST) -> list[str]:
    return [_node_name(d) for d in getattr(node, "decorator_list", [])]


def _arg_count(args: ast.arguments) -> int:
    return (
        len(args.posonlyargs)
        + len(args.args)
        + len(args.kwonlyargs)
        + (1 if args.vararg else 0)
        + (1 if args.kwarg else 0)
    )


def _annotation_coverage(args: ast.arguments) -> float:
    total = _arg_count(args)
    if total == 0:
        return 1.0
    annotated = 0
    for a in args.posonlyargs + args.args:
        if a.annotation is not None:
            annotated += 1
    for a in args.kwonlyargs:
        if a.annotation is not None:
            annotated += 1
    if args.vararg and args.vararg.annotation is not None:
        annotated += 1
    if args.kwarg and args.kwarg.annotation is not None:
        annotated += 1
    return annotated / total


class _ComplexityCounter(ast.NodeVisitor):
    """Counts cyclomatic decision points, not descending into nested defs."""

    def __init__(self) -> None:
        self.count = 0

    def _safe_visit(self, node: ast.AST) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return
        visitor = getattr(self, f"visit_{type(node).__name__}", self.generic_visit_single)
        visitor(node)

    def generic_visit_single(self, node: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            self._safe_visit(child)

    def visit_FunctionDef(self, node: ast.AST) -> None:
        # measure this function's own decisions; nested defs are skipped
        for child in ast.iter_child_nodes(node):
            self._safe_visit(child)

    def visit_AsyncFunctionDef(self, node: ast.AST) -> None:
        self.visit_FunctionDef(node)

    def visit_If(self, node: ast.AST) -> None:
        self.count += 1
        self.generic_visit_single(node)

    def visit_For(self, node: ast.AST) -> None:
        self.count += 1
        self.generic_visit_single(node)

    def visit_While(self, node: ast.AST) -> None:
        self.count += 1
        self.generic_visit_single(node)

    def visit_ExceptHandler(self, node: ast.AST) -> None:
        self.count += 1
        self.generic_visit_single(node)

    def visit_With(self, node: ast.AST) -> None:
        self.count += 1
        self.generic_visit_single(node)

    def visit_Try(self, node: ast.AST) -> None:
        self.count += 1
        self.generic_visit_single(node)

    def visit_BoolOp(self, node: ast.AST) -> None:
        self.count += max(0, len(getattr(node, "values", [])) - 1)
        self.generic_visit_single(node)

    def visit_comprehension(self, node: ast.AST) -> None:
        self.count += len(getattr(node, "ifs", []))
        self.generic_visit_single(node)


def _cyclomatic_complexity(node: ast.AST) -> int:
    counter = _ComplexityCounter()
    counter.visit(node)
    return max(1, counter.count)


def _max_nesting(node: ast.AST) -> int:
    best = 0

    def walk(n: ast.AST, depth: int) -> None:
        nonlocal best
        if isinstance(n, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
            depth += 1
            best = max(best, depth)
        for child in ast.iter_child_nodes(n):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            walk(child, depth)

    walk(node, 0)
    return best


def _count_returns(node: ast.AST) -> int:
    count = 0

    def walk(n: ast.AST) -> None:
        nonlocal count
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return
        if isinstance(n, ast.Return):
            count += 1
        for child in ast.iter_child_nodes(n):
            walk(child)

    walk(node)
    return count


def _count_except_handlers(node: ast.AST) -> int:
    count = 0

    def walk(n: ast.AST) -> None:
        nonlocal count
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return
        if isinstance(n, ast.ExceptHandler):
            count += 1
        for child in ast.iter_child_nodes(n):
            walk(child)

    walk(node)
    return count


def _code_lines(node: ast.AST) -> int:
    start = node.lineno
    end = getattr(node, "end_lineno", start)
    return max(0, end - start + 1)


def _make_function_metric(
    node: ast.AST,
    *,
    is_async: bool,
    is_method: bool,
    is_nested: bool,
) -> FunctionMetric:
    return FunctionMetric(
        name=node.name,
        line=node.lineno,
        end_line=getattr(node, "end_lineno", node.lineno),
        is_async=is_async,
        is_method=is_method,
        args_count=_arg_count(node.args),
        branch_count=_cyclomatic_complexity(node) - 1,
        complexity=_cyclomatic_complexity(node),
        nesting_depth=_max_nesting(node),
        return_count=_count_returns(node),
        exception_handler_count=_count_except_handlers(node),
        has_docstring=ast.get_docstring(node) is not None,
        annotation_coverage=_annotation_coverage(node.args),
        decorators=_decorator_names(node),
        code_lines=_code_lines(node),
        is_nested=is_nested,
    )


class _FileAnalyzer(ast.NodeVisitor):
    def __init__(self, source: str, path: str, module_name: str) -> None:
        self.source = source
        self.path = path
        self.module_name = module_name
        self.tree: ast.Module | None = None
        self.imports: list[ImportInfo] = []
        self.classes: list[ClassMetric] = []
        self.functions: list[FunctionMetric] = []
        self.decorators: list[str] = []
        self.global_declarations = 0
        self.exception_handlers = 0
        self.async_definitions = 0
        self.nested_definitions = 0
        self.docstring: str | None = None
        self.syntax_error: str | None = None
        self._current_class: ClassMetric | None = None
        self._func_depth = 0

    def analyze(self) -> None:
        try:
            self.tree = ast.parse(self.source, filename=self.path)
        except SyntaxError as exc:
            self.syntax_error = f"SyntaxError: {exc.msg} (line {exc.lineno})"
            return
        except Exception as exc:  # pragma: no cover - defensive
            self.syntax_error = f"ParseError: {exc}"
            return
        self.visit(self.tree)

    def visit_Module(self, node: ast.Module) -> None:
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
        ):
            self.docstring = ast.get_docstring(node)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(
                ImportInfo(
                    module=alias.name,
                    line=node.lineno,
                    kind="import",
                    names=[alias.asname or alias.name],
                    level=0,
                )
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        self.imports.append(
            ImportInfo(
                module=module,
                line=node.lineno,
                kind="from",
                names=[a.asname or a.name for a in node.names],
                level=node.level or 0,
            )
        )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._process_function(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.async_definitions += 1
        self._process_function(node, is_async=True)

    def _process_function(self, node: ast.AST, *, is_async: bool, as_method: bool = False) -> None:
        self._func_depth += 1
        is_method = as_method or (self._current_class is not None and self._func_depth == 1)
        is_nested = self._func_depth > 1
        metric = _make_function_metric(
            node, is_async=is_async, is_method=is_method, is_nested=is_nested
        )
        if is_method and self._current_class is not None:
            self._current_class.methods.append(metric)
        else:
            self.functions.append(metric)
            if is_nested:
                self.nested_definitions += 1
        self.generic_visit(node)
        self._func_depth -= 1

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        bases = [_node_name(b) for b in node.bases]
        cls = ClassMetric(
            name=node.name,
            line=node.lineno,
            end_line=getattr(node, "end_lineno", node.lineno),
            bases=bases,
            decorators=_decorator_names(node),
            has_docstring=ast.get_docstring(node) is not None,
        )
        prev = self._current_class
        self._current_class = cls
        # Direct methods of this class.
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self._process_function(item, is_async=False, as_method=True)
            elif isinstance(item, ast.AsyncFunctionDef):
                self.async_definitions += 1
                self._process_function(item, is_async=True, as_method=True)
            elif isinstance(item, ast.ClassDef):
                self.visit(item)
        public = sum(1 for m in cls.methods if not m.name.startswith("_"))
        cls.public_method_count = public
        self.classes.append(cls)
        self._current_class = prev

    def visit_Global(self, node: ast.Global) -> None:
        self.global_declarations += len(node.names)
        self.generic_visit(node)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        self.global_declarations += len(node.names)
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        self.exception_handlers += len(node.handlers)
        self.generic_visit(node)


def analyze_source(source: str, path: str, module_name: str) -> FileAnalysis:
    """Analyze a single source string."""
    analysis = _FileAnalyzer(source, path, module_name)
    analysis.analyze()
    total, code, comments, blanks = _count_lines(source)
    return FileAnalysis(
        path=path,
        module_name=module_name,
        line_count=total,
        code_line_count=code,
        comment_count=comments,
        blank_line_count=blanks,
        imports=analysis.imports,
        classes=analysis.classes,
        functions=analysis.functions,
        decorators=analysis.decorators,
        global_declarations=analysis.global_declarations,
        exception_handlers=analysis.exception_handlers,
        async_definitions=analysis.async_definitions,
        nested_definitions=analysis.nested_definitions,
        docstring=analysis.docstring,
        syntax_error=analysis.syntax_error,
    )


def analyze_file(path: Path, root: Path) -> FileAnalysis:
    """Read and analyze one file on disk."""
    rel = path.resolve().relative_to(root.resolve()).as_posix()
    module_name = _module_name_from_path(rel)
    try:
        source, encoding = _decode_source(path)
    except (SyntaxError, tokenize.TokenError) as exc:
        return FileAnalysis(
            path=rel,
            module_name=module_name,
            line_count=0,
            code_line_count=0,
            comment_count=0,
            blank_line_count=0,
            syntax_error=f"Encoding/syntax read error: {exc}",
            encoding="utf-8",
        )
    except OSError as exc:
        return FileAnalysis(
            path=rel,
            module_name=module_name,
            line_count=0,
            code_line_count=0,
            comment_count=0,
            blank_line_count=0,
            syntax_error=f"OSError: {exc}",
            encoding="utf-8",
        )
    analysis = _FileAnalyzer(source, rel, module_name)
    analysis.analyze()
    total, code, comments, blanks = _count_lines(source)
    return FileAnalysis(
        path=rel,
        module_name=module_name,
        line_count=total,
        code_line_count=code,
        comment_count=comments,
        blank_line_count=blanks,
        imports=analysis.imports,
        classes=analysis.classes,
        functions=analysis.functions,
        decorators=analysis.decorators,
        global_declarations=analysis.global_declarations,
        exception_handlers=analysis.exception_handlers,
        async_definitions=analysis.async_definitions,
        nested_definitions=analysis.nested_definitions,
        docstring=analysis.docstring,
        syntax_error=analysis.syntax_error,
        encoding=encoding,
    )


def _module_name_from_path(relative: str) -> str:
    parts = relative.replace("\\", "/").removesuffix(".py").split("/")
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts) if parts else ""
