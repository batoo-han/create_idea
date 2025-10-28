"""
Клиент для работы с ProxyAPI (OpenAI-совместимый API)

Поддерживает:
- Генерацию текста (chat completions)
- Генерацию изображений (DALL-E)
- Транскрибацию аудио (Whisper)

Особенности:
- Асинхронные запросы
- Автоматическая обработка ошибок
- Retry логика для временных сбоев
- Детальное логирование
- Автоматическая адаптация параметров под модель:
  
  Лимит токенов:
  * GPT-4, GPT-4o, GPT-3.5: max_tokens
  * GPT-5, O1, O3: max_completion_tokens
  
  Temperature:
  * GPT-4, GPT-4o, GPT-3.5: настраиваемый (0.0-2.0)
  * GPT-5, O1, O3: фиксированный 1.0 (параметр не передаётся)
"""

import asyncio
import json
from typing import Optional, Dict, List, Any
from pathlib import Path
import httpx
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from openai.types import ImagesResponse

from core.logger import get_logger, log_api_request, log_api_response, log_exception
from core.exceptions import (
    APIError,
    APIConnectionError,
    APIRateLimitError,
    APIAuthenticationError,
    GenerationError,
    ImageGenerationError,
    TranscriptionError,
)

logger = get_logger(__name__)


class ProxyAPIClient:
    """
    Клиент для работы с ProxyAPI.ru (OpenAI-совместимый API)
    
    Использует официальную библиотеку OpenAI для совместимости.
    
    Таблица совместимости параметров:
    ┌─────────────────┬──────────────┬─────────────────┬──────────────┐
    │ Модель          │ max_tokens   │ temperature     │ Примечания   │
    ├─────────────────┼──────────────┼─────────────────┼──────────────┤
    │ GPT-3.5-turbo   │ ✅ max_tokens│ ✅ настраиваемый│              │
    │ GPT-4           │ ✅ max_tokens│ ✅ настраиваемый│              │
    │ GPT-4o          │ ✅ max_tokens│ ✅ настраиваемый│              │
    │ GPT-4o-mini     │ ✅ max_tokens│ ✅ настраиваемый│              │
    │ GPT-5           │ ❌ → max_comp│ ❌ только 1.0   │ Новый API    │
    │ O1-preview      │ ❌ → max_comp│ ❌ только 1.0   │ Reasoning    │
    │ O1-mini         │ ❌ → max_comp│ ❌ только 1.0   │ Reasoning    │
    │ O3-mini         │ ❌ → max_comp│ ❌ только 1.0   │ Reasoning    │
    └─────────────────┴──────────────┴─────────────────┴──────────────┘
    
    max_comp = max_completion_tokens
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.proxyapi.ru/openai/v1",
        timeout: int = 60,
        max_retries: int = 3
    ):
        """
        Инициализация клиента
        
        Args:
            api_key: API ключ от ProxyAPI.ru
            base_url: Базовый URL API
            timeout: Таймаут запросов в секундах
            max_retries: Максимальное количество повторных попыток
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Инициализация OpenAI клиента с настройками для ProxyAPI
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries
        )
        
        logger.info(f"ProxyAPI клиент инициализирован | Base URL: {base_url}")
    
    @staticmethod
    def _uses_max_completion_tokens(model: str) -> bool:
        """
        Определить, использует ли модель max_completion_tokens вместо max_tokens
        
        Новые модели (GPT-5, O1, O3 серии) требуют max_completion_tokens.
        Старые модели (GPT-4, GPT-3.5) используют max_tokens.
        
        Args:
            model: Название модели
            
        Returns:
            True если модель использует max_completion_tokens
        """
        model_lower = model.lower()
        
        # Модели, которые используют max_completion_tokens
        new_models = [
            'gpt-5',
            'o1-preview',
            'o1-mini',
            'o3-mini',
            'o3',
        ]
        
        # Проверяем начинается ли модель с одного из новых префиксов
        for new_model in new_models:
            if model_lower.startswith(new_model):
                return True
        
        return False
    
    @staticmethod
    def _supports_custom_temperature(model: str) -> bool:
        """
        Определить, поддерживает ли модель кастомный temperature
        
        Некоторые модели имеют ограничения на temperature:
        - GPT-5: только temperature=1 (дефолт)
        - O1 модели: только temperature=1 (дефолт)
        - O3 модели: только temperature=1 (дефолт)
        
        Args:
            model: Название модели
            
        Returns:
            False если модель не поддерживает кастомный temperature
        """
        model_lower = model.lower()
        
        # Модели с фиксированной temperature
        fixed_temp_models = [
            'gpt-5',
            'o1-preview',
            'o1-mini',
            'o3-mini',
            'o3',
        ]
        
        # Проверяем начинается ли модель с одного из префиксов
        for fixed_model in fixed_temp_models:
            if model_lower.startswith(fixed_model):
                return False
        
        return True
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
        **kwargs
    ) -> str:
        """
        Генерация текста через chat completion
        
        Args:
            messages: Список сообщений в формате [{"role": "user", "content": "..."}]
            model: Модель для использования
            temperature: Креативность (0.0-2.0)
            max_tokens: Максимальное количество токенов в ответе
                       (автоматически преобразуется в max_completion_tokens для GPT-5 и O-моделей)
            json_mode: Требовать JSON ответ
            **kwargs: Дополнительные параметры для API
            
        Returns:
            Сгенерированный текст
            
        Raises:
            APIError: При ошибках API
            GenerationError: При проблемах с генерацией
            
        Note:
            Метод автоматически определяет тип модели и адаптирует параметры:
            
            **Лимит токенов:**
            - max_tokens для GPT-4, GPT-4o, GPT-3.5
            - max_completion_tokens для GPT-5, O1, O3
            
            **Temperature:**
            - Настраиваемый для GPT-4, GPT-4o, GPT-3.5
            - Фиксированный (1.0) для GPT-5, O1, O3 - параметр не передаётся
        """
        try:
            log_api_request(logger, "POST", f"{self.base_url}/chat/completions", {
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens
            })
            
            # Подготовка параметров
            params = {
                "model": model,
                "messages": messages,
                **kwargs
            }
            
            # Некоторые модели не поддерживают кастомный temperature (GPT-5, O1, O3)
            if self._supports_custom_temperature(model):
                params["temperature"] = temperature
            else:
                logger.debug(f"Temperature пропущена для модели {model} (поддерживает только дефолт)")
            
            # Выбор правильного параметра для ограничения токенов в зависимости от модели
            if max_tokens:
                if self._uses_max_completion_tokens(model):
                    params["max_completion_tokens"] = max_tokens
                    logger.debug(f"Используется max_completion_tokens для модели {model}")
                else:
                    params["max_tokens"] = max_tokens
                    logger.debug(f"Используется max_tokens для модели {model}")
            
            if json_mode:
                params["response_format"] = {"type": "json_object"}
            
            # Запрос к API
            import time
            start_time = time.time()
            
            response: ChatCompletion = await self.client.chat.completions.create(**params)
            
            elapsed_time = time.time() - start_time
            log_api_response(logger, 200, elapsed_time, success=True)
            
            # Извлечение текста из ответа
            if not response.choices:
                logger.error(f"API вернул ответ без choices | Model: {model}")
                raise GenerationError("API вернул пустой ответ без choices")
            
            choice = response.choices[0]
            message = choice.message
            
            # Логируем детали ответа для отладки
            logger.debug(f"Response details | finish_reason: {choice.finish_reason} | role: {message.role}")
            
            # Проверяем refusal (отказ модели)
            if hasattr(message, 'refusal') and message.refusal:
                logger.warning(f"Модель отказала в генерации | Reason: {message.refusal}")
                raise GenerationError(f"Модель отказала в генерации контента: {message.refusal}")
            
            content = message.content
            
            if not content:
                # Детальное логирование для отладки
                logger.error(f"Пустой контент | Model: {model} | finish_reason: {choice.finish_reason}")
                logger.error(f"Full response: {response.model_dump_json()}")
                raise GenerationError(f"API вернул пустой контент (finish_reason: {choice.finish_reason})")
            
            logger.debug(f"Получен ответ длиной {len(content)} символов")
            
            return content
            
        except httpx.TimeoutException as e:
            log_exception(logger, e, "Timeout при запросе к API")
            raise APIConnectionError(
                "Превышено время ожидания ответа от API",
                original_error=e
            )
        
        except httpx.ConnectError as e:
            log_exception(logger, e, "Ошибка соединения с API")
            raise APIConnectionError(
                "Не удалось подключиться к API. Проверьте интернет-соединение",
                original_error=e
            )
        
        except Exception as e:
            # Обработка специфичных ошибок OpenAI
            error_message = str(e).lower()
            
            if "429" in error_message or "rate limit" in error_message:
                log_exception(logger, e, "Rate limit превышен")
                raise APIRateLimitError(
                    "Превышен лимит запросов к API. Попробуйте позже",
                    retry_after=60,
                    original_error=e
                )
            
            elif "401" in error_message or "unauthorized" in error_message or "api key" in error_message:
                log_exception(logger, e, "Ошибка аутентификации")
                raise APIAuthenticationError(
                    "Неверный API ключ или недостаточно прав",
                    original_error=e
                )
            
            else:
                log_exception(logger, e, "Неожиданная ошибка при генерации текста")
                raise APIError(
                    f"Ошибка API: {str(e)}",
                    original_error=e
                )
    
    async def generate_image(
        self,
        prompt: str,
        model: str = "dall-e-3",
        size: str = "1024x1024",
        quality: str = "standard",
        n: int = 1
    ) -> str:
        """
        Генерация изображения через DALL-E
        
        Args:
            prompt: Описание изображения на английском
            model: Модель (dall-e-2, dall-e-3)
            size: Размер изображения (1024x1024, 1792x1024, 1024x1792 для DALL-E 3)
            quality: Качество (standard, hd для DALL-E 3)
            n: Количество изображений (1-10, для DALL-E 3 только 1)
            
        Returns:
            URL сгенерированного изображения
            
        Raises:
            ImageGenerationError: При ошибках генерации
        """
        try:
            log_api_request(logger, "POST", f"{self.base_url}/images/generations", {
                "model": model,
                "size": size,
                "quality": quality
            })
            
            import time
            start_time = time.time()
            
            # Генерация изображения
            response: ImagesResponse = await self.client.images.generate(
                model=model,
                prompt=prompt,
                size=size,
                quality=quality if model == "dall-e-3" else "standard",
                n=n if model != "dall-e-3" else 1  # DALL-E 3 поддерживает только n=1
            )
            
            elapsed_time = time.time() - start_time
            log_api_response(logger, 200, elapsed_time, success=True)
            
            if not response.data:
                raise ImageGenerationError("API вернул пустой ответ без изображений")
            
            image_url = response.data[0].url
            
            logger.info(f"Изображение сгенерировано успешно | Time: {elapsed_time:.2f}s")
            
            return image_url
            
        except Exception as e:
            error_message = str(e).lower()
            
            if "content policy" in error_message or "safety" in error_message:
                log_exception(logger, e, "Промпт нарушает политику контента")
                raise ImageGenerationError(
                    "Промпт был отклонен из-за нарушения политики контента",
                    original_error=e
                )
            
            elif "429" in error_message or "rate limit" in error_message:
                log_exception(logger, e, "Rate limit для генерации изображений")
                raise APIRateLimitError(
                    "Превышен лимит генерации изображений. Попробуйте позже",
                    retry_after=60,
                    original_error=e
                )
            
            else:
                log_exception(logger, e, "Ошибка генерации изображения")
                raise ImageGenerationError(
                    f"Не удалось сгенерировать изображение: {str(e)}",
                    original_error=e
                )
    
    async def download_image(self, image_url: str, save_path: Optional[Path] = None) -> bytes:
        """
        Скачивание изображения по URL
        
        Args:
            image_url: URL изображения
            save_path: Путь для сохранения (опционально)
            
        Returns:
            Байты изображения
            
        Raises:
            APIConnectionError: При ошибках скачивания
        """
        try:
            logger.debug(f"Скачивание изображения: {image_url}")
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(image_url)
                response.raise_for_status()
                
                image_bytes = response.content
                
                # Сохранение файла, если указан путь
                if save_path:
                    save_path.parent.mkdir(parents=True, exist_ok=True)
                    save_path.write_bytes(image_bytes)
                    logger.info(f"Изображение сохранено: {save_path}")
                
                logger.debug(f"Изображение скачано: {len(image_bytes)} байт")
                return image_bytes
                
        except Exception as e:
            log_exception(logger, e, "Ошибка скачивания изображения")
            raise APIConnectionError(
                f"Не удалось скачать изображение: {str(e)}",
                original_error=e
            )
    
    async def transcribe_audio(
        self,
        audio_file_path: Path,
        model: str = "whisper-1",
        language: Optional[str] = "ru"
    ) -> str:
        """
        Транскрибация аудио через Whisper
        
        Args:
            audio_file_path: Путь к аудио файлу
            model: Модель (whisper-1)
            language: Язык аудио (ru, en, etc.)
            
        Returns:
            Распознанный текст
            
        Raises:
            TranscriptionError: При ошибках транскрибации
        """
        try:
            if not audio_file_path.exists():
                raise TranscriptionError(f"Аудио файл не найден: {audio_file_path}")
            
            log_api_request(logger, "POST", f"{self.base_url}/audio/transcriptions", {
                "model": model,
                "language": language
            })
            
            import time
            start_time = time.time()
            
            # Открываем файл в бинарном режиме
            with open(audio_file_path, "rb") as audio_file:
                # Транскрибация
                response = await self.client.audio.transcriptions.create(
                    model=model,
                    file=audio_file,
                    language=language
                )
            
            elapsed_time = time.time() - start_time
            log_api_response(logger, 200, elapsed_time, success=True)
            
            text = response.text.strip()
            
            logger.info(f"Аудио транскрибировано | Длина текста: {len(text)} символов | Time: {elapsed_time:.2f}s")
            
            return text
            
        except FileNotFoundError as e:
            log_exception(logger, e, "Файл не найден")
            raise TranscriptionError(
                f"Аудио файл не найден: {audio_file_path}",
                original_error=e
            )
        
        except Exception as e:
            log_exception(logger, e, "Ошибка транскрибации")
            raise TranscriptionError(
                f"Не удалось транскрибировать аудио: {str(e)}",
                original_error=e
            )
    
    async def validate_connection(self) -> bool:
        """
        Проверка подключения к API
        
        Returns:
            True если подключение успешно, False иначе
        """
        try:
            logger.info("Проверка подключения к ProxyAPI...")
            
            # Простой тестовый запрос
            await self.chat_completion(
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=10
            )
            
            logger.info("✓ Подключение к ProxyAPI успешно")
            return True
            
        except Exception as e:
            logger.error(f"✗ Ошибка подключения к ProxyAPI: {str(e)}")
            return False
    
    async def close(self):
        """Закрытие клиента и освобождение ресурсов"""
        await self.client.close()
        logger.debug("ProxyAPI клиент закрыт")

