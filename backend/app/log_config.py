"""Centralized logging configuration with structured JSON output for Loki."""
import json
import logging
import os
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Output log records as JSON lines for Loki ingestion.

    Captures standard fields plus any extra= context passed by loggers
    (both ExtraLogger adapter and plain logging.getLogger usage).
    """

    # Standard LogRecord attrs that should not be treated as extra context
    STANDARD_ATTRS = frozenset({
        "args", "asctime", "created", "exc_info", "exc_text", "filename",
        "funcName", "levelname", "levelno", "lineno", "message", "module",
        "msecs", "msg", "name", "pathname", "process", "processName",
        "relativeCreated", "stack_info", "thread", "threadName",
    })

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info and record.exc_info[0]:
            entry["exception"] = self.formatException(record.exc_info)

        # Merge explicitly-passed extra_fields via ExtraLogger
        if hasattr(record, "extra_fields") and record.extra_fields:
            entry.update(record.extra_fields)

        # Merge any other non-standard LogRecord attributes.
        # Catches modules using logging.getLogger(__name__) with extra={} directly.
        for key, value in record.__dict__.items():
            if key in self.STANDARD_ATTRS or key in entry:
                continue
            if key.startswith("_") or callable(value) or isinstance(value, type):
                continue
            try:
                entry[key] = value
            except Exception:
                pass

        return json.dumps(entry, default=str)


class ExtraLogger(logging.LoggerAdapter):
    """Logger adapter that allows passing extra= fields inline."""

    def process(self, msg, kwargs):
        extra = kwargs.pop("extra", {})
        return msg, {"extra": extra}


def setup_logging(service_name: str = "pantry-helper"):
    """Configure structured JSON logging to stdout.

    Reads LOG_LEVEL from env (default INFO).
    Returns an ExtraLogger adapter that accepts extra= dict fields.
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    root.setLevel(level)
    for h in root.handlers[:]:
        root.removeHandler(h)
    root.addHandler(handler)

    logger = logging.getLogger(service_name)
    logger.setLevel(level)

    # Quiet noisy libs
    for noisy in ("httpx", "urllib3", "PIL", "google", "openai", "httpcore", "asyncio", "chardet"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    return ExtraLogger(logger, {})
