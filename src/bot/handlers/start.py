"""
Handler для команды /start

Обрабатывает начало работы с ботом и инициализацию FSM.
"""

import random
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from core.logger import get_logger, log_user_action
from bot.states import ContentGenerationStates
from bot.utils import send_with_typing
from bot.keyboards import get_main_keyboard

logger = get_logger(__name__)

# Создаем router для этого handler
start_router = Router()

# Хранилище данных о пользователях (в памяти)
# Структура: {user_id: {"last_interaction": datetime, "session_count": int}}
user_sessions = {}


@start_router.message(F.text == "✨ Новый диалог")
async def new_dialog(message: Message, state: FSMContext):
    """
    Обработка нажатия кнопки "Новый диалог"
    
    Запускает новую сессию генерации контента.
    """
    # Удаляем старые inline кнопки если они есть
    data = await state.get_data()
    last_buttons_message_id = data.get("last_buttons_message_id")
    
    if last_buttons_message_id:
        try:
            await message.bot.edit_message_reply_markup(
                chat_id=message.chat.id,
                message_id=last_buttons_message_id,
                reply_markup=None
            )
        except Exception as e:
            logger.warning(f"Не удалось удалить старые кнопки: {e}")
    
    # Вызываем cmd_start
    await cmd_start(message, state)


@start_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """
    Обработка команды /start
    
    Приветствует пользователя, объясняет функционал и запускает процесс генерации.
    """
    user_id = message.from_user.id
    username = message.from_user.username or "пользователь"
    first_name = message.from_user.first_name
    
    log_user_action(logger, user_id, "Команда /start", f"Username: {username}")
    
    # Удаляем старые inline кнопки если они есть
    data = await state.get_data()
    last_buttons_message_id = data.get("last_buttons_message_id")
    
    if last_buttons_message_id:
        try:
            await message.bot.edit_message_reply_markup(
                chat_id=message.chat.id,
                message_id=last_buttons_message_id,
                reply_markup=None
            )
        except Exception as e:
            logger.warning(f"Не удалось удалить старые кнопки: {e}")
    
    # Очищаем предыдущее состояние FSM
    await state.clear()
    
    # Проверяем данные пользователя из глобального хранилища
    now = datetime.now()
    user_data = user_sessions.get(user_id)
    
    # Определяем тип приветствия
    if user_data is None:
        # Совсем новый пользователь - полное приветствие
        greeting_type = "first_time"
        session_count = 1
    else:
        # Пользователь уже был
        last_interaction = user_data.get("last_interaction")
        session_count = user_data.get("session_count", 0) + 1
        
        # Проверяем, прошло ли более 12 часов
        time_diff = now - last_interaction
        if time_diff > timedelta(hours=12):
            # Давно не общались - приветствуем заново
            greeting_type = "after_break"
        else:
            # Недавно общались - продолжаем
            greeting_type = "continue"
    
    # Обновляем данные пользователя
    user_sessions[user_id] = {
        "last_interaction": now,
        "session_count": session_count
    }
    
    # Формируем приветствие в зависимости от типа
    if greeting_type == "first_time":
        # Полное приветствие для новых пользователей
        welcome_text = f"""Привет, {first_name}! 👋

Я помогу тебе создать крутые идеи для контента и превратить их в готовые посты с изображениями.

**Как это работает:**

1️⃣ Расскажешь мне о своей нише
2️⃣ Укажешь цель контента
3️⃣ Выберешь формат
4️⃣ Я сгенерирую 5 идей
5️⃣ Ты выберешь лучшую
6️⃣ Получишь готовый пост с изображением!

Это займет всего пару минут ⚡

Давай начнем! 

**Какая у тебя ниша?**

Например: фитнес, бизнес, образование, психология, кулинария и т.д.

💡 *Можешь отвечать голосовыми сообщениями!*"""
    
    elif greeting_type == "after_break":
        # Вернулся после перерыва - краткое напоминание
        welcome_text = f"""С возвращением, {first_name}! 👋

Создаём новый пост?

**Какая у тебя ниша?**

Например: фитнес, бизнес, образование, психология, кулинария и т.д.

💡 *Можешь отвечать голосовыми сообщениями!*"""
    
    else:  # greeting_type == "continue"
        # Только что общались - очень короткое приветствие (варианты)
        short_greetings = [
            f"Продолжим, {first_name}! 🚀\n\n**Какая ниша?**",
            f"Окей, {first_name}! 👌\n\n**Новый пост? Какая ниша?**",
            f"Го дальше! ⚡\n\n**Какая ниша?**",
            f"Ещё один пост? 💪\n\n**Ниша?**",
            f"Создаём! 🎯\n\n**Какая ниша?**",
            f"Поехали, {first_name}! 🔥\n\n**Ниша?**"
        ]
        
        base_greeting = random.choice(short_greetings)
        welcome_text = f"""{base_greeting}

Например: фитнес, бизнес, образование, психология, кулинария и т.д.

💡 *Можешь отвечать голосовыми сообщениями!*"""
    
    # Отправляем приветствие с typing indicator и главной клавиатурой
    await send_with_typing(
        bot=message.bot,
        chat_id=message.chat.id,
        text=welcome_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    
    # Устанавливаем состояние сбора ниши
    await state.set_state(ContentGenerationStates.COLLECTING_NICHE)
    
    # Инициализируем данные FSM
    await state.update_data(
        off_topic_count=0,  # Счетчик отклонений от темы
        user_id=user_id,
        username=username
    )
    
    logger.info(f"User {user_id} начал новую сессию | Тип: {greeting_type} | Сессия #{session_count}")

