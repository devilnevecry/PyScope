"""Exceptions used by PyScope."""


class PyScopeError(Exception):
    """Base exception for PyScope errors."""


class AnalysisError(PyScopeError):
    """Raised when analysis of a project fails."""


class ConfigurationError(PyScopeError):
    """Raised when configuration is invalid."""


class SafetyError(PyScopeError):
    """Raised when a safety violation is detected."""


class FileSkippedError(PyScopeError):
    """Raised when a file is intentionally skipped."""


class ExportError(PyScopeError):
    """Raised when an export fails."""


class ReportError(PyScopeError):
    """Raised when report generation fails."""
