"""
Сервис генерации постов

Создает готовые посты с изображениями на основе выбранной идеи.
"""

import json
from typing import Dict, Tuple, Optional
from pathlib import Path
import time

from core.logger import get_logger, log_exception
from core.exceptions import GenerationError, ImageGenerationError
from api.proxyapi_client import ProxyAPIClient
from prompts.builders import PromptBuilder
from config.settings import Settings

logger = get_logger(__name__)


class PostGenerator:
    """
    Генератор постов и изображений
    
    Многоэтапная генерация:
    1. Генерация текста поста
    2. Генерация промпта для изображения
    3. Генерация изображения
    """
    
    def __init__(self, api_client: ProxyAPIClient, settings: Settings):
        """
        Инициализация генератора постов
        
        Args:
            api_client: Клиент для API
            settings: Настройки приложения
        """
        self.api_client = api_client
        self.settings = settings
    
    async def generate_post_text(
        self,
        niche: str,
        goal: str,
        format_type: str,
        idea: Dict
    ) -> Dict:
        """
        Сгенерировать текст поста
        
        Args:
            niche: Ниша
            goal: Цель
            format_type: Формат
            idea: Выбранная идея
            
        Returns:
            Данные поста в формате:
            {
                "title": str,
                "content": str,
                "hashtags": List[str],
                "call_to_action": str
            }
            
        Raises:
            GenerationError: При ошибках генерации
        """
        try:
            logger.info(f"Генерация текста поста | Идея: {idea.get('title', 'N/A')}")
            
            # Построение промпта
            prompt = PromptBuilder.build_post_prompt(
                niche=niche,
                goal=goal,
                format_type=format_type,
                idea_title=idea["title"],
                idea_description=idea["description"],
                key_elements=idea["key_elements"]
            )
            
            messages = PromptBuilder.build_messages("creator", prompt)
            
            # Запрос к API (используем более мощную модель для финального поста)
            # С fallback на GPT-4o если основная модель не работает
            try:
                response = await self.api_client.chat_completion(
                    messages=messages,
                    model=self.settings.model_final_post,
                    temperature=self.settings.temperature_post,
                    max_tokens=self.settings.max_tokens_post,
                    json_mode=True
                )
            except GenerationError as e:
                # Если модель вернула пустой контент, отказала или исчерпала токены, пробуем fallback
                error_str = str(e).lower()
                if ("пустой контент" in error_str or 
                    "отказала" in error_str or 
                    "finish_reason: length" in error_str):
                    logger.warning(
                        f"Основная модель не справилась ({self.settings.model_final_post}), "
                        f"переключаемся на fallback (gpt-4o) | Причина: {e}"
                    )
                    response = await self.api_client.chat_completion(
                        messages=messages,
                        model="gpt-4o",  # Fallback модель
                        temperature=self.settings.temperature_post,
                        max_tokens=self.settings.max_tokens_post,
                        json_mode=True
                    )
                else:
                    raise
            
            # Парсинг JSON
            try:
                result = json.loads(response)
            except json.JSONDecodeError as e:
                logger.error(f"Не удалось распарсить JSON ответ поста")
                raise GenerationError(
                    "Ошибка парсинга ответа при генерации поста",
                    original_error=e
                )
            
            # Валидация структуры
            if "post" not in result:
                raise GenerationError("Отсутствует поле 'post' в ответе")
            
            post_data = result["post"]
            
            # Обязательные поля
            required_fields = ["title", "content"]
            for field in required_fields:
                if field not in post_data:
                    raise GenerationError(f"Отсутствует поле '{field}' в данных поста")
            
            # Необязательные поля с значениями по умолчанию
            if "hashtags" not in post_data or not post_data["hashtags"]:
                post_data["hashtags"] = []
            if "call_to_action" not in post_data:
                post_data["call_to_action"] = ""
            
            logger.info(f"✓ Текст поста сгенерирован | Длина: {len(post_data['content'])} символов")
            
            return post_data
            
        except GenerationError:
            raise
        except Exception as e:
            log_exception(logger, e, "Ошибка при генерации текста поста")
            raise GenerationError(
                f"Не удалось сгенерировать текст поста: {str(e)}",
                original_error=e
            )
    
    async def generate_image_prompt(
        self,
        niche: str,
        format_type: str,
        post_data: Dict
    ) -> str:
        """
        Сгенерировать промпт для изображения
        
        Args:
            niche: Ниша
            format_type: Формат
            post_data: Данные поста
            
        Returns:
            Промпт для DALL-E на английском
            
        Raises:
            GenerationError: При ошибках генерации
        """
        try:
            logger.info("Генерация промпта для изображения")
            
            # Построение промпта
            prompt = PromptBuilder.build_image_prompt_prompt(
                niche=niche,
                format_type=format_type,
                post_title=post_data["title"],
                post_content=post_data["content"]
            )
            
            messages = PromptBuilder.build_messages("creator", prompt)
            
            # Запрос к API
            response = await self.api_client.chat_completion(
                messages=messages,
                model=self.settings.model_text_generation,
                temperature=self.settings.temperature_image_prompt,
                max_tokens=500,
                json_mode=True
            )
            
            # Парсинг JSON
            try:
                result = json.loads(response)
            except json.JSONDecodeError as e:
                logger.error("Не удалось распарсить JSON ответ image prompt")
                raise GenerationError(
                    "Ошибка парсинга ответа при генерации image prompt",
                    original_error=e
                )
            
            # Извлечение промпта
            if "image_prompt" not in result:
                raise GenerationError("Отсутствует поле 'image_prompt' в ответе")
            
            image_prompt_data = result["image_prompt"]
            
            if "full_prompt" not in image_prompt_data:
                raise GenerationError("Отсутствует поле 'full_prompt' в image_prompt")
            
            full_prompt = image_prompt_data["full_prompt"]
            
            logger.info(f"✓ Промпт для изображения сгенерирован | Длина: {len(full_prompt)} символов")
            logger.debug(f"Image prompt: {full_prompt}")
            
            return full_prompt
            
        except GenerationError:
            raise
        except Exception as e:
            log_exception(logger, e, "Ошибка при генерации промпта для изображения")
            raise GenerationError(
                f"Не удалось сгенерировать промпт для изображения: {str(e)}",
                original_error=e
            )
    
    async def generate_image(self, image_prompt: str) -> Tuple[str, Optional[bytes]]:
        """
        Сгенерировать изображение
        
        Args:
            image_prompt: Промпт для DALL-E
            
        Returns:
            Кортеж (URL изображения, байты изображения или None)
            
        Raises:
            ImageGenerationError: При ошибках генерации
        """
        try:
            logger.info("Генерация изображения через DALL-E")
            
            # Генерация изображения
            image_url = await self.api_client.generate_image(
                prompt=image_prompt,
                model=self.settings.model_image_generation,
                size="1024x1024",
                quality="standard"
            )
            
            logger.info(f"✓ Изображение сгенерировано | URL: {image_url[:50]}...")
            
            # Скачивание изображения
            image_bytes = await self.api_client.download_image(image_url)
            
            # Сохранение локально если нужно
            if self.settings.save_images_locally:
                timestamp = int(time.time())
                save_path = Path(self.settings.images_folder) / f"post_{timestamp}.png"
                await self.api_client.download_image(image_url, save_path)
                logger.info(f"Изображение сохранено локально: {save_path}")
            
            return image_url, image_bytes
            
        except ImageGenerationError:
            raise
        except Exception as e:
            log_exception(logger, e, "Ошибка при генерации изображения")
            raise ImageGenerationError(
                f"Не удалось сгенерировать изображение: {str(e)}",
                original_error=e
            )
    
    async def generate_complete_post(
        self,
        niche: str,
        goal: str,
        format_type: str,
        idea: Dict
    ) -> Tuple[Dict, str, bytes]:
        """
        Сгенерировать полный пост с изображением
        
        Оркестрирует все этапы генерации:
        1. Текст поста
        2. Промпт для изображения
        3. Изображение
        
        Args:
            niche: Ниша
            goal: Цель
            format_type: Формат
            idea: Выбранная идея
            
        Returns:
            Кортеж (данные поста, URL изображения, байты изображения)
            
        Raises:
            GenerationError, ImageGenerationError: При ошибках генерации
        """
        logger.info("=" * 80)
        logger.info("НАЧАЛО ГЕНЕРАЦИИ ПОЛНОГО ПОСТА")
        logger.info("=" * 80)
        
        try:
            # Этап 1: Генерация текста поста
            logger.info("Этап 1/3: Генерация текста поста")
            post_data = await self.generate_post_text(
                niche=niche,
                goal=goal,
                format_type=format_type,
                idea=idea
            )
            
            # Этап 2: Генерация промпта для изображения
            logger.info("Этап 2/3: Генерация промпта для изображения")
            image_prompt = await self.generate_image_prompt(
                niche=niche,
                format_type=format_type,
                post_data=post_data
            )
            
            # Этап 3: Генерация изображения
            logger.info("Этап 3/3: Генерация изображения")
            image_url, image_bytes = await self.generate_image(image_prompt)
            
            logger.info("=" * 80)
            logger.info("✓ ПОЛНЫЙ ПОСТ УСПЕШНО СГЕНЕРИРОВАН")
            logger.info("=" * 80)
            
            return post_data, image_url, image_bytes
            
        except (GenerationError, ImageGenerationError):
            raise
        except Exception as e:
            log_exception(logger, e, "Неожиданная ошибка при генерации полного поста")
            raise GenerationError(
                f"Не удалось сгенерировать полный пост: {str(e)}",
                original_error=e
            )

