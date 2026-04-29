"""
Simple logging setup for summarizvid bot.
Creates rotating log files in ./logs/ directory.
"""
from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path

_NOISY_LOGGERS = (
    "httpx", "httpcore", "telegram", "hpack", "urllib3", "asyncio",
)
_FMT = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s | %(message)s")


def setup_bot_logging(logger_name: str, base_file: str) -> logging.Logger:
    logs_dir = Path(base_file).parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    handlers = [
        # worklog.txt — INFO+, 10 MB × 5
        _make_handler(logs_dir / "worklog.txt", logging.INFO, 10 * 1024 * 1024, 5),
        # errors.txt — ERROR+, 5 MB × 3
        _make_handler(logs_dir / "errors.txt", logging.ERROR, 5 * 1024 * 1024, 3),
        # console
        _make_stream_handler(),
    ]

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.INFO)
    for h in handlers:
        root.addHandler(h)

    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)

    return logging.getLogger(logger_name)


def _make_handler(path: Path, level: int, max_bytes: int, backup: int):
    h = logging.handlers.RotatingFileHandler(
        path, maxBytes=max_bytes, backupCount=backup, encoding="utf-8"
    )
    h.setLevel(level)
    h.setFormatter(_FMT)
    return h


def _make_stream_handler():
    h = logging.StreamHandler(sys.stdout)
    h.setLevel(logging.INFO)
    h.setFormatter(_FMT)
    return h
