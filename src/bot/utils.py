"""
Утилиты для бота

Вспомогательные функции для естественного поведения бота:
- Typing indicators
- Задержки
- Форматирование сообщений
"""

import asyncio
from typing import Optional
from aiogram import Bot
from aiogram.enums import ChatAction

from core.logger import get_logger

logger = get_logger(__name__)


async def send_typing_action(
    bot: Bot,
    chat_id: int,
    duration: float = 2.0
) -> None:
    """
    Показать индикатор печати (typing...)
    
    Создает иллюзию, что бот "думает" и печатает ответ.
    
    Args:
        bot: Экземпляр бота
        chat_id: ID чата
        duration: Длительность индикации в секундах
    """
    try:
        await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(duration)
    except Exception as e:
        logger.warning(f"Не удалось отправить typing action: {e}")


def calculate_delay(text_length: int, min_delay: float = 0.5, max_delay: float = 3.0, per_char: float = 0.01) -> float:
    """
    Рассчитать задержку перед ответом
    
    Задержка зависит от длины текста - чем длиннее, тем больше задержка.
    Это делает поведение бота более естественным.
    
    Args:
        text_length: Длина текста в символах
        min_delay: Минимальная задержка в секундах
        max_delay: Максимальная задержка в секундах
        per_char: Задержка на один символ
        
    Returns:
        Задержка в секундах
    """
    calculated = min_delay + (text_length * per_char)
    return min(max(calculated, min_delay), max_delay)


async def send_with_typing(
    bot: Bot,
    chat_id: int,
    text: str,
    typing_duration: Optional[float] = None,
    **kwargs
) -> None:
    """
    Отправить сообщение с предварительным typing indicator
    
    Args:
        bot: Экземпляр бота
        chat_id: ID чата
        text: Текст сообщения
        typing_duration: Длительность typing (если None, вычисляется автоматически)
        **kwargs: Дополнительные параметры для send_message
    """
    # Вычисляем задержку если не указана
    if typing_duration is None:
        typing_duration = calculate_delay(len(text))
    
    # Показываем typing
    await send_typing_action(bot, chat_id, typing_duration)
    
    # Отправляем сообщение
    await bot.send_message(chat_id=chat_id, text=text, **kwargs)


def format_ideas_message(ideas: list) -> str:
    """
    Форматировать список идей для отображения
    
    Args:
        ideas: Список идей в формате [{id, title, description, key_elements}]
        
    Returns:
        Красиво отформатированное сообщение
    """
    message_parts = ["Вот 5 идей для твоего контента 💡\n"]
    
    for idea in ideas:
        message_parts.append("━━━━━━━━━━━━━━━━")
        message_parts.append(f"💡 **Идея {idea['id']}: \"{idea['title']}\"**\n")
        message_parts.append(f"{idea['description']}\n")
        
        # Ключевые элементы если есть
        if idea.get('key_elements'):
            message_parts.append("**Ключевые элементы:**")
            for element in idea['key_elements']:
                message_parts.append(f"• {element}")
            message_parts.append("")
    
    message_parts.append("━━━━━━━━━━━━━━━━")
    message_parts.append("\nКакая идея тебе больше нравится? Выбери номер 👇")
    
    return "\n".join(message_parts)


def escape_markdown(text: str) -> str:
    """
    Экранировать специальные символы для Markdown
    
    Args:
        text: Исходный текст
        
    Returns:
        Текст с экранированными символами
    """
    # Символы, которые нужно экранировать в Markdown V2
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text


def truncate_text(text: str, max_length: int = 4000, suffix: str = "...") -> str:
    """
    Обрезать текст до максимальной длины
    
    Telegram имеет лимит на длину сообщения (4096 символов).
    
    Args:
        text: Исходный текст
        max_length: Максимальная длина
        suffix: Суффикс для обрезанного текста
        
    Returns:
        Обрезанный текст
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


async def safe_send_message(bot: Bot, chat_id: int, text: str, **kwargs) -> bool:
    """
    Безопасная отправка сообщения с обработкой ошибок
    
    Args:
        bot: Экземпляр бота
        chat_id: ID чата
        text: Текст сообщения
        **kwargs: Дополнительные параметры
        
    Returns:
        True если отправка успешна, False иначе
    """
    try:
        # Обрезаем текст если слишком длинный
        text = truncate_text(text)
        
        await bot.send_message(chat_id=chat_id, text=text, **kwargs)
        return True
        
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")
        
        # Пытаемся отправить упрощенное сообщение об ошибке
        try:
            await bot.send_message(
                chat_id=chat_id,
                text="Произошла ошибка при отправке сообщения 😔\nПопробуйте еще раз."
            )
        except:
            pass
        
        return False


def format_post_with_hashtags(post_data: dict) -> str:
    """
    Форматировать пост с хештегами
    
    Args:
        post_data: Данные поста в формате {content, hashtags, ...}
        
    Returns:
        Отформатированный текст поста
    """
    content = post_data.get("content", "")
    hashtags = post_data.get("hashtags", [])
    
    # Добавляем хештеги в конец если их нет в тексте
    if hashtags and not any(f"#{tag}" in content for tag in hashtags):
        hashtag_string = " ".join([f"#{tag}" for tag in hashtags])
        content = f"{content}\n\n{hashtag_string}"
    
    return content

