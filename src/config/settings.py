"""
Настройки приложения

Загружает конфигурацию из переменных окружения (.env файл).
Валидирует обязательные параметры и предоставляет значения по умолчанию для опциональных.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.exceptions import ConfigurationError


class Settings(BaseSettings):
    """
    Настройки приложения
    
    Все параметры загружаются из .env файла.
    Обязательные параметры проверяются при инициализации.
    """
    
    # ===========================================
    # TELEGRAM
    # ===========================================
    
    telegram_bot_token: str = Field(
        ...,  # обязательный параметр
        description="Токен Telegram бота от @BotFather"
    )
    
    # ===========================================
    # PROXYAPI (OpenAI)
    # ===========================================
    
    proxyapi_key: str = Field(
        ...,  # обязательный параметр
        description="API ключ от ProxyAPI.ru"
    )
    
    proxyapi_base_url: str = Field(
        default="https://api.proxyapi.ru/openai/v1",
        description="Базовый URL для ProxyAPI"
    )
    
    # ===========================================
    # МОДЕЛИ AI
    # ===========================================
    
    model_text_generation: str = Field(
        default="gpt-4o-mini",
        description="Модель для генерации текста (идеи, модерация)"
    )
    
    model_final_post: str = Field(
        default="gpt-5",
        description="Модель для генерации финального поста (более качественный и живой текст)"
    )
    
    model_image_generation: str = Field(
        default="dall-e-3",
        description="Модель для генерации изображений"
    )
    
    model_speech_to_text: str = Field(
        default="whisper-1",
        description="Модель для транскрибации речи"
    )
    
    # ===========================================
    # ПАРАМЕТРЫ ГЕНЕРАЦИИ
    # ===========================================
    
    max_tokens_ideas: int = Field(
        default=1500,
        ge=500,
        le=4000,
        description="Максимальное количество токенов для генерации идей"
    )
    
    max_tokens_post: int = Field(
        default=2500,
        ge=1000,
        le=4000,
        description="Максимальное количество токенов для генерации поста"
    )
    
    temperature_ideas: float = Field(
        default=0.8,
        ge=0.0,
        le=2.0,
        description="Температура (креативность) для генерации идей"
    )
    
    temperature_post: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Температура для генерации постов"
    )
    
    temperature_image_prompt: float = Field(
        default=0.9,
        ge=0.0,
        le=2.0,
        description="Температура для генерации промптов изображений"
    )
    
    temperature_moderation: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Температура для модерации (должна быть низкой)"
    )
    
    # ===========================================
    # ЛОГИРОВАНИЕ
    # ===========================================
    
    log_level: str = Field(
        default="INFO",
        description="Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    log_max_bytes: int = Field(
        default=10485760,  # 10MB
        ge=1048576,  # минимум 1MB
        description="Максимальный размер файла лога в байтах"
    )
    
    log_backup_count: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Количество резервных копий логов"
    )
    
    log_format: str = Field(
        default="detailed",
        description="Формат логов (simple, detailed, json)"
    )
    
    log_file: str = Field(
        default="logs/bot.log",
        description="Путь к файлу логов"
    )
    
    # ===========================================
    # ПОВЕДЕНИЕ БОТА
    # ===========================================
    
    max_off_topic_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Максимальное количество попыток отклонения от темы"
    )
    
    typing_timeout: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Время отображения typing indicator в секундах"
    )
    
    min_response_delay: float = Field(
        default=0.5,
        ge=0.0,
        le=5.0,
        description="Минимальная задержка перед ответом в секундах"
    )
    
    max_response_delay: float = Field(
        default=3.0,
        ge=0.0,
        le=10.0,
        description="Максимальная задержка перед ответом в секундах"
    )
    
    delay_per_char: float = Field(
        default=0.01,
        ge=0.0,
        le=0.1,
        description="Коэффициент задержки на символ в секундах"
    )
    
    # ===========================================
    # РАСШИРЕННЫЕ НАСТРОЙКИ
    # ===========================================
    
    debug_mode: bool = Field(
        default=False,
        description="Режим отладки (больше логов)"
    )
    
    save_images_locally: bool = Field(
        default=False,
        description="Сохранять ли изображения локально"
    )
    
    images_folder: str = Field(
        default="generated_images",
        description="Папка для сохранения изображений"
    )
    
    # Настройки для Pydantic
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # игнорировать лишние поля
        protected_namespaces=()  # отключаем защиту namespace для полей model_*
    )
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Валидация уровня логирования"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level должен быть одним из: {', '.join(valid_levels)}")
        return v_upper
    
    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Валидация формата логов"""
        valid_formats = ["simple", "detailed", "json"]
        v_lower = v.lower()
        if v_lower not in valid_formats:
            raise ValueError(f"log_format должен быть одним из: {', '.join(valid_formats)}")
        return v_lower
    
    @field_validator("max_response_delay")
    @classmethod
    def validate_delays(cls, v: float, info) -> float:
        """Проверка, что max_response_delay >= min_response_delay"""
        if "min_response_delay" in info.data:
            min_delay = info.data["min_response_delay"]
            if v < min_delay:
                raise ValueError("max_response_delay должен быть >= min_response_delay")
        return v
    
    def validate_required_settings(self) -> None:
        """
        Дополнительная валидация настроек
        
        Проверяет критичные параметры и выбрасывает ConfigurationError при проблемах.
        """
        # Проверка Telegram токена
        if not self.telegram_bot_token or self.telegram_bot_token == "your_telegram_bot_token_here":
            raise ConfigurationError(
                "TELEGRAM_BOT_TOKEN не установлен! "
                "Получите токен от @BotFather и добавьте в .env файл"
            )
        
        # Проверка ProxyAPI ключа
        if not self.proxyapi_key or self.proxyapi_key == "your_proxyapi_key_here":
            raise ConfigurationError(
                "PROXYAPI_KEY не установлен! "
                "Получите ключ на https://proxyapi.ru и добавьте в .env файл"
            )
        
        # Создание папок при необходимости
        if self.save_images_locally:
            Path(self.images_folder).mkdir(parents=True, exist_ok=True)
        
        # Создание папки для логов
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)
    
    def get_summary(self) -> str:
        """
        Получить сводку текущих настроек
        
        Returns:
            Строка с основными настройками (без секретов)
        """
        return f"""
╔══════════════════════════════════════════════════════════════╗
║                  КОНФИГУРАЦИЯ ПРИЛОЖЕНИЯ                     ║
╠══════════════════════════════════════════════════════════════╣
║ Telegram Bot Token: {'✓ Установлен' if self.telegram_bot_token else '✗ Не установлен'}
║ ProxyAPI Key: {'✓ Установлен' if self.proxyapi_key else '✗ Не установлен'}
║ ProxyAPI URL: {self.proxyapi_base_url}
╠══════════════════════════════════════════════════════════════╣
║ Модель текста: {self.model_text_generation}
║ Модель изображений: {self.model_image_generation}
║ Модель транскрибации: {self.model_speech_to_text}
╠══════════════════════════════════════════════════════════════╣
║ Max токенов (идеи): {self.max_tokens_ideas}
║ Max токенов (посты): {self.max_tokens_post}
║ Temperature (идеи): {self.temperature_ideas}
║ Temperature (посты): {self.temperature_post}
╠══════════════════════════════════════════════════════════════╣
║ Уровень логов: {self.log_level}
║ Файл логов: {self.log_file}
║ Размер лога: {self.log_max_bytes / 1024 / 1024:.1f} MB
║ Резервных копий: {self.log_backup_count}
╠══════════════════════════════════════════════════════════════╣
║ Max попыток оффтопа: {self.max_off_topic_attempts}
║ Задержка (мин-макс): {self.min_response_delay}s - {self.max_response_delay}s
║ Typing timeout: {self.typing_timeout}s
╠══════════════════════════════════════════════════════════════╣
║ Debug mode: {'✓ Включен' if self.debug_mode else '✗ Выключен'}
║ Сохранение изображений: {'✓ Включено' if self.save_images_locally else '✗ Выключено'}
╚══════════════════════════════════════════════════════════════╝
        """.strip()


# Глобальный экземпляр настроек (Singleton pattern)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Получить глобальный экземпляр настроек
    
    При первом вызове загружает настройки из .env
    Последующие вызовы возвращают тот же экземпляр (Singleton)
    
    Returns:
        Настройки приложения
        
    Raises:
        ConfigurationError: Если настройки невалидны
    """
    global _settings
    
    if _settings is None:
        try:
            _settings = Settings()
            _settings.validate_required_settings()
        except Exception as e:
            raise ConfigurationError(
                f"Ошибка загрузки конфигурации: {str(e)}",
                original_error=e
            )
    
    return _settings


def reload_settings() -> Settings:
    """
    Перезагрузить настройки из .env
    
    Полезно для тестирования или при изменении конфигурации на лету.
    
    Returns:
        Обновленные настройки
    """
    global _settings
    _settings = None
    return get_settings()

