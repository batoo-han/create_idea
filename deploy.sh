#!/bin/bash

# Скрипт для развертывания и обновления бота на production
# Использование: ./deploy.sh [команда]
# Команды: start, stop, restart, update, logs

set -e  # Остановка при ошибке

COMPOSE_FILE="docker-compose.yml"
SERVICE_NAME="telegram-bot"

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функции
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Проверка наличия .env файла
check_env() {
    if [ ! -f ".env" ]; then
        print_error ".env файл не найден!"
        print_warning "Создайте .env файл на основе .env.example"
        exit 1
    fi
    print_success ".env файл найден"
}

# Запуск бота
start_bot() {
    print_success "Запуск бота..."
    check_env
    docker-compose up -d
    print_success "Бот запущен!"
    print_warning "Проверьте логи командой: ./deploy.sh logs"
}

# Остановка бота
stop_bot() {
    print_success "Остановка бота..."
    docker-compose down
    print_success "Бот остановлен!"
}

# Перезапуск бота
restart_bot() {
    print_success "Перезапуск бота..."
    docker-compose restart
    print_success "Бот перезапущен!"
}

# Обновление бота
update_bot() {
    print_success "Обновление бота..."
    
    # Получаем последние изменения
    print_success "Получение обновлений из git..."
    git pull origin main
    
    # Пересборка образа
    print_success "Пересборка Docker образа..."
    docker-compose build --no-cache
    
    # Перезапуск с новым образом
    print_success "Перезапуск контейнера..."
    docker-compose down
    docker-compose up -d
    
    print_success "Бот успешно обновлен!"
    print_warning "Проверьте логи командой: ./deploy.sh logs"
}

# Просмотр логов
show_logs() {
    docker-compose logs -f --tail=100 $SERVICE_NAME
}

# Статус бота
show_status() {
    docker-compose ps
}

# Главное меню
case "$1" in
    start)
        start_bot
        ;;
    stop)
        stop_bot
        ;;
    restart)
        restart_bot
        ;;
    update)
        update_bot
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|update|logs|status}"
        echo ""
        echo "Команды:"
        echo "  start   - Запустить бота"
        echo "  stop    - Остановить бота"
        echo "  restart - Перезапустить бота"
        echo "  update  - Обновить бота из git и пересобрать"
        echo "  logs    - Показать логи бота"
        echo "  status  - Показать статус контейнера"
        exit 1
        ;;
esac

exit 0

