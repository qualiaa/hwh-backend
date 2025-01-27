import logging
from enum import StrEnum
from typing import Optional

logger = logging.getLogger("hwh_backend")


class LogLevel(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"


def _parse_verbose_level(config_settings: Optional[dict[str, str]] = None) -> int:
    """Parse verbosity level from config settings.
    During pip install/build, verbosity is passed via --config-setting verbose="debug"
    """
    log_level = LogLevel.WARNING
    if not config_settings:
        return logging.WARNING

    if log_level_str := config_settings.get("verbose"):
        try:
            log_level = LogLevel(log_level_str)
        except ValueError:
            logger.error(f"Log level {log_level_str} is not valid log level")

    match log_level:
        case LogLevel.DEBUG:
            return logging.DEBUG
        case LogLevel.INFO:
            return logging.INFO
        case LogLevel.WARNING:
            return logging.WARNING


def setup_logging(config_settings: Optional[dict[str, str]] = None):
    """Configure logging based on config settings."""
    log_level = _parse_verbose_level(config_settings)

    logger.setLevel(log_level)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console handler
    ch = logging.StreamHandler()
    ch.setLevel(log_level)

    # Format to match pip's output style
    if log_level >= logging.WARNING:
        formatter = logging.Formatter("  hwh-backend: %(message)s")
    else:
        formatter = logging.Formatter("%(levelname)s: hwh-backend: %(message)s")

    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Log initial setup
    if log_level >= logging.WARNING:
        logger.debug(f"Backend logging initialized (verbosity={log_level})")
