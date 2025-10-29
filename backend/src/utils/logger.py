import logging
from typing import Optional

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"


def _configure_root_logger(level: int = logging.INFO) -> None:
    """Configure the root logger once with a standard format."""
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        root_logger.addHandler(handler)
    root_logger.setLevel(level)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a module-level logger with standard configuration."""
    _configure_root_logger()
    return logging.getLogger(name)
