"""Logging configuration for LinkedIn Spider."""

import logging
from pathlib import Path
from typing import Optional

from rich.logging import RichHandler

from linkedin_spider.utils.config import config


def setup_logger(
    name: str = "linkedin_spider",
    level: Optional[str] = None,
) -> logging.Logger:
    """
    Set up logger with a console handler.

    The log file is attached separately by add_file_handler, so that importing
    this package creates nothing on disk.

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger
    """
    if level is None:
        level = config.log_level

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler with Rich
    if config.console_logging:
        # markup stays off: messages carry page text and exception messages, and a
        # stray "[/x]" in them would make the logging call itself raise.
        console_handler = RichHandler(
            rich_tracebacks=True,
            markup=False,
            show_time=True,
            show_path=False,
        )
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("%(message)s", datefmt="[%X]")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger


def add_file_handler(log_file: Optional[str] = None) -> None:
    """
    Log to a file as well, replacing any log file already attached.

    Args:
        log_file: Path to log file. If None, uses config value.
    """
    log_file = log_file or config.log_file
    if not log_file:
        return

    for handler in [h for h in logger.handlers if isinstance(h, logging.FileHandler)]:
        logger.removeHandler(handler)
        handler.close()

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)


def enable_debug() -> None:
    """Turn on debug output everywhere, including the console."""
    logger.setLevel(logging.DEBUG)
    for handler in logger.handlers:
        handler.setLevel(logging.DEBUG)


# Global logger instance
logger = setup_logger()
