"""
Handler для основного диалога

Обрабатывает все состояния процесса генерации контента.
"""

import io
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext

from core.logger import get_logger, log_user_action, log_exception
from core.exceptions import GenerationError, ModerationError
from bot.states import ContentGenerationStates, get_state_question
from bot.keyboards import get_ideas_keyboard, get_continue_keyboard, get_yes_no_keyboard, get_main_keyboard
from bot.utils import (
    send_with_typing,
    send_typing_action,
    format_ideas_message,
    format_post_with_hashtags,
    safe_send_message
)
from services.moderation import ModerationService
from services.idea_generator import IdeaGenerator
from services.post_generator import PostGenerator
from api.proxyapi_client import ProxyAPIClient

logger = get_logger(__name__)

# Создаем router
conversation_router = Router()

# Глобальные ссылки на сервисы (будут установлены в main.py)
moderation_service: ModerationService = None
idea_generator: IdeaGenerator = None
post_generator: PostGenerator = None
api_client: ProxyAPIClient = None


def setup_services(moderation: ModerationService, ideas: IdeaGenerator, posts: PostGenerator, api: ProxyAPIClient):
    """Установить сервисы для handlers"""
    global moderation_service, idea_generator, post_generator, api_client
    moderation_service = moderation
    idea_generator = ideas
    post_generator = posts
    api_client = api


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def reformulate_user_input(user_text: str, context: str) -> str:
    """
    Переформулировать ввод пользователя в грамотную форму
    
    Args:
        user_text: Текст пользователя (например, "я хлеб пеку")
        context: Контекст ('niche', 'goal', 'format')
        
    Returns:
        Грамотно сформулированный текст (например, "Выпечка хлеба")
    """
    try:
        if context == 'niche':
            prompt = f"""Переформулируй текст пользователя в грамотную форму для описания ниши/темы.

Пользователь написал: "{user_text}"

Правила:
- Если написано как действие ("я хлеб пеку", "делаю мебель"), преобразуй в существительное ("Выпечка хлеба", "Изготовление мебели")
- Если написано некорректно ("собираю машины"), сделай грамотно ("Сборка автомобилей")
- Сохрани смысл, но сделай формулировку профессиональной
- Максимум 3-5 слов
- Только суть, без лишних слов

Ответь ТОЛЬКО переформулированным текстом, без объяснений."""

        elif context == 'goal':
            prompt = f"""Переформулируй цель пользователя в грамотную форму.

Пользователь написал: "{user_text}"

Правила:
- Преобразуй в инфинитив если нужно ("хочу клиентов" → "Привлечение клиентов")
- Сделай формулировку четкой и профессиональной  
- Сохрани смысл
- Максимум 5-7 слов

Ответь ТОЛЬКО переформулированным текстом, без объяснений."""

        elif context == 'format':
            prompt = f"""Переформулируй формат контента в грамотную форму.

Пользователь написал: "{user_text}"

Правила:
- Сделай формулировку четкой ("пост инсте" → "Пост для Instagram")
- Сохрани смысл
- Максимум 5-7 слов

Ответь ТОЛЬКО переформулированным текстом, без объяснений."""
        
        else:
            return user_text
        
        # Запрос к AI
        response = await api_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model="gpt-4o-mini",  # Быстрая модель для простой задачи
            temperature=0.3,  # Низкая температура для точности
            max_tokens=50
        )
        
        reformulated = response.strip().strip('"').strip("'")
        logger.debug(f"Переформулировка | '{user_text}' → '{reformulated}'")
        
        return reformulated
        
    except Exception as e:
        logger.warning(f"Ошибка переформулировки, используем оригинал: {e}")
        return user_text  # В случае ошибки возвращаем оригинал

async def check_and_moderate(
    message: Message,
    state: FSMContext,
    current_step: str,
    bot_question: str
) -> bool:
    """
    Проверить релевантность сообщения и применить модерацию
    
    Returns:
        True если сообщение релевантно, False если нет (и диалог нужно прервать)
    """
    user_response = message.text
    data = await state.get_data()
    off_topic_count = data.get("off_topic_count", 0)
    
    # Проверка на мат
    if moderation_service.detect_offensive_content(user_response):
        off_topic_count += 1
        await state.update_data(off_topic_count=off_topic_count)
        
        if off_topic_count == 1:
            await message.answer(
                "Пожалуйста, давай общаться уважительно 🙏\n\n"
                "Я здесь, чтобы помочь с созданием контента.\n\n"
                "Если у тебя есть вопросы или проблемы, давай обсудим их конструктивно.",
                reply_markup=get_main_keyboard()
            )
            return False
        else:
            await message.answer(
                "Мне жаль, но я не могу продолжать общение в таком ключе.\n\n"
                "Если захочешь работать над контентом, буду рад помочь.\n\n"
                "До встречи! 👋",
                reply_markup=get_main_keyboard()
            )
            await state.clear()
            return False
    
    # Проверка релевантности через AI
    try:
        result = await moderation_service.check_relevance(
            current_step=current_step,
            bot_question=bot_question,
            user_response=user_response
        )
        
        if result["is_relevant"]:
            # Сбрасываем счетчик если ответ релевантен
            await state.update_data(off_topic_count=0)
            return True
        
        # Сообщение нерелевантно
        off_topic_count += 1
        await state.update_data(off_topic_count=off_topic_count)
        
        # Проверяем, нужно ли завершить диалог
        if moderation_service.should_end_conversation(off_topic_count):
            await message.answer(
                moderation_service.get_redirection_message(
                    off_topic_count, 
                    bot_question
                ),
                reply_markup=get_main_keyboard()
            )
            await state.clear()
            return False
        
        # Возвращаем к теме
        redirect_msg = moderation_service.get_redirection_message(
            off_topic_count,
            bot_question,
            result.get("suggestion")
        )
        
        await send_with_typing(
            bot=message.bot,
            chat_id=message.chat.id,
            text=redirect_msg,
            reply_markup=get_main_keyboard()
        )
        
        return False
        
    except ModerationError as e:
        logger.error(f"Ошибка модерации: {e}")
        # В случае ошибки модерации, считаем сообщение релевантным
        return True


# ============================================================================
# STATE HANDLERS
# ============================================================================

@conversation_router.message(ContentGenerationStates.COLLECTING_NICHE, F.text)
async def handle_niche(message: Message, state: FSMContext):
    """Обработка ввода ниши"""
    user_id = message.from_user.id
    log_user_action(logger, user_id, "Ввод ниши", message.text[:50])
    
    # Модерация
    if not await check_and_moderate(
        message,
        state,
        "COLLECTING_NICHE",
        get_state_question("COLLECTING_NICHE")
    ):
        return
    
    # Сохраняем оригинал
    niche_original = message.text.strip()
    
    # Переформулируем для красивого ответа
    niche_formatted = await reformulate_user_input(niche_original, 'niche')
    
    # Сохраняем оригинал (для генерации контента)
    await state.update_data(niche=niche_original)
    
    # Переходим к сбору цели
    response_text = f"""Отлично! **{niche_formatted}** - интересная ниша 💡

Теперь скажи, **какая главная цель твоего контента?**

Например:
• Привлечь новых подписчиков
• Продать продукт или услугу
• Обучить аудиторию
• Повысить вовлеченность
• Что-то другое?"""
    
    await send_with_typing(
        bot=message.bot,
        chat_id=message.chat.id,
        text=response_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    
    await state.set_state(ContentGenerationStates.COLLECTING_GOAL)


@conversation_router.message(ContentGenerationStates.COLLECTING_GOAL, F.text)
async def handle_goal(message: Message, state: FSMContext):
    """Обработка ввода цели"""
    user_id = message.from_user.id
    log_user_action(logger, user_id, "Ввод цели", message.text[:50])
    
    # Модерация
    if not await check_and_moderate(
        message,
        state,
        "COLLECTING_GOAL",
        get_state_question("COLLECTING_GOAL")
    ):
        return
    
    # Сохраняем оригинал
    goal_original = message.text.strip()
    
    # Переформулируем для красивого ответа
    goal_formatted = await reformulate_user_input(goal_original, 'goal')
    
    # Сохраняем оригинал (для генерации контента)
    await state.update_data(goal=goal_original)
    
    # Переходим к сбору формата
    response_text = f"""Понял! **{goal_formatted}** 🎯

Последний вопрос: **в каком формате ты хочешь создать контент?**

Например:
• Пост для Instagram/VK/Facebook
• Статья для блога или Telegram-канала
• Сценарий для видео/Reels/Shorts
• Email-рассылка
• Что-то другое?"""
    
    await send_with_typing(
        bot=message.bot,
        chat_id=message.chat.id,
        text=response_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    
    await state.set_state(ContentGenerationStates.COLLECTING_FORMAT)


@conversation_router.message(ContentGenerationStates.COLLECTING_FORMAT, F.text)
async def handle_format(message: Message, state: FSMContext):
    """Обработка ввода формата и запуск генерации идей"""
    user_id = message.from_user.id
    log_user_action(logger, user_id, "Ввод формата", message.text[:50])
    
    # Модерация
    if not await check_and_moderate(
        message,
        state,
        "COLLECTING_FORMAT",
        get_state_question("COLLECTING_FORMAT")
    ):
        return
    
    # Сохраняем оригинал
    format_original = message.text.strip()
    
    # Переформулируем для красивого ответа
    format_formatted = await reformulate_user_input(format_original, 'format')
    
    # Сохраняем оба варианта
    await state.update_data(
        format_type=format_original,  # Для генерации контента
        format_formatted=format_formatted  # Для красивого отображения
    )
    
    # Получаем все собранные данные
    data = await state.get_data()
    niche = data.get("niche")
    goal = data.get("goal")
    
    # Сообщаем о начале генерации
    await send_with_typing(
        bot=message.bot,
        chat_id=message.chat.id,
        text=f"Супер! **{format_formatted}** ✨\n\nСейчас подумаю и предложу тебе **5 крутых идей** для контента! 🤔",
        parse_mode="Markdown",
        typing_duration=2,
        reply_markup=get_main_keyboard()
    )
    
    # Переходим к генерации идей
    await state.set_state(ContentGenerationStates.GENERATING_IDEAS)
    
    # Запускаем генерацию (используем оригинальный текст для AI)
    await generate_and_show_ideas(message, state, niche, goal, format_original)


async def generate_and_show_ideas(message: Message, state: FSMContext, niche: str, goal: str, format_type: str):
    """Генерация и отображение идей"""
    chat_id = message.chat.id
    bot = message.bot
    
    try:
        # Показываем процесс
        await send_typing_action(bot, chat_id, duration=3)
        await message.answer("⏳ Генерирую идеи...")
        
        # Генерируем идеи
        ideas = await idea_generator.generate_ideas(
            niche=niche,
            goal=goal,
            format_type=format_type
        )
        
        # Сохраняем идеи
        await state.update_data(ideas=ideas)
        
        # Форматируем и отправляем
        ideas_text = format_ideas_message(ideas)
        
        # Показываем typing indicator
        await send_typing_action(bot, chat_id, duration=2)
        
        # Отправляем идеи с кнопками
        ideas_message = await bot.send_message(
            chat_id=chat_id,
            text=ideas_text,
            reply_markup=get_ideas_keyboard(len(ideas)),
            parse_mode="Markdown"
        )
        
        # Сохраняем message_id для последующего удаления кнопок
        await state.update_data(last_buttons_message_id=ideas_message.message_id)
        
        # Переходим к ожиданию выбора
        await state.set_state(ContentGenerationStates.WAITING_IDEA_CHOICE)
        
    except GenerationError as e:
        logger.error(f"Ошибка генерации идей: {e}")
        await message.answer(
            "😔 Произошла ошибка при генерации идей.\n\n"
            "Попробуйте еще раз через пару секунд, или отправьте /start для перезапуска.",
            reply_markup=get_main_keyboard()
        )
        await state.set_state(ContentGenerationStates.COLLECTING_FORMAT)


def should_offer_image(format_type: str) -> bool:
    """
    Определить, нужно ли предлагать иллюстрацию для данного формата
    
    Args:
        format_type: Формат контента
        
    Returns:
        True если формат предполагает публикацию с изображением
    """
    format_lower = format_type.lower()
    
    # Форматы, которые обычно публикуются с изображением
    with_image_keywords = [
        "пост", "статья", "публикация", "заметка", "блог", 
        "instagram", "facebook", "vk", "telegram", "соцсет"
    ]
    
    # Форматы, которые не требуют изображения
    without_image_keywords = [
        "сценарий", "скрипт", "инструкция", "план", "текст",
        "email", "письмо", "рассылка", "описание"
    ]
    
    # Проверяем на наличие ключевых слов
    for keyword in without_image_keywords:
        if keyword in format_lower:
            return False
    
    for keyword in with_image_keywords:
        if keyword in format_lower:
            return True
    
    # По умолчанию предлагаем изображение
    return True


@conversation_router.callback_query(ContentGenerationStates.WAITING_IDEA_CHOICE, F.data.startswith("idea_"))
async def handle_idea_choice(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора идеи"""
    await callback.answer()
    
    user_id = callback.from_user.id
    idea_id = int(callback.data.split("_")[1])
    
    log_user_action(logger, user_id, "Выбор идеи", f"ID: {idea_id}")
    
    # Удаляем только кнопки (с анимацией), оставляем сообщение с идеями
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception as e:
        logger.warning(f"Не удалось удалить кнопки: {e}")
    
    # Получаем выбранную идею
    data = await state.get_data()
    ideas = data.get("ideas", [])
    
    selected_idea = None
    for idea in ideas:
        if idea["id"] == idea_id:
            selected_idea = idea
            break
    
    if not selected_idea:
        await callback.message.answer("😔 Ошибка: идея не найдена. Попробуйте еще раз.")
        return
    
    # Сохраняем выбранную идею
    await state.update_data(selected_idea=selected_idea)
    
    # Подтверждаем выбор
    await callback.message.answer(
        f"Отлично! ✨\n\n"
        f"Идея **\"{selected_idea['title']}\"**",
        parse_mode="Markdown"
    )
    
    # Определяем, нужно ли предлагать иллюстрацию
    format_type = data.get("format_type", "")
    format_formatted = data.get("format_formatted", format_type)  # Используем красиво переформулированный
    
    if should_offer_image(format_type):
        # Спрашиваем нужна ли иллюстрация (используем красивую формулировку)
        # Формируем правильный вопрос с правильным падежом
        format_lower = format_formatted.lower()
        
        # Конвертируем формат в дательный падеж
        if "пост" in format_lower and "для" in format_lower:
            # "Пост для Instagram" → "посту для Instagram"
            format_dative = format_formatted.replace("Пост", "посту").replace("пост", "посту")
            question_text = f"Нужна иллюстрация к {format_dative.lower()}?"
        elif "пост" in format_lower:
            question_text = "Нужна иллюстрация к посту?"
        elif "статья" in format_lower:
            # "Статья для блога" → "статье для блога"
            format_dative = format_formatted.replace("Статья", "статье").replace("статья", "статье")
            question_text = f"Нужна иллюстрация к {format_dative.lower()}?"
        elif "сценарий" in format_lower:
            format_dative = format_formatted.replace("Сценарий", "сценарию").replace("сценарий", "сценарию")
            question_text = f"Нужна иллюстрация к {format_dative.lower()}?"
        elif "email" in format_lower or "письмо" in format_lower or "рассылка" in format_lower:
            question_text = "Нужна иллюстрация к рассылке?"
        else:
            # По умолчанию
            question_text = f"Нужна иллюстрация для этого контента?"
        
        image_question = await callback.message.answer(
            question_text,
            reply_markup=get_yes_no_keyboard()
        )
        
        # Сохраняем message_id для последующего удаления кнопок
        await state.update_data(last_buttons_message_id=image_question.message_id)
        
        await state.set_state(ContentGenerationStates.ASKING_IMAGE)
    else:
        # Сразу генерируем без изображения
        await state.update_data(need_image=False)
        await callback.message.answer(
            "Сейчас создам для тебя готовый текст...\n\n"
            "⏳ Это займет около 20-30 секунд",
            reply_markup=get_main_keyboard()
        )
        
        # Переходим к генерации
        await state.set_state(ContentGenerationStates.GENERATING_POST)
        niche = data.get("niche")
        goal = data.get("goal")
        
        await generate_and_send_post(callback.message, state, niche, goal, format_type, selected_idea)


@conversation_router.callback_query(ContentGenerationStates.ASKING_IMAGE, F.data == "need_image_yes")
async def handle_image_yes(callback: CallbackQuery, state: FSMContext):
    """Пользователь хочет иллюстрацию"""
    await callback.answer()
    
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    log_user_action(logger, user_id, "Иллюстрация нужна")
    
    # Удаляем сообщение с вопросом об иллюстрации
    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение с вопросом: {e}")
    
    # Сохраняем выбор
    await state.update_data(need_image=True)
    
    await callback.bot.send_message(
        chat_id=chat_id,
        text="Сейчас создам для тебя готовый пост с изображением...\n\n"
             "⏳ Это займет около 30-40 секунд",
        reply_markup=get_main_keyboard()
    )
    
    # Переходим к генерации
    await state.set_state(ContentGenerationStates.GENERATING_POST)
    
    data = await state.get_data()
    niche = data.get("niche")
    goal = data.get("goal")
    format_type = data.get("format_type")
    selected_idea = data.get("selected_idea")
    
    await generate_and_send_post(callback.message, state, niche, goal, format_type, selected_idea)


@conversation_router.callback_query(ContentGenerationStates.ASKING_IMAGE, F.data == "need_image_no")
async def handle_image_no(callback: CallbackQuery, state: FSMContext):
    """Пользователь не хочет иллюстрацию"""
    await callback.answer()
    
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    log_user_action(logger, user_id, "Иллюстрация не нужна")
    
    # Удаляем сообщение с вопросом об иллюстрации
    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение с вопросом: {e}")
    
    # Сохраняем выбор
    await state.update_data(need_image=False)
    
    await callback.bot.send_message(
        chat_id=chat_id,
        text="Сейчас создам для тебя готовый текст...\n\n"
             "⏳ Это займет около 20-30 секунд",
        reply_markup=get_main_keyboard()
    )
    
    # Переходим к генерации
    await state.set_state(ContentGenerationStates.GENERATING_POST)
    
    data = await state.get_data()
    niche = data.get("niche")
    goal = data.get("goal")
    format_type = data.get("format_type")
    selected_idea = data.get("selected_idea")
    
    await generate_and_send_post(callback.message, state, niche, goal, format_type, selected_idea)


@conversation_router.callback_query(ContentGenerationStates.WAITING_IDEA_CHOICE, F.data == "regenerate_ideas")
async def handle_regenerate_ideas(callback: CallbackQuery, state: FSMContext):
    """Обработка запроса на генерацию новых идей"""
    await callback.answer()
    
    user_id = callback.from_user.id
    log_user_action(logger, user_id, "Запрос регенерации идей")
    
    # Удаляем только кнопки
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception as e:
        logger.warning(f"Не удалось удалить кнопки: {e}")
    
    data = await state.get_data()
    niche = data.get("niche")
    goal = data.get("goal")
    format_type = data.get("format_type")
    
    await callback.message.answer("Хорошо, генерирую другие идеи! 🔄", reply_markup=get_main_keyboard())
    
    await state.set_state(ContentGenerationStates.GENERATING_IDEAS)
    await generate_and_show_ideas(callback.message, state, niche, goal, format_type)


async def generate_and_send_post(message: Message, state: FSMContext, niche: str, goal: str, format_type: str, idea: dict):
    """Генерация и отправка полного поста"""
    chat_id = message.chat.id
    bot = message.bot
    user_id = message.from_user.id
    
    # Получаем флаг нужна ли картинка
    data = await state.get_data()
    need_image = data.get("need_image", False)
    
    try:
        # Показываем процесс
        await send_typing_action(bot, chat_id, duration=3)
        
        if need_image:
            # Генерируем с изображением
            post_data, image_url, image_bytes = await post_generator.generate_complete_post(
                niche=niche,
                goal=goal,
                format_type=format_type,
                idea=idea
            )
            
            log_user_action(logger, user_id, "Пост с изображением сгенерирован")
            
            # Отправляем изображение (с retry механизмом)
            photo_sent = False
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    photo = BufferedInputFile(image_bytes, filename="post_image.png")
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=photo,
                        request_timeout=30  # Увеличиваем таймаут для больших изображений
                    )
                    photo_sent = True
                    logger.info(f"✓ Изображение успешно отправлено (попытка {attempt + 1})")
                    break
                except Exception as e:
                    logger.warning(
                        f"Попытка {attempt + 1}/{max_retries} отправки фото не удалась: {type(e).__name__}: {e}"
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)  # Пауза перед повторной попыткой
                    else:
                        logger.error(f"✗ Не удалось отправить изображение после {max_retries} попыток")
            
            # Отправляем текст поста
            post_text = format_post_with_hashtags(post_data)
            
            # Если изображение не отправилось, предупреждаем пользователя
            if not photo_sent:
                warning_text = (
                    "⚠️ _К сожалению, не удалось отправить изображение из-за проблем с сетью._\n"
                    "_Но вот твой готовый текст поста:_\n\n"
                )
                post_text = warning_text + post_text
            
            await send_with_typing(
                bot=bot,
                chat_id=chat_id,
                text=f"{'━' * 30}\n\n{post_text}\n\n{'━' * 30}",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard(),
                typing_duration=2
            )
        else:
            # Генерируем только текст
            post_data = await post_generator.generate_post_text(
                niche=niche,
                goal=goal,
                format_type=format_type,
                idea=idea
            )
            
            log_user_action(logger, user_id, "Текст поста сгенерирован")
            
            # Отправляем только текст
            post_text = format_post_with_hashtags(post_data)
            
            await send_with_typing(
                bot=bot,
                chat_id=chat_id,
                text=f"{'━' * 30}\n\n{post_text}\n\n{'━' * 30}",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard(),
                typing_duration=2
            )
        
        # Финальное сообщение
        continue_message = await message.answer(
            "✅ Готово!\n\n"
            "Что делаем дальше?",
            reply_markup=get_continue_keyboard()
        )
        
        # Сохраняем message_id для последующего удаления кнопок
        await state.update_data(last_buttons_message_id=continue_message.message_id)
        
        # Переходим в состояние завершения
        await state.set_state(ContentGenerationStates.COMPLETED)
        
    except (GenerationError, Exception) as e:
        log_exception(logger, e, "Ошибка генерации поста")
        
        await message.answer(
            "😔 Произошла ошибка при генерации.\n\n"
            "Попробуйте еще раз или отправьте /start для перезапуска.",
            reply_markup=get_main_keyboard()
        )
        
        # Возвращаемся к выбору идеи
        await state.set_state(ContentGenerationStates.WAITING_IDEA_CHOICE)


@conversation_router.callback_query(ContentGenerationStates.COMPLETED, F.data == "create_new")
async def handle_create_new(callback: CallbackQuery, state: FSMContext):
    """Создание нового поста"""
    await callback.answer()
    
    user_id = callback.from_user.id
    log_user_action(logger, user_id, "Создание нового поста")
    
    # Удаляем кнопки с текущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception as e:
        logger.warning(f"Не удалось удалить кнопки: {e}")
    
    # Очищаем состояние
    await state.clear()
    
    # Перезапускаем процесс
    await callback.message.answer(
        "Отлично! Давай создадим еще один 🚀\n\n"
        "**Какая у тебя ниша?**",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    
    await state.set_state(ContentGenerationStates.COLLECTING_NICHE)
    await state.update_data(off_topic_count=0, user_id=user_id)


@conversation_router.callback_query(ContentGenerationStates.COMPLETED, F.data == "finish")
async def handle_finish(callback: CallbackQuery, state: FSMContext):
    """Завершение работы"""
    await callback.answer()
    
    user_id = callback.from_user.id
    log_user_action(logger, user_id, "Завершение работы")
    
    # Удаляем кнопки с текущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception as e:
        logger.warning(f"Не удалось удалить кнопки: {e}")
    
    await callback.message.answer(
        "Было приятно помочь! 😊\n\n"
        "Возвращайся, когда понадобятся новые идеи для контента.\n\n"
        "Нажми **✨ Новый диалог** когда будешь готов создать новый пост.\n\n"
        "Удачи с твоим контентом! 🚀",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    
    await state.clear()

