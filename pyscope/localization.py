"""Localization for PyScope.

Russian is the default language, English is the secondary language.  All
user-facing strings live here keyed by message id.  Technical identifiers,
JSON keys and CLI command names remain language-independent.
"""

from __future__ import annotations

from typing import Final

LANGUAGES: Final = ("ru", "en")
DEFAULT_LANGUAGE: Final = "ru"

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "ru": {
        # CLI
        "cli.analyze": "Анализ проекта: {path}",
        "cli.discovering": "Обнаружение файлов...",
        "cli.analyzing": "Анализ файлов ({done}/{total})...",
        "cli.complete": "Анализ завершён. Файлов: {count}, модулей: {modules}.",
        "cli.cycles_found": "Обнаружено циклических зависимостей: {count}.",
        "cli.findings": "Рекомендаций по архитектуре: {count}.",
        "cli.writing_report": "Запись отчёта в {path}",
        "cli.writing_json": "Запись JSON в {path}",
        "cli.writing_dot": "Запись DOT в {path}",
        "cli.writing_mermaid": "Запись Mermaid в {path}",
        "cli.opening": "Открытие отчёта: {path}",
        "cli.version": "PyScope {version}",
        "cli.error": "Ошибка: {message}",
        "cli.invalid_path": "Путь не существует: {path}",
        "cli.not_directory": "Путь не является каталогом: {path}",
        # Report
        "report.title": "PyScope — отчёт об архитектуре кода",
        "report.project_overview": "Обзор проекта",
        "report.file_statistics": "Статистика файлов",
        "report.package_structure": "Структура пакетов",
        "report.dependency_graph": "Граф зависимостей",
        "report.circular_dependencies": "Циклические зависимости",
        "report.complexity": "Сложность",
        "report.largest_files": "Самые большие файлы",
        "report.inventory": "Инвентаризация функций и классов",
        "report.findings": "Рекомендации по архитектуре",
        "report.search": "Поиск",
        "report.module_details": "Подробности модуля",
        "report.export": "Экспорт",
        "report.no_files": "Файлы не найдены",
        "report.skipped": "Пропущено файлов: {count}",
        "report.failed": "Ошибок при анализе: {count}",
        "report.language": "Язык",
        "report.theme": "Тема",
        "report.russian": "Русский",
        "report.english": "English",
        "report.light": "Светлая",
        "report.dark": "Тёмная",
        # findings
        "finding.severity.high": "Высокий",
        "finding.severity.medium": "Средний",
        "finding.severity.low": "Низкий",
        "finding.severity.info": "Информация",
        # metrics
        "metric.cyclomatic_complexity": "Цикломатическая сложность",
        "metric.code_lines": "Строк кода",
        "metric.argument_count": "Аргументов",
        "metric.nesting_depth": "Глубина вложенности",
        "metric.return_count": "Операторов return",
        "metric.annotation_coverage": "Покрытие аннотациями типов",
        "metric.docstring_coverage": "Покрытие docstring",
        # errors
        "error.syntax_error": "Ошибка синтаксиса",
        "error.encoding_error": "Ошибка кодирования",
        "error.skipped": "Пропущен",
        "error.failed": "Не удалось проанализировать",
        "error.path_traversal": "Попытка выхода за пределы корня проекта",
        "error.symlink_unsafe": "Небезопасная символическая ссылка",
    },
    "en": {
        # CLI
        "cli.analyze": "Analyzing project: {path}",
        "cli.discovering": "Discovering files...",
        "cli.analyzing": "Analyzing files ({done}/{total})...",
        "cli.complete": "Analysis complete. Files: {count}, modules: {modules}.",
        "cli.cycles_found": "Circular dependencies found: {count}.",
        "cli.findings": "Architecture recommendations: {count}.",
        "cli.writing_report": "Writing report to {path}",
        "cli.writing_json": "Writing JSON to {path}",
        "cli.writing_dot": "Writing DOT to {path}",
        "cli.writing_mermaid": "Writing Mermaid to {path}",
        "cli.opening": "Opening report: {path}",
        "cli.version": "PyScope {version}",
        "cli.error": "Error: {message}",
        "cli.invalid_path": "Path does not exist: {path}",
        "cli.not_directory": "Path is not a directory: {path}",
        # Report
        "report.title": "PyScope — Code Architecture Report",
        "report.project_overview": "Project Overview",
        "report.file_statistics": "File Statistics",
        "report.package_structure": "Package Structure",
        "report.dependency_graph": "Dependency Graph",
        "report.circular_dependencies": "Circular Dependencies",
        "report.complexity": "Complexity",
        "report.largest_files": "Largest Files",
        "report.inventory": "Function and Class Inventory",
        "report.findings": "Architecture Recommendations",
        "report.search": "Search",
        "report.module_details": "Module Details",
        "report.export": "Export",
        "report.no_files": "No files found",
        "report.skipped": "Skipped files: {count}",
        "report.failed": "Analysis failures: {count}",
        "report.language": "Language",
        "report.theme": "Theme",
        "report.russian": "Русский",
        "report.english": "English",
        "report.light": "Light",
        "report.dark": "Dark",
        # findings
        "finding.severity.high": "High",
        "finding.severity.medium": "Medium",
        "finding.severity.low": "Low",
        "finding.severity.info": "Info",
        # metrics
        "metric.cyclomatic_complexity": "Cyclomatic Complexity",
        "metric.code_lines": "Code Lines",
        "metric.argument_count": "Arguments",
        "metric.nesting_depth": "Nesting Depth",
        "metric.return_count": "Return Statements",
        "metric.annotation_coverage": "Type Annotation Coverage",
        "metric.docstring_coverage": "Docstring Coverage",
        # errors
        "error.syntax_error": "Syntax Error",
        "error.encoding_error": "Encoding Error",
        "error.skipped": "Skipped",
        "error.failed": "Failed to analyze",
        "error.path_traversal": "Path traversal outside project root",
        "error.symlink_unsafe": "Unsafe symlink",
    },
}


def translate(key: str, language: str = DEFAULT_LANGUAGE, **kwargs: str) -> str:
    """Translate ``key`` for ``language``, formatting with ``kwargs``."""
    table = _TRANSLATIONS.get(language, _TRANSLATIONS[DEFAULT_LANGUAGE])
    message = table.get(key, key)
    if kwargs:
        try:
            message = message.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return message
