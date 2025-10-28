"""
Ядро системы: логирование, исключения, базовые утилиты
"""

from .logger import get_logger, setup_logging
from .exceptions import (
    BotException,
    ConfigurationError,
    APIError,
    APIConnectionError,
    APIRateLimitError,
    GenerationError,
    ModerationError,
)

__all__ = [
    "get_logger",
    "setup_logging",
    "BotException",
    "ConfigurationError",
    "APIError",
    "APIConnectionError",
    "APIRateLimitError",
    "GenerationError",
    "ModerationError",
]

