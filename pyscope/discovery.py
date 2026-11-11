"""Project discovery.

Discovers Python source files, packages and configuration while respecting
exclusions, ``.gitignore`` and symlink safety.  Never executes or imports
anything from the target project.
"""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .config import DEFAULT_EXCLUDES

GITIGNORE_NAME = ".gitignore"
CONFIG_NAME = "pyscope.toml"


@dataclass
class DiscoveredFile:
    path: Path  # absolute path
    relative: str  # path relative to project root, POSIX separators


@dataclass
class DiscoveryResult:
    files: list[DiscoveredFile] = field(default_factory=list)
    packages: list[str] = field(default_factory=list)  # dirs with __init__.py
    config_path: Path | None = None
    ignored_count: int = 0


def _is_within_root(child: Path, root: Path) -> bool:
    """Return True if ``child`` is inside ``root`` (resolved)."""
    try:
        child.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False


def _load_gitignore_patterns(root: Path) -> list[str]:
    """Parse a simple .gitignore into glob patterns."""
    gitignore = root / GITIGNORE_NAME
    patterns: list[str] = []
    if not gitignore.is_file():
        return patterns
    try:
        text = gitignore.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return patterns
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        patterns.append(stripped)
    return patterns


def _matches_any(name: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(name, pat) for pat in patterns)


def _component_match(part: str, pat: str) -> bool:
    return fnmatch.fnmatch(part, pat)


def _match_parts(path_parts: list[str], pat_parts: list[str]) -> bool:
    """Glob match where ``**`` matches zero or more path components."""
    i = j = 0
    star_idx = -1
    match_idx = 0
    while i < len(path_parts):
        if j < len(pat_parts) and pat_parts[j] == "**":
            star_idx = j
            match_idx = i
            j += 1
        elif j < len(pat_parts) and _component_match(path_parts[i], pat_parts[j]):
            i += 1
            j += 1
        elif star_idx >= 0:
            j = star_idx + 1
            match_idx += 1
            i = match_idx
        else:
            return False
    while j < len(pat_parts) and pat_parts[j] == "**":
        j += 1
    return j == len(pat_parts)


def _path_matches(relative: str, patterns: list[str]) -> bool:
    """Match a relative POSIX path against glob patterns.

    ``**`` matches zero or more directory components.  A pattern without a
    slash is matched against any single path component (basename semantics).
    """
    parts = relative.replace("\\", "/").split("/")
    for pat in patterns:
        pat = pat.strip()
        if not pat:
            continue
        # trailing slash: match the directory and everything beneath it
        if pat.endswith("/"):
            pat = pat[:-1]
        pat_parts = pat.replace("\\", "/").split("/")
        if "/" not in pat:
            # basename semantics: matches any component
            if any(_component_match(p, pat) for p in parts):
                return True
            continue
        if _match_parts(parts, pat_parts):
            return True
    return False


def discover_project(
    root: str | os.PathLike[str],
    *,
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
    default_excludes: list[str] | None = None,
    respect_gitignore: bool = True,
    follow_symlinks: bool = False,
    max_files: int = 50_000,
) -> DiscoveryResult:
    """Discover Python files under ``root``.

    Returns a :class:`DiscoveryResult`.  Does not follow symlinks that point
    outside the project root unless ``follow_symlinks`` is True.
    """
    root_path = Path(root).expanduser().resolve(strict=False)
    if not root_path.exists():
        raise FileNotFoundError(f"Project root does not exist: {root}")
    if not root_path.is_dir():
        raise NotADirectoryError(f"Project root is not a directory: {root}")

    include = include_patterns or ["**/*.py"]
    exclude = list(exclude_patterns or [])
    defaults = list(default_excludes or DEFAULT_EXCLUDES)

    gitignore_patterns = _load_gitignore_patterns(root_path) if respect_gitignore else []

    files: list[DiscoveredFile] = []
    packages: list[str] = []
    ignored = 0

    seen_real: set[str] = set()

    for dirpath, dirnames, filenames in os.walk(
        root_path, topdown=True, followlinks=follow_symlinks
    ):
        current = Path(dirpath)

        # Filter directories in place.
        kept_dirs: list[str] = []
        for d in dirnames:
            dpath = current / d
            rel = dpath.relative_to(root_path).as_posix()
            real = str(dpath.resolve(strict=False))

            # Default exclusions (by directory name).
            if _matches_any(d, defaults):
                ignored += 1
                continue
            # User exclusions.
            if _path_matches(rel, exclude):
                ignored += 1
                continue
            # Gitignore.
            if _path_matches(rel, gitignore_patterns):
                ignored += 1
                continue
            # Symlink safety.
            if dpath.is_symlink() and not follow_symlinks:
                target = dpath.resolve(strict=False)
                if not _is_within_root(target, root_path):
                    ignored += 1
                    continue
            # Avoid duplicate real paths (hardlinked/symlinked dirs inside root).
            if real in seen_real:
                ignored += 1
                continue
            seen_real.add(real)
            kept_dirs.append(d)

            # Package detection: __init__.py makes a directory a package.
            if (dpath / "__init__.py").is_file():
                packages.append(rel)

        dirnames[:] = kept_dirs

        for filename in filenames:
            if len(files) >= max_files:
                break
            if not filename.endswith(".py"):
                continue
            fpath = current / filename
            rel = fpath.relative_to(root_path).as_posix()

            # Default excludes by filename.
            if _matches_any(filename, defaults):
                ignored += 1
                continue
            if _path_matches(rel, exclude):
                ignored += 1
                continue
            if _path_matches(rel, gitignore_patterns):
                ignored += 1
                continue
            if fpath.is_symlink() and not follow_symlinks:
                target = fpath.resolve(strict=False)
                if not _is_within_root(target, root_path):
                    ignored += 1
                    continue
            # Include pattern filter.
            if not _path_matches(rel, include):
                ignored += 1
                continue
            files.append(DiscoveredFile(path=fpath, relative=rel))
        if len(files) >= max_files:
            break

    # Configuration file detection.
    config_path: Path | None = None
    candidate = root_path / CONFIG_NAME
    if candidate.is_file():
        config_path = candidate

    return DiscoveryResult(
        files=files,
        packages=sorted(set(packages)),
        config_path=config_path,
        ignored_count=ignored,
    )
