"""
Клавиатуры для Telegram бота

Создает интерактивные кнопки для удобного взаимодействия с пользователем.
"""

from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def get_ideas_keyboard(num_ideas: int = 5) -> InlineKeyboardMarkup:
    """
    Клавиатура для выбора идеи (полупрозрачные кнопки)
    
    Создает кнопки для каждой идеи + кнопку для генерации новых идей.
    
    Args:
        num_ideas: Количество идей (обычно 5)
        
    Returns:
        Клавиатура с кнопками
    """
    # Создаем кнопки для идей (по 2-3 в ряд для компактности)
    buttons = []
    
    # Идеи 1-3 в первом ряду
    row1 = [
        InlineKeyboardButton(text=f"▫️ Идея {i}", callback_data=f"idea_{i}")
        for i in range(1, min(4, num_ideas + 1))
    ]
    
    # Идеи 4-5 во втором ряду
    row2 = [
        InlineKeyboardButton(text=f"▫️ Идея {i}", callback_data=f"idea_{i}")
        for i in range(4, num_ideas + 1)
    ]
    
    # Кнопка для генерации новых идей
    row3 = [
        InlineKeyboardButton(
            text="🔄 Другие идеи",
            callback_data="regenerate_ideas"
        )
    ]
    
    # Собираем все ряды
    if row1:
        buttons.append(row1)
    if row2:
        buttons.append(row2)
    buttons.append(row3)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_continue_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для продолжения или завершения
    
    Предлагает создать новый пост или завершить работу.
    
    Returns:
        Клавиатура с кнопками
    """
    buttons = [
        [
            InlineKeyboardButton(
                text="▫️ Создать новый",
                callback_data="create_new"
            )
        ],
        [
            InlineKeyboardButton(
                text="▫️ Завершить",
                callback_data="finish"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_yes_no_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура Да/Нет для вопроса об иллюстрации
    
    Returns:
        Клавиатура с кнопками
    """
    buttons = [
        [
            InlineKeyboardButton(
                text="▫️ Да",
                callback_data="need_image_yes"
            ),
            InlineKeyboardButton(
                text="▫️ Нет",
                callback_data="need_image_no"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура с кнопкой отмены
    
    Позволяет пользователю отменить текущую операцию.
    
    Returns:
        Клавиатура с кнопкой отмены
    """
    buttons = [
        [
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data="cancel"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Главная клавиатура с постоянной кнопкой внизу чата
    
    Показывает кнопку "Новый диалог" которая всегда доступна.
    
    Returns:
        Клавиатура с постоянной кнопкой
    """
    buttons = [
        [
            KeyboardButton(text="✨ Новый диалог")
        ]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,  # Автоматический размер
        persistent=True  # Клавиатура остается после отправки сообщения
    )

