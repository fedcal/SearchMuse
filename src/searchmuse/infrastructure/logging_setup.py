"""Logging configuration for SearchMuse.

Sets up the root logger with stderr and optional file handlers based
on the application LoggingConfig.
"""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from searchmuse.infrastructure.config import LoggingConfig

_LOG_FORMAT_WITH_TIMESTAMP: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_LOG_FORMAT_WITHOUT_TIMESTAMP: str = "[%(levelname)s] %(name)s: %(message)s"
_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


def setup_logging(config: LoggingConfig) -> None:
    """Configure the root logger from the application LoggingConfig.

    Sets the log level, adds a stderr StreamHandler, and optionally
    adds a FileHandler when ``config.file`` is not None.

    Args:
        config: Frozen logging configuration with level, file path,
            and timestamp toggle.
    """
    level = getattr(logging, config.level.upper(), logging.INFO)
    fmt = _LOG_FORMAT_WITH_TIMESTAMP if config.timestamps else _LOG_FORMAT_WITHOUT_TIMESTAMP

    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing handlers to avoid duplicates on repeated calls
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    formatter = logging.Formatter(fmt, datefmt=_DATE_FORMAT)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(level)
    stderr_handler.setFormatter(formatter)
    root.addHandler(stderr_handler)

    if config.file is not None:
        from pathlib import Path

        log_path = Path(config.file).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(str(log_path), encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
