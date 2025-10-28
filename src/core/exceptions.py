"""
Кастомные исключения для системы

Все исключения наследуются от базового BotException для удобства обработки.
"""


class BotException(Exception):
    """
    Базовое исключение для всех ошибок бота
    
    От него наследуются все остальные исключения для единообразной обработки.
    """
    
    def __init__(self, message: str, original_error: Exception = None):
        """
        Args:
            message: Описание ошибки
            original_error: Оригинальная ошибка, если это обертка
        """
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class ConfigurationError(BotException):
    """
    Ошибка конфигурации приложения
    
    Возникает когда:
    - Отсутствуют обязательные переменные окружения
    - Неверный формат конфигурации
    - Невалидные значения параметров
    """
    pass


class APIError(BotException):
    """
    Базовая ошибка при работе с API
    
    Используется для общих проблем с внешними API (ProxyAPI/OpenAI).
    """
    
    def __init__(self, message: str, status_code: int = None, original_error: Exception = None):
        """
        Args:
            message: Описание ошибки
            status_code: HTTP статус код ошибки (если есть)
            original_error: Оригинальная ошибка
        """
        super().__init__(message, original_error)
        self.status_code = status_code


class APIConnectionError(APIError):
    """
    Ошибка соединения с API
    
    Возникает когда:
    - Нет интернет-соединения
    - API недоступен
    - Timeout при запросе
    """
    pass


class APIRateLimitError(APIError):
    """
    Превышен лимит запросов к API
    
    Возникает при получении HTTP 429 Too Many Requests.
    Требует повторной попытки через некоторое время.
    """
    
    def __init__(self, message: str, retry_after: int = None, original_error: Exception = None):
        """
        Args:
            message: Описание ошибки
            retry_after: Через сколько секунд можно повторить запрос
            original_error: Оригинальная ошибка
        """
        super().__init__(message, status_code=429, original_error=original_error)
        self.retry_after = retry_after


class APIAuthenticationError(APIError):
    """
    Ошибка аутентификации в API
    
    Возникает при:
    - Неверном API ключе
    - Истекшем токене
    - Недостаточных правах доступа
    """
    
    def __init__(self, message: str = "Неверный API ключ или недостаточно прав", original_error: Exception = None):
        super().__init__(message, status_code=401, original_error=original_error)


class GenerationError(BotException):
    """
    Ошибка генерации контента
    
    Возникает когда:
    - AI вернул невалидный JSON
    - Не хватает идей (меньше 5)
    - Результат не соответствует ожиданиям
    """
    pass


class ModerationError(BotException):
    """
    Ошибка модерации контента
    
    Возникает при проблемах с проверкой сообщений пользователя.
    """
    pass


class ImageGenerationError(GenerationError):
    """
    Ошибка генерации изображения
    
    Возникает когда:
    - Не удалось создать изображение
    - Промпт был отклонен (policy violation)
    - Ошибка скачивания изображения
    """
    pass


class TranscriptionError(BotException):
    """
    Ошибка транскрибации аудио
    
    Возникает при проблемах с распознаванием голосовых сообщений.
    """
    pass

