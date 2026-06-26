import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "run_id": getattr(record, "run_id", "-"),
            "trace_id": getattr(record, "trace_id", "-"),
            "span_id": getattr(record, "span_id", "-"),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class LogContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        for key in ("run_id", "trace_id", "span_id"):
            if not hasattr(record, key):
                setattr(record, key, "-")
        return True


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(LogContextFilter())
    root = logging.getLogger()
    if not root.handlers:
        root.addHandler(handler)
    else:
        for existing in root.handlers:
            existing.setFormatter(JsonFormatter())
            existing.addFilter(LogContextFilter())
    root.setLevel(logging.INFO)
