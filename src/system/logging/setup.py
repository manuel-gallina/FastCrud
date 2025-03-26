import datetime
import logging
import sys
from logging.handlers import TimedRotatingFileHandler

from system.logging.settings import LoggingFormatter
from system.settings import get_logging_settings


# noinspection PyPep8Naming,PyUnusedLocal
def _formatTime(  # pylint: disable=invalid-name
    record: logging.LogRecord,
    datefmt=None,  # pylint: disable=unused-argument
):
    """Override the original formatTime method to use a timezone-aware
    timestamp, compatible with both ISO 8601 and RFC 3339."""
    return (
        datetime.datetime.fromtimestamp(record.created, datetime.timezone.utc)
        .astimezone()
        .isoformat(timespec="milliseconds")
    )


def init_logging() -> logging.Logger:
    settings = get_logging_settings()

    logger = logging.getLogger()
    logger.setLevel(settings.root_level.upper())

    plain_formatter = logging.Formatter(fmt=settings.format)
    plain_formatter.formatTime = _formatTime

    formatters = {
        LoggingFormatter.PLAIN: plain_formatter,
    }

    if settings.file.enabled:
        file_handler = TimedRotatingFileHandler(
            settings.file.path,
            when="midnight",
            backupCount=settings.file.backup_count,
        )
        file_handler.setLevel(settings.file.root_level.upper())
        formatter = formatters[settings.file.formatter]
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if settings.console.enabled:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(settings.console.root_level.upper())
        formatter = formatters[settings.console.formatter]
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    for module, level in settings.module_levels.items():
        logging.getLogger(module).setLevel(level.upper())

    logger.info("Logging initialized")
    return logger
