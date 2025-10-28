"""
Главный файл запуска Telegram бота

Инициализирует все компоненты и запускает бота.
"""

import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from core.logger import setup_logging, get_logger
from core.exceptions import ConfigurationError
from config.settings import get_settings
from api.proxyapi_client import ProxyAPIClient
from services.moderation import ModerationService
from services.idea_generator import IdeaGenerator
from services.post_generator import PostGenerator

# Импорт handlers
from bot.handlers.start import start_router
from bot.handlers.conversation import conversation_router, setup_services
from bot.handlers.voice import voice_router, setup_api_client

logger = get_logger(__name__)


async def main():
    """
    Главная функция запуска бота
    
    Выполняет:
    1. Инициализацию логирования
    2. Загрузку конфигурации
    3. Создание API клиента
    4. Инициализацию сервисов
    5. Настройку бота и диспетчера
    6. Регистрацию handlers
    7. Запуск polling
    """
    
    try:
        # ========================================
        # ЭТАП 1: ИНИЦИАЛИЗАЦИЯ ЛОГИРОВАНИЯ
        # ========================================
        
        print("Инициализация логирования...")
        
        # Загружаем настройки для логирования
        settings = get_settings()
        
        # Настраиваем логирование
        setup_logging(
            log_level=settings.log_level,
            log_file=settings.log_file,
            max_bytes=settings.log_max_bytes,
            backup_count=settings.log_backup_count,
            log_format=settings.log_format
        )
        
        logger.info("=" * 80)
        logger.info("ЗАПУСК CONTENT IDEAS GENERATOR BOT")
        logger.info("=" * 80)
        
        # ========================================
        # ЭТАП 2: ВАЛИДАЦИЯ КОНФИГУРАЦИИ
        # ========================================
        
        logger.info("Проверка конфигурации...")
        
        try:
            settings.validate_required_settings()
            logger.info("✓ Конфигурация валидна")
        except ConfigurationError as e:
            logger.critical(f"✗ Ошибка конфигурации: {e}")
            logger.critical("Проверьте файл .env и убедитесь, что все обязательные параметры установлены")
            sys.exit(1)
        
        # Выводим сводку настроек
        logger.info(settings.get_summary())
        
        # ========================================
        # ЭТАП 3: ИНИЦИАЛИЗАЦИЯ API КЛИЕНТА
        # ========================================
        
        logger.info("Инициализация API клиента...")
        
        api_client = ProxyAPIClient(
            api_key=settings.proxyapi_key,
            base_url=settings.proxyapi_base_url,
            timeout=60,
            max_retries=3
        )
        
        # Проверка подключения к API
        logger.info("Проверка подключения к ProxyAPI...")
        if await api_client.validate_connection():
            logger.info("✓ Подключение к ProxyAPI успешно")
        else:
            logger.error("✗ Не удалось подключиться к ProxyAPI")
            logger.error("Проверьте API ключ и доступность сервиса")
            # Продолжаем работу, возможно проблемы временные
        
        # ========================================
        # ЭТАП 4: ИНИЦИАЛИЗАЦИЯ СЕРВИСОВ
        # ========================================
        
        logger.info("Инициализация сервисов...")
        
        # Сервис модерации
        moderation_service = ModerationService(
            api_client=api_client,
            settings=settings
        )
        logger.info("✓ ModerationService инициализирован")
        
        # Генератор идей
        idea_generator = IdeaGenerator(
            api_client=api_client,
            settings=settings
        )
        logger.info("✓ IdeaGenerator инициализирован")
        
        # Генератор постов
        post_generator = PostGenerator(
            api_client=api_client,
            settings=settings
        )
        logger.info("✓ PostGenerator инициализирован")
        
        # ========================================
        # ЭТАП 5: НАСТРОЙКА БОТА И ДИСПЕТЧЕРА
        # ========================================
        
        logger.info("Настройка бота...")
        
        # Создание бота
        bot = Bot(
            token=settings.telegram_bot_token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.MARKDOWN
            )
        )
        
        # Создание диспетчера с хранилищем в памяти
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        logger.info("✓ Bot и Dispatcher созданы")
        
        # ========================================
        # ЭТАП 6: РЕГИСТРАЦИЯ HANDLERS
        # ========================================
        
        logger.info("Регистрация handlers...")
        
        # Устанавливаем сервисы для conversation handler
        setup_services(moderation_service, idea_generator, post_generator, api_client)
        logger.info("✓ Сервисы установлены для conversation handler")
        
        # Устанавливаем API клиент для voice handler
        setup_api_client(api_client)
        logger.info("✓ API клиент установлен для voice handler")
        
        # Регистрируем routers
        # Порядок важен! Сначала команды, потом голосовые, потом остальное
        dp.include_router(start_router)
        logger.info("✓ Start handler зарегистрирован")
        
        dp.include_router(voice_router)
        logger.info("✓ Voice handler зарегистрирован")
        
        dp.include_router(conversation_router)
        logger.info("✓ Conversation handler зарегистрирован")
        
        # ========================================
        # ЭТАП 7: ЗАПУСК БОТА
        # ========================================
        
        logger.info("=" * 80)
        logger.info("БОТ ГОТОВ К РАБОТЕ")
        logger.info("Ожидание сообщений...")
        logger.info("Нажмите Ctrl+C для остановки")
        logger.info("=" * 80)
        
        # Удаляем вебхук если был (на случай предыдущего использования webhook mode)
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Запускаем polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки (Ctrl+C)")
    
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        # ========================================
        # ЗАВЕРШЕНИЕ РАБОТЫ
        # ========================================
        
        logger.info("=" * 80)
        logger.info("ЗАВЕРШЕНИЕ РАБОТЫ БОТА")
        logger.info("=" * 80)
        
        # Закрываем API клиент
        if 'api_client' in locals():
            await api_client.close()
            logger.info("✓ API клиент закрыт")
        
        # Закрываем бота
        if 'bot' in locals():
            await bot.session.close()
            logger.info("✓ Bot session закрыт")
        
        logger.info("Бот остановлен")
        logger.info("=" * 80)


if __name__ == "__main__":
    """
    Точка входа в приложение
    
    Запускает главную асинхронную функцию.
    """
    try:
        # Запускаем main через asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот остановлен пользователем")
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)

