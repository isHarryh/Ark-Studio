# Copyright (c) 2024-2026, Harry Huang
# @ BSD 3-Clause License
import sys
from loguru import logger

logger.remove()

logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level:<5}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
    level="DEBUG",
    colorize=True,
)

__all__ = ["logger"]
