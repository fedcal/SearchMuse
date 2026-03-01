"""Tests for searchmuse.infrastructure.logging_setup."""

import logging

from searchmuse.infrastructure.config import LoggingConfig
from searchmuse.infrastructure.logging_setup import setup_logging


def test_setup_logging_configures_root_level():
    config = LoggingConfig(level="WARNING", file=None, timestamps=True)
    setup_logging(config)
    assert logging.getLogger().level == logging.WARNING


def test_setup_logging_adds_stderr_handler():
    config = LoggingConfig(level="DEBUG", file=None, timestamps=False)
    setup_logging(config)
    root = logging.getLogger()
    assert any(isinstance(h, logging.StreamHandler) for h in root.handlers)


def test_setup_logging_with_file(tmp_path):
    log_file = tmp_path / "test.log"
    config = LoggingConfig(level="INFO", file=str(log_file), timestamps=True)
    setup_logging(config)
    root = logging.getLogger()
    file_handlers = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) >= 1
    # Cleanup
    for h in file_handlers:
        h.close()


def test_setup_logging_removes_previous_handlers():
    config = LoggingConfig(level="DEBUG", file=None, timestamps=True)
    setup_logging(config)
    count_before = len(logging.getLogger().handlers)
    setup_logging(config)
    count_after = len(logging.getLogger().handlers)
    assert count_after <= count_before


def test_setup_logging_without_timestamps():
    config = LoggingConfig(level="INFO", file=None, timestamps=False)
    setup_logging(config)
    root = logging.getLogger()
    handler = root.handlers[0]
    assert handler.formatter is not None
    assert "asctime" not in (handler.formatter._fmt or "")
