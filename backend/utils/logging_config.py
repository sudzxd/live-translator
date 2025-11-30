"""Logging configuration with verbose mode support."""

# =============================================================================
# 1. IMPORTS
# =============================================================================

# Standard library
import logging
import sys

# Project/local
from .constants import LOG_DATE_FORMAT, LOG_FORMAT

# =============================================================================
# 2. TYPES & CONSTANTS
# =============================================================================

# Module state
_verbose_mode: bool = False
_LOGGERS: dict[str, logging.Logger] = {}


# =============================================================================
# 3. PUBLIC API / MAIN ENTRY POINTS
# =============================================================================


def setup_logging(verbose: bool = False) -> None:
    """Configure application-wide logging.

    Args:
        verbose: If True, set log level to DEBUG; otherwise INFO.
    """
    global _verbose_mode
    _verbose_mode = verbose

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        fmt=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )
    console_handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Suppress noisy third-party loggers unless verbose
    if not verbose:
        logging.getLogger("PIL").setLevel(logging.WARNING)
        logging.getLogger("paddleocr").setLevel(logging.WARNING)
        logging.getLogger("ppocr").setLevel(logging.WARNING)
        logging.getLogger("transformers").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a module.

    Args:
        name: Module name (use __name__).

    Returns:
        Configured logger for the module.
    """
    if name in _LOGGERS:
        return _LOGGERS[name]

    logger = logging.getLogger(name)
    _LOGGERS[name] = logger
    return logger


def is_verbose() -> bool:
    """Check if verbose mode is active.

    Returns:
        True if verbose logging is enabled, False otherwise.
    """
    return _verbose_mode
