"""
Handler для голосовых сообщений

Обрабатывает голосовые сообщения, транскрибирует их и обрабатывает как текст.
"""

import os
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from core.logger import get_logger, log_user_action, log_exception
from core.exceptions import TranscriptionError
from api.proxyapi_client import ProxyAPIClient
from bot.utils import send_typing_action
from bot.keyboards import get_main_keyboard

logger = get_logger(__name__)

# Создаем router
voice_router = Router()

# Глобальная ссылка на API клиент (будет установлена в main.py)
api_client: ProxyAPIClient = None


def setup_api_client(client: ProxyAPIClient):
    """Установить API клиент для handler"""
    global api_client
    api_client = client


@voice_router.message(F.voice)
async def handle_voice(message: Message, state: FSMContext):
    """
    Обработка голосового сообщения
    
    1. Скачивает голосовое
    2. Транскрибирует через Whisper
    3. Показывает распознанный текст
    4. Обрабатывает как текстовое сообщение
    """
    user_id = message.from_user.id
    log_user_action(logger, user_id, "Получено голосовое сообщение")
    
    try:
        # Показываем typing indicator пока обрабатываем
        await send_typing_action(message.bot, message.chat.id, duration=2)
        
        # Получаем информацию о голосовом сообщении
        voice = message.voice
        file_id = voice.file_id
        
        # Скачиваем файл
        file = await message.bot.get_file(file_id)
        
        # Создаем временную папку если не существует
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        
        # Путь для сохранения
        temp_file_path = temp_dir / f"voice_{user_id}_{message.message_id}.ogg"
        
        # Скачиваем файл
        await message.bot.download_file(file.file_path, destination=temp_file_path)
        
        logger.info(f"Голосовое сообщение скачано: {temp_file_path}")
        
        # Транскрибируем
        transcribed_text = await api_client.transcribe_audio(
            audio_file_path=temp_file_path,
            language="ru"
        )
        
        # Удаляем временный файл
        try:
            os.remove(temp_file_path)
        except Exception as e:
            logger.warning(f"Не удалось удалить временный файл: {e}")
        
        logger.info(f"Голосовое транскрибировано | User {user_id} | Текст: {transcribed_text[:100]}")
        
        # Показываем распознанный текст пользователю
        await message.answer(
            f"📝 Текст сообщения:\n\n{transcribed_text}",
            reply_markup=get_main_keyboard()
        )
        
        # Создаем копию сообщения с обновленным текстом
        # Message в aiogram 3.x является frozen (неизменяемым), поэтому используем model_copy
        text_message = message.model_copy(update={"text": transcribed_text})
        
        # Обрабатываем как обычное текстовое сообщение
        # Находим текущее состояние и обрабатываем соответственно
        current_state = await state.get_state()
        
        # Импортируем handlers здесь чтобы избежать циклической зависимости
        from bot.handlers.conversation import (
            handle_niche,
            handle_goal,
            handle_format
        )
        from bot.states import ContentGenerationStates
        
        # Вызываем соответствующий handler в зависимости от состояния
        if current_state == ContentGenerationStates.COLLECTING_NICHE.state:
            await handle_niche(text_message, state)
        elif current_state == ContentGenerationStates.COLLECTING_GOAL.state:
            await handle_goal(text_message, state)
        elif current_state == ContentGenerationStates.COLLECTING_FORMAT.state:
            await handle_format(text_message, state)
        else:
            # Для других состояний просто показываем текст
            await message.answer(
                "Спасибо! Но сейчас мне нужен выбор из кнопок, а не текст 😊",
                reply_markup=get_main_keyboard()
            )
        
    except TranscriptionError as e:
        log_exception(logger, e, "Ошибка транскрибации")
        
        await message.answer(
            "😔 Не удалось распознать голосовое сообщение.\n\n"
            "Попробуйте:\n"
            "• Говорить четче и громче\n"
            "• Уменьшить фоновый шум\n"
            "• Или отправить текстом",
            reply_markup=get_main_keyboard()
        )
    
    except Exception as e:
        log_exception(logger, e, "Неожиданная ошибка при обработке голосового")
        
        await message.answer(
            "😔 Произошла ошибка при обработке голосового сообщения.\n\n"
            "Попробуйте отправить текстом или повторите голосовое.",
            reply_markup=get_main_keyboard()
        )

