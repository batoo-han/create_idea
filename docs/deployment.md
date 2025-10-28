# 🚀 Руководство по развертыванию

Полное руководство по развертыванию Telegram бота для генерации контента.

## 📋 Содержание

- [Подготовка к развертыванию](#подготовка-к-развертыванию)
- [Docker развертывание](#docker-развертывание)
- [Локальное развертывание](#локальное-развертывание)
- [Production развертывание](#production-развертывание)
- [Обновление на production](#обновление-на-production)
- [Мониторинг и обслуживание](#мониторинг-и-обслуживание)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Подготовка к развертыванию

### Требования

#### Для Docker (рекомендуется)
- Docker Engine 20.10+
- Docker Compose 2.0+
- 1 GB свободного места
- Доступ к интернету

#### Для локального запуска
- Python 3.11+
- ffmpeg (для обработки аудио)
- 500 MB свободного места
- Доступ к интернету

### Получение API ключей

#### 1. Telegram Bot Token

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям:
   - Введите имя бота (например: "Content Ideas Generator")
   - Введите username бота (должен заканчиваться на `bot`, например: `my_content_bot`)
4. Скопируйте полученный токен

**Формат токена:** `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

#### 2. ProxyAPI Key

1. Зарегистрируйтесь на [proxyapi.ru](https://proxyapi.ru)
2. Пополните баланс:
   - Минимум 100₽ для тестирования
   - Рекомендуется 500₽+ для стабильной работы
3. Перейдите в раздел "API Keys"
4. Скопируйте ключ

**Формат ключа:** `sk-abcd1234efgh5678ijkl9012mnop3456`

**Стоимость использования (ориентировочно):**
- Генерация идей (GPT-4o-mini): ~0.5₽ за запрос
- Генерация поста (GPT-5): ~5-10₽ за пост
- Генерация изображения (DALL-E 3): ~15-20₽ за изображение
- Транскрибация голоса (Whisper): ~0.1₽ за минуту

---

## 🐳 Docker развертывание

### Установка Docker

#### Windows
1. Скачайте [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. Установите и запустите
3. Проверьте установку:
   ```powershell
   docker --version
   docker-compose --version
   ```

#### Linux (Ubuntu/Debian)
```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Проверка
docker --version
docker compose version
```

#### macOS
1. Скачайте [Docker Desktop для Mac](https://www.docker.com/products/docker-desktop)
2. Установите и запустите
3. Проверьте установку

### Развертывание через Docker

#### 1. Клонируйте репозиторий

```bash
git clone https://github.com/yourusername/telegram-content-bot.git
cd telegram-content-bot
```

#### 2. Создайте .env файл

```bash
# Linux/macOS
cp .env.example .env

# Windows PowerShell
Copy-Item .env.example .env
```

#### 3. Настройте .env

Откройте `.env` в текстовом редакторе и укажите:

```env
# ОБЯЗАТЕЛЬНЫЕ параметры
TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather
PROXYAPI_KEY=ваш_ключ_от_ProxyAPI

# РЕКОМЕНДУЕМЫЕ параметры (можно оставить по умолчанию)
MODEL_TEXT_GENERATION=gpt-4o-mini
MODEL_FINAL_POST=gpt-5-mini
MODEL_IMAGE_GENERATION=dall-e-3
MODEL_SPEECH_TO_TEXT=whisper-1

MAX_TOKENS_POST=3000
TEMPERATURE_POST=0.3
```

#### 4. Запустите бота

```bash
docker-compose up -d
```

**Флаги:**
- `-d` - запуск в фоновом режиме (detached)

**Вывод:**
```
Creating network "telegram-content-bot_default" with the default driver
Creating telegram_content_bot ... done
```

#### 5. Проверьте статус

```bash
# Статус контейнера
docker-compose ps

# Логи (последние 50 строк)
docker-compose logs --tail=50

# Логи в реальном времени
docker-compose logs -f

# Выход из просмотра логов: Ctrl+C
```

#### 6. Остановка бота

```bash
# Остановить (данные сохраняются)
docker-compose stop

# Остановить и удалить контейнер (данные сохраняются в volumes)
docker-compose down
```

### Использование deploy.sh

Скрипт для упрощенного управления:

```bash
# Сделать исполняемым (Linux/macOS)
chmod +x deploy.sh

# Запуск
./deploy.sh start

# Остановка
./deploy.sh stop

# Перезапуск
./deploy.sh restart

# Обновление (git pull + rebuild + restart)
./deploy.sh update

# Логи
./deploy.sh logs

# Статус
./deploy.sh status
```

---

## 🐍 Локальное развертывание

### 1. Установите Python 3.11+

Проверьте версию:
```bash
python --version
# или
python3 --version
```

Скачать: [python.org](https://www.python.org/downloads/)

### 2. Установите ffmpeg

#### Windows
1. Скачайте с [ffmpeg.org](https://ffmpeg.org/download.html)
2. Распакуйте и добавьте в PATH
3. Проверьте: `ffmpeg -version`

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

#### macOS
```bash
brew install ffmpeg
```

### 3. Клонируйте и настройте

```bash
# Клонирование
git clone https://github.com/yourusername/telegram-content-bot.git
cd telegram-content-bot

# Создание виртуального окружения
python -m venv .venv

# Активация
# Windows:
.venv\Scripts\activate

# Linux/macOS:
source .venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Настройка .env
cp .env.example .env
# Отредактируйте .env вашим редактором
```

### 4. Запустите бота

```bash
python src/main.py
```

**Успешный запуск:**
```
Инициализация логирования...
================================================================================
ЗАПУСК CONTENT IDEAS GENERATOR BOT
================================================================================
Проверка конфигурации...
✓ Конфигурация валидна
...
================================================================================
БОТ ГОТОВ К РАБОТЕ
Ожидание сообщений...
Нажмите Ctrl+C для остановки
================================================================================
```

### 5. Остановка

Нажмите `Ctrl+C` в терминале.

---

## 🏢 Production развертывание

### Рекомендации для production

1. **Используйте Docker** для изоляции и упрощения управления
2. **Настройте автозапуск** через systemd или supervisor
3. **Мониторинг логов** через централизованную систему (ELK, Graylog)
4. **Резервное копирование** .env файла
5. **Reverse proxy** (nginx) если используется webhook mode

### Развертывание на VPS/VDS

#### 1. Подключитесь к серверу

```bash
ssh user@your-server-ip
```

#### 2. Установите Docker (если не установлен)

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install docker-compose-plugin
```

#### 3. Клонируйте репозиторий

```bash
cd /opt
sudo git clone https://github.com/yourusername/telegram-content-bot.git
cd telegram-content-bot
```

#### 4. Настройте .env

```bash
sudo cp .env.example .env
sudo nano .env
# Укажите ваши ключи
# Сохраните: Ctrl+O, Enter, Ctrl+X
```

#### 5. Запустите

```bash
sudo docker-compose up -d
```

#### 6. Настройте автозапуск (systemd)

Создайте файл `/etc/systemd/system/telegram-bot.service`:

```ini
[Unit]
Description=Telegram Content Generator Bot
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/telegram-content-bot
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
Restart=always

[Install]
WantedBy=multi-user.target
```

Активируйте:
```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot.service
sudo systemctl start telegram-bot.service
```

Проверьте:
```bash
sudo systemctl status telegram-bot.service
```

---

## 🔄 Обновление на production

### Метод 1: Скрипт deploy.sh

```bash
cd /opt/telegram-content-bot
sudo ./deploy.sh update
```

Скрипт автоматически:
1. Получит изменения из git
2. Пересоберет Docker образ
3. Перезапустит контейнер

### Метод 2: Вручную

```bash
cd /opt/telegram-content-bot

# Получить изменения
sudo git pull origin main

# Пересобрать образ
sudo docker-compose build --no-cache

# Перезапустить
sudo docker-compose down
sudo docker-compose up -d

# Проверить логи
sudo docker-compose logs -f --tail=100
```

### Откат к предыдущей версии

```bash
# Посмотреть историю коммитов
git log --oneline

# Откатиться к предыдущему коммиту
git reset --hard <commit-hash>

# Пересобрать и перезапустить
docker-compose down
docker-compose up -d --build
```

---

## 📊 Мониторинг и обслуживание

### Просмотр логов

#### Docker
```bash
# Последние 100 строк
docker-compose logs --tail=100

# Реальное время
docker-compose logs -f

# Конкретный контейнер
docker-compose logs -f telegram-bot
```

#### Локальный запуск
```bash
# Linux/macOS
tail -f logs/bot.log

# Windows PowerShell
Get-Content logs\bot.log -Wait -Tail 50
```

### Проверка статуса

```bash
# Docker
docker-compose ps

# Systemd
sudo systemctl status telegram-bot.service

# Проверка доступности API
curl https://api.proxyapi.ru/health
```

### Ротация логов

Логи автоматически ротируются:
- Максимальный размер: 10 MB
- Количество файлов: 5
- Старые логи удаляются автоматически

### Резервное копирование

Важные файлы для бэкапа:
```bash
# .env файл (содержит ключи!)
cp .env .env.backup

# Логи (опционально)
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/

# Docker volumes (если используются для хранения данных)
docker run --rm -v telegram-content-bot_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/data_backup.tar.gz /data
```

---

## 🐛 Troubleshooting

### Бот не запускается

#### 1. Проверьте .env файл

```bash
# Убедитесь, что файл существует
ls -la .env

# Проверьте содержимое (без отображения секретов)
cat .env | grep -v "KEY\|TOKEN"
```

**Частые ошибки:**
- Отсутствие `.env` файла
- Пробелы в значениях
- Неправильный формат токенов

#### 2. Проверьте логи

```bash
docker-compose logs --tail=100
```

Ищите строки с `ERROR` или `CRITICAL`.

#### 3. Проверьте Docker

```bash
# Версия
docker --version

# Запущен ли демон
docker ps

# Образ существует
docker images | grep telegram
```

### Ошибка "Invalid token"

**Причина:** Неправильный `TELEGRAM_BOT_TOKEN`

**Решение:**
1. Получите новый токен от @BotFather
2. Обновите `.env`
3. Перезапустите: `docker-compose restart`

### Ошибка "Unauthorized" (ProxyAPI)

**Причины:**
- Неправильный API ключ
- Недостаточно средств на балансе
- Ключ деактивирован

**Решение:**
1. Проверьте баланс на proxyapi.ru
2. Проверьте статус ключа
3. Обновите `.env` если нужно

### Бот не отвечает на сообщения

**Проверки:**
1. Бот запущен: `docker-compose ps`
2. Нет ошибок в логах: `docker-compose logs`
3. Интернет доступен на сервере
4. ProxyAPI доступен: `curl https://api.proxyapi.ru/health`

### Высокое потребление ресурсов

**CPU:**
- Нормально: 5-15% при активности
- Высоко: 50%+ постоянно

**Память:**
- Нормально: 100-300 MB
- Высоко: 1 GB+

**Решение:**
1. Проверьте логи на циклические ошибки
2. Уменьшите `MAX_TOKENS_POST` в `.env`
3. Перезапустите бота

### Docker проблемы

#### "No space left on device"

```bash
# Очистка неиспользуемых образов
docker system prune -a

# Очистка volumes
docker volume prune
```

#### "Port already in use"

Если используете webhook mode и порт занят:
```bash
# Найти процесс
sudo netstat -tulpn | grep :8080

# Или изменить порт в docker-compose.yml
```

### Сетевые проблемы

#### Timeout при отправке фото

**Причины:**
- Медленное соединение
- Большой размер изображения
- Проблемы на стороне Telegram

**Решение:**
Бот автоматически делает 3 retry попытки. Если все неудачны, отправляется только текст.

#### ProxyAPI недоступен

```bash
# Проверка доступности
curl -I https://api.proxyapi.ru

# Проверка DNS
nslookup api.proxyapi.ru

# Проверка из контейнера
docker-compose exec telegram-bot ping -c 4 api.proxyapi.ru
```

---

## 📞 Поддержка

Если проблема не решена:

1. **Проверьте документацию:** [docs/](../docs/)
2. **Создайте Issue:** [GitHub Issues](https://github.com/yourusername/telegram-content-bot/issues)
3. **Предоставьте:**
   - Версию бота
   - Логи (без секретов!)
   - Описание проблемы
   - Шаги для воспроизведения

---

**Версия документа**: 1.0.0  
**Дата создания**: 28 октября 2025  
**Автор**: Development Team

