"""
FSM состояния для управления диалогом

Определяет все возможные состояния разговора пользователя с ботом.
"""

from aiogram.fsm.state import State, StatesGroup


class ContentGenerationStates(StatesGroup):
    """
    Состояния процесса генерации контента
    
    Каждое состояние представляет этап диалога с пользователем.
    """
    
    # Начальное состояние
    INITIAL = State()
    
    # Сбор информации
    COLLECTING_NICHE = State()      # Запрос ниши
    COLLECTING_GOAL = State()       # Запрос цели
    COLLECTING_FORMAT = State()     # Запрос формата
    
    # Генерация идей
    GENERATING_IDEAS = State()      # Процесс генерации идей
    WAITING_IDEA_CHOICE = State()   # Ожидание выбора идеи
    
    # Вопрос об иллюстрации
    ASKING_IMAGE = State()          # Спрашиваем нужна ли картинка
    
    # Генерация поста
    GENERATING_POST = State()       # Процесс генерации поста
    
    # Завершение
    COMPLETED = State()             # Пост готов, предложение продолжить


# Описания состояний для логирования и отладки
STATE_DESCRIPTIONS = {
    "INITIAL": "Начало диалога",
    "COLLECTING_NICHE": "Сбор информации о нише",
    "COLLECTING_GOAL": "Сбор информации о цели",
    "COLLECTING_FORMAT": "Сбор информации о формате",
    "GENERATING_IDEAS": "Генерация идей",
    "WAITING_IDEA_CHOICE": "Ожидание выбора идеи",
    "ASKING_IMAGE": "Вопрос о необходимости иллюстрации",
    "GENERATING_POST": "Генерация поста",
    "COMPLETED": "Завершение, пост готов"
}


def get_state_description(state: str) -> str:
    """
    Получить описание состояния
    
    Args:
        state: Название состояния
        
    Returns:
        Описание состояния
    """
    return STATE_DESCRIPTIONS.get(state, "Неизвестное состояние")


# Вопросы бота для каждого состояния (используются в модерации)
STATE_QUESTIONS = {
    "COLLECTING_NICHE": "Какая у тебя ниша или тематика контента?",
    "COLLECTING_GOAL": "Какая главная цель твоего контента?",
    "COLLECTING_FORMAT": "В каком формате ты хочешь создать контент?"
}


def get_state_question(state: str) -> str:
    """
    Получить вопрос для состояния
    
    Args:
        state: Название состояния
        
    Returns:
        Вопрос, который задает бот в этом состоянии
    """
    return STATE_QUESTIONS.get(state, "")

