"""
Structured Logging Module for Simple Reminder List Application.

Provides thread-safe, configurable logging across application components
with file audit logging and console diagnostic output.
"""

import logging
import os
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "SimpleReminder",
    log_file: str = "logs/app.log",
    level: int = logging.INFO,
    console_output: bool = False
) -> logging.Logger:
    """
    Configure and return a structured logger instance.

    Args:
        name: Module or logger namespace name.
        log_file: Target log file destination path.
        level: Minimum logging threshold level.
        console_output: Whether to duplicate log entries to stdout.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if already configured
    if logger.handlers:
        return logger

    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # File Handler
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Optional Console Handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger


# Default application-wide root logger
logger = setup_logger()
