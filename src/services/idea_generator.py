"""
Сервис генерации идей для контента

Генерирует 5 уникальных идей на основе параметров пользователя.
"""

import json
from typing import List, Dict

from core.logger import get_logger, log_exception
from core.exceptions import GenerationError
from api.proxyapi_client import ProxyAPIClient
from prompts.builders import PromptBuilder
from config.settings import Settings

logger = get_logger(__name__)


class IdeaGenerator:
    """
    Генератор идей для контента
    
    Создает 5 разнообразных идей на основе ниши, цели и формата.
    """
    
    def __init__(self, api_client: ProxyAPIClient, settings: Settings):
        """
        Инициализация генератора идей
        
        Args:
            api_client: Клиент для API
            settings: Настройки приложения
        """
        self.api_client = api_client
        self.settings = settings
    
    async def generate_ideas(
        self,
        niche: str,
        goal: str,
        format_type: str
    ) -> List[Dict]:
        """
        Сгенерировать 5 идей для контента
        
        Args:
            niche: Ниша пользователя
            goal: Цель контента
            format_type: Формат контента
            
        Returns:
            Список из 5 идей, каждая в формате:
            {
                "id": int,
                "title": str,
                "description": str,
                "key_elements": List[str]
            }
            
        Raises:
            GenerationError: При ошибках генерации
        """
        try:
            logger.info(f"Генерация идей | Ниша: {niche} | Цель: {goal} | Формат: {format_type}")
            
            # Построение промпта
            prompt = PromptBuilder.build_ideas_prompt(
                niche=niche,
                goal=goal,
                format_type=format_type
            )
            
            messages = PromptBuilder.build_messages("creator", prompt)
            
            # Запрос к API
            response = await self.api_client.chat_completion(
                messages=messages,
                model=self.settings.model_text_generation,
                temperature=self.settings.temperature_ideas,
                max_tokens=self.settings.max_tokens_ideas,
                json_mode=True
            )
            
            # Парсинг JSON
            try:
                result = json.loads(response)
            except json.JSONDecodeError as e:
                logger.error(f"Не удалось распарсить JSON ответ: {response[:200]}...")
                raise GenerationError(
                    "Ошибка парсинга ответа при генерации идей",
                    original_error=e
                )
            
            # Валидация структуры
            if "ideas" not in result:
                raise GenerationError("Отсутствует поле 'ideas' в ответе")
            
            ideas = result["ideas"]
            
            if not isinstance(ideas, list):
                raise GenerationError("Поле 'ideas' должно быть списком")
            
            if len(ideas) != 5:
                logger.warning(f"Получено {len(ideas)} идей вместо 5")
                if len(ideas) < 5:
                    raise GenerationError(f"Недостаточно идей: получено {len(ideas)}, ожидалось 5")
            
            # Валидация каждой идеи
            required_fields = ["id", "title", "description", "key_elements"]
            for i, idea in enumerate(ideas[:5], 1):  # Берем только первые 5
                for field in required_fields:
                    if field not in idea:
                        raise GenerationError(f"Отсутствует поле '{field}' в идее {i}")
                
                # Проверка типов
                if not isinstance(idea["id"], int):
                    idea["id"] = i  # Исправляем ID если неверный
                
                if not isinstance(idea["key_elements"], list):
                    raise GenerationError(f"Поле 'key_elements' в идее {i} должно быть списком")
            
            ideas = ideas[:5]  # Обрезаем до 5 идей
            
            logger.info(f"✓ Успешно сгенерировано {len(ideas)} идей")
            
            return ideas
            
        except GenerationError:
            raise
        except Exception as e:
            log_exception(logger, e, "Неожиданная ошибка при генерации идей")
            raise GenerationError(
                f"Не удалось сгенерировать идеи: {str(e)}",
                original_error=e
            )
    
    def validate_idea(self, idea: Dict) -> bool:
        """
        Валидация структуры идеи
        
        Args:
            idea: Идея для валидации
            
        Returns:
            True если идея валидна
        """
        required_fields = ["id", "title", "description", "key_elements"]
        
        for field in required_fields:
            if field not in idea:
                return False
        
        if not isinstance(idea["key_elements"], list):
            return False
        
        return True

