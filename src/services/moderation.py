"""
Сервис модерации поведения пользователя

Отслеживает отклонения от темы и помогает вернуть пользователя к цели диалога.
"""

import json
from typing import Dict, Optional

from core.logger import get_logger, log_exception
from core.exceptions import ModerationError
from api.proxyapi_client import ProxyAPIClient
from prompts.builders import PromptBuilder
from config.settings import Settings

logger = get_logger(__name__)


class ModerationService:
    """
    Сервис для модерации сообщений пользователя
    
    Проверяет релевантность ответов и предлагает способы возврата к теме.
    """
    
    def __init__(self, api_client: ProxyAPIClient, settings: Settings):
        """
        Инициализация сервиса модерации
        
        Args:
            api_client: Клиент для API
            settings: Настройки приложения
        """
        self.api_client = api_client
        self.settings = settings
    
    async def check_relevance(
        self,
        current_step: str,
        bot_question: str,
        user_response: str
    ) -> Dict[str, any]:
        """
        Проверить релевантность ответа пользователя
        
        Args:
            current_step: Текущий этап диалога
            bot_question: Вопрос бота
            user_response: Ответ пользователя
            
        Returns:
            Словарь с полями:
            - is_relevant: bool - релевантен ли ответ
            - reason: str - причина решения
            - suggestion: str - как вернуть к теме (если нерелевантно)
            
        Raises:
            ModerationError: При ошибках модерации
        """
        try:
            logger.info(f"Проверка релевантности | Этап: {current_step} | Длина ответа: {len(user_response)}")
            
            # Построение промпта
            prompt = PromptBuilder.build_moderation_prompt(
                current_step=current_step,
                bot_question=bot_question,
                user_response=user_response
            )
            
            messages = PromptBuilder.build_messages("moderator", prompt)
            
            # Запрос к API
            response = await self.api_client.chat_completion(
                messages=messages,
                model=self.settings.model_text_generation,
                temperature=self.settings.temperature_moderation,
                max_tokens=200,
                json_mode=True
            )
            
            # Парсинг JSON
            try:
                result = json.loads(response)
            except json.JSONDecodeError as e:
                logger.error(f"Не удалось распарсить JSON ответ модерации: {response}")
                raise ModerationError(
                    "Ошибка парсинга ответа модерации",
                    original_error=e
                )
            
            # Валидация структуры
            required_fields = ["is_relevant", "reason", "suggestion"]
            for field in required_fields:
                if field not in result:
                    raise ModerationError(f"Отсутствует поле '{field}' в ответе модерации")
            
            is_relevant = result["is_relevant"]
            logger.info(f"Результат модерации: {'Релевантно' if is_relevant else 'Нерелевантно'} | {result['reason']}")
            
            return result
            
        except ModerationError:
            raise
        except Exception as e:
            log_exception(logger, e, "Ошибка при проверке релевантности")
            raise ModerationError(
                f"Не удалось проверить релевантность: {str(e)}",
                original_error=e
            )
    
    def get_redirection_message(
        self,
        attempt_number: int,
        bot_question: str,
        suggestion: Optional[str] = None
    ) -> str:
        """
        Получить сообщение для возврата к теме
        
        Сообщение становится строже с каждой попыткой.
        
        Args:
            attempt_number: Номер попытки отклонения (1, 2, 3, ...)
            bot_question: Вопрос бота, к которому нужно вернуться
            suggestion: Предложение от AI (опционально)
            
        Returns:
            Текст сообщения для пользователя
        """
        if attempt_number == 1:
            # Первая попытка - мягко
            if suggestion:
                return suggestion
            return f"Давай сосредоточимся на создании твоего контента 😊\n\n{bot_question}"
        
        elif attempt_number == 2:
            # Вторая попытка - настойчивее
            return (
                f"Я понимаю, что тебе интересно, но я создан специально для генерации идей контента 🎯\n\n"
                f"Пожалуйста, давай вернемся к нашей задаче.\n\n{bot_question}"
            )
        
        elif attempt_number == 3:
            # Третья попытка - предупреждение
            return (
                f"Я вижу, что тебя что-то отвлекает 😔\n\n"
                f"Мне важно помочь тебе создать качественный контент, "
                f"но для этого мне нужна информация.\n\n"
                f"Если сейчас не подходящее время, мы можем продолжить позже.\n\n"
                f"Готов ответить на мой вопрос?\n\n{bot_question}"
            )
        
        else:
            # Четвертая и далее - прощание
            return (
                "Понимаю, что сейчас ты не готов работать над контентом 😌\n\n"
                "Возвращайся, когда будешь готов! Отправь /start для начала новой сессии.\n\n"
                "Всего хорошего! 👋"
            )
    
    def should_end_conversation(self, attempt_number: int) -> bool:
        """
        Определить, нужно ли завершить диалог
        
        Args:
            attempt_number: Номер попытки отклонения
            
        Returns:
            True если нужно завершить, False иначе
        """
        return attempt_number > self.settings.max_off_topic_attempts
    
    def detect_offensive_content(self, text: str) -> bool:
        """
        Простая проверка на ненормативную лексику
        
        Это базовая проверка. Для production лучше использовать специализированные библиотеки.
        
        Args:
            text: Текст для проверки
            
        Returns:
            True если обнаружен мат, False иначе
        """
        # Список базовых паттернов ненормативной лексики
        # В production стоит использовать более продвинутые методы
        offensive_patterns = [
            "блять", "бля", "хуй", "пизд", "ебать", "еба", "сука", 
            "пидор", "мудак", "долбоеб", "уебок"
        ]
        
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in offensive_patterns)

