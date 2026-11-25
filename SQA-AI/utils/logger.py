"""
Logging Configuration for SQA-AI
Provides consistent logging across all modules.
Supports colored console output using Rich when available.

This version is compatible with main.py expectations:
- SafeFileReader
- scan_start / scan_complete / scan_failed
- file_error / error_with_context
- cicd_gate_result
- recommendation_logged
"""

import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Try to import Rich for colored output
try:
    from rich.console import Console
    from rich.logging import RichHandler
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class Logger:
    """
    Custom logger for SQA-AI.
    Supports file + console logging and optional Rich colored output.
    """

    _loggers: Dict[str, logging.Logger] = {}
    _config = None

    def __init__(self, name: str, log_file: Optional[str] = None):
        self.name = name
        self._load_config()
        self.log_file = log_file or self._get_log_file()
        self.logger = self._get_or_create_logger()

    def _load_config(self) -> None:
        """Load config lazily to avoid circular imports"""
        if Logger._config is None:
            try:
                from .config import config
                Logger._config = config
            except ImportError:
                Logger._config = None

    def _get_log_file(self) -> str:
        if Logger._config:
            return Logger._config.log_file
        return "sqa_ai.log"

    def _get_log_level_str(self) -> str:
        if Logger._config:
            return Logger._config.log_level
        return "INFO"

    def _get_log_level(self) -> int:
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        return level_map.get(self._get_log_level_str().upper(), logging.INFO)

    def _use_colors(self) -> bool:
        # config uses dot notation keys via config.get()
        if Logger._config:
            try:
                return Logger._config.get("logging.console_colors", True) and RICH_AVAILABLE
            except Exception:
                return RICH_AVAILABLE
        return RICH_AVAILABLE

    def _get_or_create_logger(self) -> logging.Logger:
        if self.name in Logger._loggers:
            return Logger._loggers[self.name]

        logger = logging.getLogger(self.name)
        logger.setLevel(self._get_log_level())
        logger.propagate = False

        if not logger.handlers:
            self._add_handlers(logger)

        Logger._loggers[self.name] = logger
        return logger

    def _add_handlers(self, logger: logging.Logger) -> None:
        # Console handler
        if self._use_colors():
            console_handler = RichHandler(
                console=Console(stderr=True),
                show_time=True,
                show_level=True,
                show_path=False,
                markup=True,
            )
            console_handler.setLevel(self._get_log_level())
        else:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self._get_log_level())
            console_format = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%H:%M:%S",
            )
            console_handler.setFormatter(console_format)

        logger.addHandler(console_handler)

        # File handler
        try:
            log_path = Path(self.log_file)
            if log_path.parent and str(log_path.parent) != ".":
                log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(file_format)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not create file handler: {e}")

    # ---------------- Basic logging ----------------

    def debug(self, message: str) -> None:
        self.logger.debug(message)

    def info(self, message: str) -> None:
        self.logger.info(message)

    def warning(self, message: str) -> None:
        self.logger.warning(message)

    def error(self, message: str, exc_info: bool = False) -> None:
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message: str, exc_info: bool = False) -> None:
        self.logger.critical(message, exc_info=exc_info)

    def exception(self, message: str) -> None:
        self.logger.exception(message)

    # ---------------- Convenience UI-ish logs ----------------

    def success(self, message: str) -> None:
        if self._use_colors():
            self.logger.info(f"[green]✓[/green] {message}")
        else:
            self.logger.info(f"✓ {message}")

    def failure(self, message: str) -> None:
        if self._use_colors():
            self.logger.error(f"[red]✗[/red] {message}")
        else:
            self.logger.error(f"✗ {message}")

    # ---------------- US11: Robust context logging ----------------

    def error_with_context(
        self,
        message: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        function_name: Optional[str] = None,
        exception: Optional[Exception] = None,
    ) -> None:
        ctx = []
        if file_path:
            ctx.append(f"file={file_path}")
        if line_number:
            ctx.append(f"line={line_number}")
        if function_name:
            ctx.append(f"func={function_name}")

        ctx_str = " | ".join(ctx) if ctx else "no-context"
        full = f"{message} [{ctx_str}]"

        if exception:
            full += f" | {type(exception).__name__}: {exception}"
            # full traceback into debug (file)
            self.debug("Traceback:\n" + traceback.format_exc())

        self.error(full)

    def file_error(self, file_path: str, error_type: str, details: str, recoverable: bool = True) -> None:
        status = "RECOVERABLE" if recoverable else "FATAL"
        msg = f"[{status}] {error_type} | {file_path} | {details}"
        if recoverable:
            self.warning(msg)
        else:
            self.critical(msg)

    # ---------------- Scan lifecycle helpers ----------------

    def scan_start(self, path: str) -> None:
        sep = "=" * 50
        self.info(sep)
        self.info(f"SCAN STARTED: {path}")
        self.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.info(sep)

    def scan_complete(self, files_count: int, duration: float) -> None:
        sep = "=" * 50
        self.info(sep)
        self.success(f"SCAN COMPLETE: {files_count} files analyzed")
        self.info(f"Duration: {duration:.2f} seconds")
        self.info(sep)

    def scan_failed(self, reason: str, duration: float) -> None:
        sep = "=" * 50
        self.critical(sep)
        self.failure(f"SCAN FAILED: {reason}")
        self.info(f"Duration before failure: {duration:.2f} seconds")
        self.critical(sep)

    def ddi_calculated(self, file: str, score: float, risk: str) -> None:
        risk_colors = {"LOW": "green", "MEDIUM": "yellow", "HIGH": "red", "CRITICAL": "bold red"}
        if self._use_colors():
            color = risk_colors.get(str(risk).upper(), "white")
            self.logger.info(
                f"DDI | {file} | Score: {score:.2f} | Risk: [{color}]{risk}[/{color}]"
            )
        else:
            self.logger.info(f"DDI | {file} | Score: {score:.2f} | Risk: {risk}")

    # ---------------- US12: CI gate logging ----------------

    def cicd_gate_result(self, passed: bool, critical_count: int, threshold: int) -> None:
        sep = "=" * 50
        self.info(sep)
        if passed:
            self.success(f"CI/CD QUALITY GATE: PASSED (threshold={threshold})")
        else:
            self.critical(f"CI/CD QUALITY GATE: FAILED (threshold={threshold})")
            self.critical(f"Critical files: {critical_count}")
        self.info(sep)

    # ---------------- Recommendation logging (location-aware) ----------------

    def recommendation_logged(
        self,
        severity: str,
        file_path: str,
        location: str,
        issue: str,
        suggestion: str,
    ) -> None:
        sev = str(severity).upper()
        msg = (
            f"RECOMMENDATION [{sev}]\n"
            f"  File: {file_path}\n"
            f"  Location: {location}\n"
            f"  Issue: {issue}\n"
            f"  Suggestion: {suggestion}"
        )
        if sev in ("CRITICAL", "HIGH"):
            self.warning(msg)
        else:
            self.info(msg)


class SafeFileReader:
    """
    Safe file reader (US11).
    Not currently used by your main.py scan loop (parser handles reading),
    but main.py imports it, so it MUST exist.
    """

    MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024  # 2MB
    BINARY_CHECK_SIZE = 8192

    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or get_logger("SafeFileReader")

    def read(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        try:
            p = Path(file_path)
            if not p.exists():
                return None, "File not found"
            if not p.is_file():
                return None, "Not a file"

            size = p.stat().st_size
            if size > self.MAX_FILE_SIZE_BYTES:
                self.logger.file_error(file_path, "SIZE_LIMIT", f"{size} bytes", recoverable=True)
                return None, "File too large"

            if self._is_binary(file_path):
                return None, "Binary file"

            return self._read_with_fallback(file_path), None

        except Exception as e:
            self.logger.file_error(file_path, "READ_ERROR", str(e), recoverable=True)
            return None, str(e)

    def _is_binary(self, file_path: str) -> bool:
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(self.BINARY_CHECK_SIZE)
                if b"\x00" in chunk:
                    return True
                non_printable = sum(1 for b in chunk if b < 32 and b not in (9, 10, 13))
                return (len(chunk) > 0) and (non_printable / len(chunk) > 0.3)
        except Exception:
            return True

    def _read_with_fallback(self, file_path: str) -> str:
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()


def get_logger(name: str) -> Logger:
    """Factory function to get logger instance"""
    return Logger(name)
    