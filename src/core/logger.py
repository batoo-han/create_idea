"""
Система логирования с ротацией и несколькими уровнями

Поддерживает:
- Запись в файл с автоматической ротацией по размеру
- Вывод в консоль для разработки
- Несколько уровней логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Форматирование с временем, уровнем и модулем
- Ограничение размера лог-файлов
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


# Глобальный флаг инициализации
_logging_initialized = False


def setup_logging(
    log_level: str = "INFO",
    log_file: str = "logs/bot.log",
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
    log_format: str = "detailed"
) -> None:
    """
    Настройка системы логирования
    
    Создает логгеры для записи в файл и вывода в консоль.
    Вызывается один раз при старте приложения.
    
    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Путь к файлу логов
        max_bytes: Максимальный размер файла лога в байтах
        backup_count: Количество резервных копий лог-файлов
        log_format: Формат логов (simple, detailed, json)
    """
    global _logging_initialized
    
    if _logging_initialized:
        return
    
    # Создаем папку для логов, если не существует
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Определяем уровень логирования
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Определяем формат в зависимости от настройки
    if log_format == "simple":
        format_string = "%(levelname)s: %(message)s"
    elif log_format == "json":
        # Упрощенный JSON-подобный формат
        format_string = '{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": "%(message)s"}'
    else:  # detailed (по умолчанию)
        format_string = "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"
    
    # Формат времени
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Создаем форматтер
    formatter = logging.Formatter(format_string, datefmt=date_format)
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Очищаем существующие handlers (если есть)
    root_logger.handlers.clear()
    
    # Handler для записи в файл с ротацией
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Handler для вывода в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Для консоли используем цветной формат (если терминал поддерживает)
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Отключаем логи от сторонних библиотек (слишком много шума)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.INFO)
    
    _logging_initialized = True
    
    # Логируем успешную инициализацию
    logger = get_logger(__name__)
    logger.info("=" * 80)
    logger.info("Система логирования инициализирована")
    logger.info(f"Уровень логирования: {log_level}")
    logger.info(f"Файл логов: {log_file}")
    logger.info(f"Максимальный размер файла: {max_bytes / 1024 / 1024:.1f} MB")
    logger.info(f"Количество резервных копий: {backup_count}")
    logger.info("=" * 80)


def get_logger(name: str) -> logging.Logger:
    """
    Получение логгера для модуля
    
    Используйте так:
    ```python
    from core.logger import get_logger
    
    logger = get_logger(__name__)
    logger.info("Сообщение")
    ```
    
    Args:
        name: Имя модуля (обычно __name__)
        
    Returns:
        Настроенный логгер
    """
    return logging.getLogger(name)


# Вспомогательные функции для удобства


def log_exception(logger: logging.Logger, exception: Exception, context: str = "") -> None:
    """
    Логирование исключения с полной информацией
    
    Args:
        logger: Логгер для записи
        exception: Исключение для логирования
        context: Дополнительный контекст (что делали, когда произошла ошибка)
    """
    if context:
        logger.error(f"{context}: {type(exception).__name__}: {str(exception)}", exc_info=True)
    else:
        logger.error(f"{type(exception).__name__}: {str(exception)}", exc_info=True)


def log_api_request(
    logger: logging.Logger,
    method: str,
    endpoint: str,
    params: Optional[dict] = None
) -> None:
    """
    Логирование API запроса
    
    Args:
        logger: Логгер
        method: HTTP метод (GET, POST, etc.)
        endpoint: URL эндпоинта
        params: Параметры запроса (опционально, не логируем секреты!)
    """
    if params:
        # Скрываем чувствительные данные
        safe_params = {k: "***" if "key" in k.lower() or "token" in k.lower() else v 
                       for k, v in params.items()}
        logger.debug(f"API Request: {method} {endpoint} | Params: {safe_params}")
    else:
        logger.debug(f"API Request: {method} {endpoint}")


def log_api_response(
    logger: logging.Logger,
    status_code: int,
    response_time: float,
    success: bool = True
) -> None:
    """
    Логирование ответа от API
    
    Args:
        logger: Логгер
        status_code: HTTP статус код
        response_time: Время выполнения запроса в секундах
        success: Успешен ли запрос
    """
    level = logging.INFO if success else logging.ERROR
    logger.log(
        level,
        f"API Response: {status_code} | Time: {response_time:.2f}s | Success: {success}"
    )


def log_user_action(
    logger: logging.Logger,
    user_id: int,
    action: str,
    details: Optional[str] = None
) -> None:
    """
    Логирование действия пользователя
    
    Args:
        logger: Логгер
        user_id: ID пользователя Telegram
        action: Описание действия
        details: Дополнительные детали (опционально)
    """
    if details:
        logger.info(f"User {user_id} | {action} | {details}")
    else:
        logger.info(f"User {user_id} | {action}")

