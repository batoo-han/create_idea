"""
Построители промптов с подстановкой данных

Берут шаблоны из templates.py и заполняют их реальными данными.
"""

from typing import Dict, List
from .templates import PromptTemplates


class PromptBuilder:
    """
    Построитель промптов с подстановкой данных
    
    Использует шаблоны и подставляет конкретные значения.
    """
    
    @staticmethod
    def build_moderation_prompt(
        current_step: str,
        bot_question: str,
        user_response: str
    ) -> str:
        """
        Построить промпт для модерации
        
        Args:
            current_step: Текущий этап диалога (COLLECTING_NICHE, COLLECTING_GOAL, etc.)
            bot_question: Вопрос, который задал бот
            user_response: Ответ пользователя
            
        Returns:
            Готовый промпт для AI
        """
        template = PromptTemplates.moderation_prompt()
        
        return template.format(
            current_step=current_step,
            bot_question=bot_question,
            user_response=user_response
        )
    
    @staticmethod
    def build_ideas_prompt(
        niche: str,
        goal: str,
        format_type: str
    ) -> str:
        """
        Построить промпт для генерации идей
        
        Args:
            niche: Ниша пользователя
            goal: Цель контента
            format_type: Формат контента
            
        Returns:
            Готовый промпт для AI
        """
        template = PromptTemplates.ideas_generation_prompt()
        
        return template.format(
            niche=niche,
            goal=goal,
            format=format_type
        )
    
    @staticmethod
    def build_post_prompt(
        niche: str,
        goal: str,
        format_type: str,
        idea_title: str,
        idea_description: str,
        key_elements: List[str]
    ) -> str:
        """
        Построить промпт для генерации поста
        
        Args:
            niche: Ниша пользователя
            goal: Цель контента
            format_type: Формат контента
            idea_title: Название выбранной идеи
            idea_description: Описание идеи
            key_elements: Ключевые элементы идеи
            
        Returns:
            Готовый промпт для AI
        """
        template = PromptTemplates.post_generation_prompt()
        
        # Форматируем key_elements как список
        key_elements_str = ", ".join([f'"{elem}"' for elem in key_elements])
        
        return template.format(
            niche=niche,
            goal=goal,
            format=format_type,
            idea_title=idea_title,
            idea_description=idea_description,
            key_elements=key_elements_str
        )
    
    @staticmethod
    def build_image_prompt_prompt(
        niche: str,
        format_type: str,
        post_title: str,
        post_content: str
    ) -> str:
        """
        Построить промпт для генерации промпта изображения
        
        Args:
            niche: Ниша
            format_type: Формат
            post_title: Заголовок поста
            post_content: Содержание поста
            
        Returns:
            Готовый промпт для AI
        """
        template = PromptTemplates.image_prompt_generation()
        
        # Обрезаем content если слишком длинный (для экономии токенов)
        if len(post_content) > 1000:
            post_content = post_content[:1000] + "..."
        
        return template.format(
            niche=niche,
            format=format_type,
            post_title=post_title,
            post_content=post_content
        )
    
    @staticmethod
    def build_system_message(role: str = "helper") -> Dict[str, str]:
        """
        Построить системное сообщение для AI
        
        Args:
            role: Роль AI (helper, moderator, creator)
            
        Returns:
            Словарь с системным сообщением
        """
        roles = {
            "helper": "Ты - полезный помощник в создании контента. Ты дружелюбен, профессионален и всегда стремишься помочь.",
            "moderator": "Ты - модератор диалога. Твоя задача объективно оценивать релевантность сообщений.",
            "creator": "Ты - креативный специалист по контент-маркетингу с богатым опытом."
        }
        
        return {
            "role": "system",
            "content": roles.get(role, roles["helper"])
        }
    
    @staticmethod
    def build_user_message(content: str) -> Dict[str, str]:
        """
        Построить пользовательское сообщение
        
        Args:
            content: Содержание сообщения
            
        Returns:
            Словарь с пользовательским сообщением
        """
        return {
            "role": "user",
            "content": content
        }
    
    @staticmethod
    def build_messages(system_role: str, user_prompt: str) -> List[Dict[str, str]]:
        """
        Построить полный список сообщений для API
        
        Args:
            system_role: Роль системы
            user_prompt: Промпт пользователя
            
        Returns:
            Список сообщений для API
        """
        return [
            PromptBuilder.build_system_message(system_role),
            PromptBuilder.build_user_message(user_prompt)
        ]

