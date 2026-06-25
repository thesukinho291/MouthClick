import logging
import os
import sys
from pathlib import Path

from .config import PROJECT_ROOT


def default_log_dir():
    if getattr(sys, "frozen", False):
        app_data = os.getenv("APPDATA")
        if app_data:
            return Path(app_data) / "MouthClick" / "logs"

    return PROJECT_ROOT / "logs"


LOG_DIR = default_log_dir()
LOG_PATH = LOG_DIR / "mouthclick.log"


def setup_event_logger():
    LOG_DIR.mkdir(exist_ok=True)

    logger = logging.getLogger("mouthclick")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)

    return logger
