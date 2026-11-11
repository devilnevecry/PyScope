"""Command-line interface for PyScope."""

from __future__ import annotations

import os
import sys
import webbrowser
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
)

from .__init__ import __version__
from .analysis import AnalysisEngine
from .config import Config
from .exceptions import (
    AnalysisError,
    ConfigurationError,
    PyScopeError,
    SafetyError,
)
from .exporters import export_dot, export_json, export_mermaid
from .localization import DEFAULT_LANGUAGE, translate
from .report import generate_report

# Ensure UTF-8 output on Windows consoles that default to a legacy code page.
# Falls back to replacement characters so analysis output never crashes on
# encoding, while modern UTF-8 terminals render Cyrillic correctly.
for _stream in (sys.stdout, sys.stderr):
    if _stream is not None and hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass

app = typer.Typer(
    name="pyscope",
    help="PyScope — Python Codebase Explorer. Static analysis of Python repositories.",
    no_args_is_help=True,
)
console = Console()


def _resolve_language(value: str | None, config: Config) -> str:
    if value:
        return value
    return config.report_language or DEFAULT_LANGUAGE


@app.command()
def analyze(
    path: str = typer.Argument(..., help="Path to the Python project to analyze."),
    output: str | None = typer.Option(
        None, "--output", "-o", help="Output file path (default: pyscope-report.html in CWD)."
    ),
    format: str = typer.Option(
        "html", "--format", "-f", help="Report format: html, json, dot, mermaid."
    ),
    exclude: list[str] = typer.Option(
        [], "--exclude", "-x", help="Additional exclude patterns (glob)."
    ),
    config: str | None = typer.Option(
        None, "--config", "-c", help="Path to pyscope.toml configuration file."
    ),
    language: str | None = typer.Option(
        None, "--language", "-l", help="Report language: ru or en."
    ),
    theme: str | None = typer.Option(None, "--theme", help="Report theme: light or dark."),
    fail_on_cycles: bool = typer.Option(
        False, "--fail-on-cycles", help="Exit with code 2 if circular dependencies are found."
    ),
    open_report: bool = typer.Option(
        False, "--open", help="Open the HTML report in the default browser."
    ),
    max_files: int = typer.Option(50000, "--max-files", help="Maximum number of files to analyze."),
) -> None:
    """Analyze a Python project and generate an architecture report."""
    root = Path(path).expanduser()
    if not root.exists():
        console.print(f"[red]{translate('cli.invalid_path', path=str(root))}[/red]")
        raise typer.Exit(code=1) from None
    if not root.is_dir():
        console.print(f"[red]{translate('cli.not_directory', path=str(root))}[/red]")
        raise typer.Exit(code=1) from None

    try:
        cfg = Config.load(config) if config else Config()
        if exclude:
            cfg.exclude_patterns = list(exclude) + list(cfg.exclude_patterns)
        cfg.max_files = max_files
        if theme:
            cfg.report_theme = theme
    except ConfigurationError as exc:
        console.print(f"[red]{translate('cli.error', message=str(exc))}[/red]")
        raise typer.Exit(code=1) from None

    lang = _resolve_language(language, cfg)

    console.print(f"[bold]{translate('cli.analyze', path=str(root))}[/bold]")
    console.print(translate("cli.discovering"))

    engine = AnalysisEngine(config=cfg, language=lang)

    try:
        with Progress(
            TextColumn("{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(translate("cli.analyzing", done="0", total="0"), total=None)

            def on_progress(done: int, total: int) -> None:
                progress.update(
                    task,
                    description=translate("cli.analyzing", done=str(done), total=str(total)),
                    completed=done,
                    total=total,
                )

            result = engine.analyze(root)
            progress.update(
                task, total=result.summary.get("files", 0), completed=result.summary.get("files", 0)
            )
    except SafetyError as exc:
        console.print(f"[red]{translate('cli.error', message=str(exc))}[/red]")
        raise typer.Exit(code=1) from None
    except AnalysisError as exc:
        console.print(f"[red]{translate('cli.error', message=str(exc))}[/red]")
        raise typer.Exit(code=1) from None
    except PyScopeError as exc:
        console.print(f"[red]{translate('cli.error', message=str(exc))}[/red]")
        raise typer.Exit(code=1) from None

    summary = result.summary
    console.print(
        translate(
            "cli.complete",
            count=str(summary.get("files", 0)),
            modules=str(summary.get("modules", 0)),
        )
    )
    if summary.get("cycles"):
        console.print(
            f"[yellow]{translate('cli.cycles_found', count=str(summary.get('cycles')))}[/yellow]"
        )
    if summary.get("findings"):
        console.print(
            f"[cyan]{translate('cli.findings', count=str(summary.get('findings')))}[/cyan]"
        )

    fmt = format.lower()
    if fmt not in ("html", "json", "dot", "mermaid"):
        console.print(f"[red]{translate('cli.error', message='unknown format: ' + fmt)}[/red]")
        raise typer.Exit(code=1) from None

    out_path = Path(output) if output else None
    if out_path is None:
        default_name = {
            "html": "pyscope-report.html",
            "json": "pyscope-report.json",
            "dot": "pyscope-graph.dot",
            "mermaid": "pyscope-graph.mmd",
        }[fmt]
        out_path = Path.cwd() / default_name

    # Safety: never write into the analyzed project tree.
    out_resolved = out_path.resolve()
    root_resolved = root.resolve()
    inside = str(out_resolved) == str(root_resolved) or str(out_resolved).startswith(
        str(root_resolved) + os.sep
    )
    if inside:
        console.print("[red]Refusing to write report inside the analyzed project.[/red]")
        raise typer.Exit(code=1) from None

    try:
        if fmt == "html":
            report_html = generate_report(result, language=lang, theme=cfg.report_theme)
            out_path.write_text(report_html, encoding="utf-8")
            console.print(translate("cli.writing_report", path=str(out_path)))
            if open_report:
                console.print(translate("cli.opening", path=str(out_path)))
                webbrowser.open(out_path.resolve().as_uri())
        elif fmt == "json":
            export_json(result, out_path)
            console.print(translate("cli.writing_json", path=str(out_path)))
        elif fmt == "dot":
            export_dot(result, out_path)
            console.print(translate("cli.writing_dot", path=str(out_path)))
        elif fmt == "mermaid":
            export_mermaid(result, out_path)
            console.print(translate("cli.writing_mermaid", path=str(out_path)))
    except OSError as exc:
        console.print(f"[red]{translate('cli.error', message=str(exc))}[/red]")
        raise typer.Exit(code=1) from None

    if fail_on_cycles and summary.get("cycles", 0) > 0:
        raise typer.Exit(code=2)


@app.command()
def version() -> None:
    """Show the PyScope version."""
    console.print(translate("cli.version", version=__version__))


def main() -> None:  # pragma: no cover - entry point
    try:
        app()
    except PyScopeError as exc:
        console.print(f"[red]{translate('cli.error', message=str(exc))}[/red]")
        raise typer.Exit(code=1) from None


if __name__ == "__main__":  # pragma: no cover
    main()
