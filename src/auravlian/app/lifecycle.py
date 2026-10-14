"""Logging and persistence lifecycle."""
import logging
from logging.handlers import RotatingFileHandler

from auravlian.shared.paths import data_path


def configure_logging() -> None:
    logger = logging.getLogger("auravlian")
    if logger.handlers:
        return
    handler = RotatingFileHandler(
        data_path() / "auravlian.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter(
        '{"time":"%(asctime)s","level":"%(levelname)s","message":%(message)s}'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

