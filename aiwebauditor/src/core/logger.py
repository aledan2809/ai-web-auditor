"""
Logging setup for AIWebAuditor
"""

import logging
import os
from datetime import datetime


def setup_logger(output_dir: str = None, name: str = "aiwebauditor") -> logging.Logger:
    """Configure logging to file and console."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler (INFO level)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console_fmt = logging.Formatter("[%(levelname)s] %(message)s")
    console.setFormatter(console_fmt)
    logger.addHandler(console)

    # File handler (DEBUG level)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        log_path = os.path.join(output_dir, "aiwebauditor.log")
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_fmt = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_fmt)
        logger.addHandler(file_handler)

    return logger
