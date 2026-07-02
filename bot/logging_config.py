"""Centralised logging configuration.

Two handlers on a single named logger:
  * a file handler (DEBUG) that records full request/response/error detail,
  * a console handler (INFO) that shows the user clean, non-noisy output.
"""

import logging
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "trading_bot.log"

_FILE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_CONSOLE_FORMAT = "%(levelname)-8s | %(message)s"


def get_logger(name: str = "trading_bot") -> logging.Logger:
    """Return a configured logger, creating handlers only once."""
    logger = logging.getLogger(name)
    if logger.handlers:  # already configured — reuse it
        return logger

    logger.setLevel(logging.DEBUG)

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(_FILE_FORMAT))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(_CONSOLE_FORMAT))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False
    return logger
