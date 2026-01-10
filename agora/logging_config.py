"""
Centralized logging configuration for Agora SDK.

This module provides easy-to-use functions to configure logging across all Agora components.
Users can enable verbose, step-by-step logging to make debugging trivial.

Usage:
    >>> from agora.logging_config import enable_verbose_logging
    >>> enable_verbose_logging()  # Enable DEBUG level logging with detailed format

    >>> from agora.logging_config import enable_file_logging
    >>> enable_file_logging("agora_debug.log")  # Log to file

    >>> from agora.logging_config import setup_structured_logging
    >>> setup_structured_logging(level="INFO")  # JSON-formatted logs
"""

import logging
import sys
import json
from datetime import datetime
from typing import Optional


# ======================================================================
# PRE-CONFIGURED LOG FORMATS
# ======================================================================

# Verbose format with all context
VERBOSE_FORMAT = (
    "[%(asctime)s] [%(levelname)-8s] [%(name)s:%(funcName)s:%(lineno)d] "
    "%(message)s"
)

# Simple format for console
SIMPLE_FORMAT = "[%(levelname)-8s] %(name)s: %(message)s"

# JSON format for structured logging
class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging systems."""

    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Add custom fields if present
        if hasattr(record, "correlation_id"):
            log_obj["correlation_id"] = record.correlation_id

        return json.dumps(log_obj)


# ======================================================================
# LOGGING SETUP FUNCTIONS
# ======================================================================

def enable_verbose_logging(level: str = "DEBUG", format_string: Optional[str] = None):
    """
    Enable verbose logging across all Agora modules.

    This configures the root logger and all Agora loggers to output detailed
    debug information. Perfect for troubleshooting and understanding execution flow.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Optional custom format string (defaults to VERBOSE_FORMAT)

    Example:
        >>> from agora.logging_config import enable_verbose_logging
        >>> enable_verbose_logging()  # Enable DEBUG logging
        >>> enable_verbose_logging(level="INFO")  # Less verbose
    """
    log_format = format_string or VERBOSE_FORMAT

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  # Override any existing configuration
    )

    # Ensure all Agora modules use this configuration
    agora_modules = [
        "agora",
        "agora.telemetry",
        "agora.engine",
        "agora.tracer",
        "agora.agora_tracer",
        "agora.supabase_uploader",
        "agora.cloud_uploader",
        "agora.wide_events",
        "agora.instrument",
    ]

    for module in agora_modules:
        logger = logging.getLogger(module)
        logger.setLevel(getattr(logging, level.upper()))

    logging.info(f"[logging_config] Verbose logging enabled at level: {level}")


def enable_simple_logging(level: str = "INFO"):
    """
    Enable simple, concise logging for production use.

    Args:
        level: Logging level (default: INFO)

    Example:
        >>> from agora.logging_config import enable_simple_logging
        >>> enable_simple_logging()
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=SIMPLE_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    logging.info(f"[logging_config] Simple logging enabled at level: {level}")


def enable_file_logging(
    filename: str,
    level: str = "DEBUG",
    format_string: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
):
    """
    Enable logging to a file with rotation.

    Args:
        filename: Path to log file
        level: Logging level (default: DEBUG)
        format_string: Optional custom format (defaults to VERBOSE_FORMAT)
        max_bytes: Maximum file size before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)

    Example:
        >>> from agora.logging_config import enable_file_logging
        >>> enable_file_logging("agora_debug.log")
    """
    from logging.handlers import RotatingFileHandler

    log_format = format_string or VERBOSE_FORMAT

    # Create rotating file handler
    handler = RotatingFileHandler(
        filename, maxBytes=max_bytes, backupCount=backup_count
    )
    handler.setLevel(getattr(logging, level.upper()))
    handler.setFormatter(logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S"))

    # Add to root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(handler)

    # Also log to console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # Less verbose on console
    console_handler.setFormatter(logging.Formatter(SIMPLE_FORMAT))
    root_logger.addHandler(console_handler)

    logging.info(f"[logging_config] File logging enabled: {filename}")


def setup_structured_logging(level: str = "INFO", pretty_print: bool = False):
    """
    Enable JSON-structured logging for log aggregation systems (e.g., ELK, Datadog).

    Args:
        level: Logging level (default: INFO)
        pretty_print: Pretty-print JSON for human readability (default: False)

    Example:
        >>> from agora.logging_config import setup_structured_logging
        >>> setup_structured_logging()
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.handlers = []  # Clear existing handlers
    root_logger.addHandler(handler)

    logging.info(f"[logging_config] Structured JSON logging enabled at level: {level}")


def disable_logging():
    """
    Disable all logging (sets level to CRITICAL+1, effectively silencing logs).

    Example:
        >>> from agora.logging_config import disable_logging
        >>> disable_logging()
    """
    logging.basicConfig(level=logging.CRITICAL + 1, force=True)
    logging.getLogger("agora").setLevel(logging.CRITICAL + 1)


# ======================================================================
# CORRELATION ID SUPPORT
# ======================================================================

class CorrelationFilter(logging.Filter):
    """
    Add correlation_id to log records for cross-layer tracking.

    Usage:
        >>> from agora.logging_config import CorrelationFilter, get_correlation_id, set_correlation_id
        >>> handler.addFilter(CorrelationFilter())
        >>> set_correlation_id("unique-request-id-123")
        >>> logger.info("This log will have correlation_id attached")
    """

    def filter(self, record):
        record.correlation_id = get_correlation_id()
        return True


_correlation_id = None


def set_correlation_id(correlation_id: str):
    """Set a correlation ID for cross-layer log tracking."""
    global _correlation_id
    _correlation_id = correlation_id


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID."""
    return _correlation_id


def clear_correlation_id():
    """Clear the correlation ID."""
    global _correlation_id
    _correlation_id = None


# ======================================================================
# USAGE EXAMPLES
# ======================================================================

if __name__ == "__main__":
    print("=== Agora Logging Configuration Examples ===\n")

    print("Example 1: Enable verbose logging")
    print(">>> from agora.logging_config import enable_verbose_logging")
    print(">>> enable_verbose_logging()\n")

    print("Example 2: Enable file logging")
    print(">>> from agora.logging_config import enable_file_logging")
    print(">>> enable_file_logging('agora_debug.log')\n")

    print("Example 3: Enable structured JSON logging")
    print(">>> from agora.logging_config import setup_structured_logging")
    print(">>> setup_structured_logging()\n")

    print("Example 4: Use correlation IDs")
    print(">>> from agora.logging_config import set_correlation_id")
    print(">>> set_correlation_id('request-123')")
    print(">>> # All subsequent logs will include this correlation_id\n")

    print("Example 5: Disable all logging")
    print(">>> from agora.logging_config import disable_logging")
    print(">>> disable_logging()\n")
