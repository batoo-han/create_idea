# ⚡ Быстрый старт

Запустите Telegram-бота для генерации контента за 5 минут!

## 🎯 Что вам понадобится

- **Docker** и **Docker Compose** (рекомендуемый способ)  
  ИЛИ
- **Python 3.11+** и **ffmpeg** (для локального запуска)
- **Telegram Bot Token** от [@BotFather](https://t.me/BotFather)
- **ProxyAPI Key** от [proxyapi.ru](https://proxyapi.ru)

---

## 🐳 Способ 1: Docker (рекомендуется)

### Шаг 1: Клонируйте репозиторий

```bash
git clone https://github.com/yourusername/telegram-content-bot.git
cd telegram-content-bot
```

### Шаг 2: Создайте .env файл

```bash
cp .env.example .env
```

### Шаг 3: Настройте ключи

Откройте `.env` в текстовом редакторе и укажите:

```env
# Обязательные параметры
TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather
PROXYAPI_KEY=ваш_ключ_от_ProxyAPI
```

### Шаг 4: Запустите бота

```bash
docker-compose up -d
```

### Шаг 5: Проверьте работу

```bash
# Смотрим логи
docker-compose logs -f

# Проверяем статус
docker-compose ps
```

✅ **Готово!** Бот работает. Откройте Telegram и напишите боту `/start`

---

## 🐍 Способ 2: Локальный запуск (Python)

### Шаг 1: Клонируйте и создайте venv

```bash
git clone https://github.com/batoo-han/create_idea.git
cd create_idea

# Создайте виртуальное окружение
python -m venv .venv

# Активируйте его
# Windows:
.venv\Scripts\activate

# Linux/Mac:
source .venv/bin/activate
```

### Шаг 2: Установите зависимости

```bash
pip install -r requirements.txt
```

### Шаг 3: Настройте .env

```bash
cp .env.example .env
# Отредактируйте .env и укажите ваши ключи
```

### Шаг 4: Запустите бота

```bash
python src/main.py
```

✅ **Готово!** Бот работает локально.

---

## 🔑 Получение ключей

### Telegram Bot Token

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям (имя и username бота)
4. Скопируйте полученный токен

**Пример токена:**
```
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### ProxyAPI Key

1. Зарегистрируйтесь на [proxyapi.ru](https://proxyapi.ru)
2. Пополните баланс (от 500₽ для начала)
3. Скопируйте API ключ из личного кабинета

**Пример ключа:**
```
sk-abcd1234efgh5678ijkl9012mnop3456
```

---

## 🎬 Первый запуск

После запуска бота:

1. Найдите вашего бота в Telegram по username
2. Отправьте `/start`
3. Следуйте инструкциям бота:
   - Укажите нишу (например: "фитнес")
   - Укажите цель (например: "привлечь подписчиков")
   - Укажите формат (например: "пост для Instagram")
4. Выберите одну из 5 сгенерированных идей
5. Укажите, нужна ли иллюстрация
6. Получите готовый пост с изображением!

---

## 🛠️ Полезные команды

### Docker

```bash
# Запуск
docker-compose up -d

# Остановка
docker-compose down

# Перезапуск
docker-compose restart

# Логи (последние 100 строк)
docker-compose logs -f --tail=100

# Обновление после изменений
docker-compose down
docker-compose up -d --build
```

### Локальный запуск

```bash
# Запуск
python src/main.py

# Остановка
Ctrl+C

# Просмотр логов
tail -f logs/bot.log

# Windows
Get-Content logs\bot.log -Wait -Tail 50
```

---

## ⚙️ Основные настройки

В `.env` файле вы можете настроить:

### Модели

```env
# Для идей и модерации (быстрая и дешевая)
MODEL_TEXT_GENERATION=gpt-4o-mini

# Для финального поста (более качественная)
MODEL_FINAL_POST=gpt-5-mini

# Для изображений
MODEL_IMAGE_GENERATION=dall-e-3
```

### Параметры

```env
# Максимум токенов для поста
MAX_TOKENS_POST=3000

# Креативность (0.0 - 2.0)
TEMPERATURE_IDEAS=0.7
TEMPERATURE_POST=0.3
```

---

## 🐛 Решение проблем

### Бот не запускается

1. **Проверьте .env файл:**
   ```bash
   cat .env  # Linux/Mac
   type .env  # Windows
   ```

2. **Проверьте токены:**
   - Telegram token должен начинаться с цифр
   - ProxyAPI key должен начинаться с `sk-`

3. **Проверьте логи:**
   ```bash
   docker-compose logs  # Docker
   cat logs/bot.log     # Локальный запуск
   ```

### Ошибка "Invalid token"

- Проверьте `TELEGRAM_BOT_TOKEN` в `.env`
- Убедитесь, что нет лишних пробелов
- Получите новый токен от @BotFather

### Ошибка "Unauthorized" (ProxyAPI)

- Проверьте `PROXYAPI_KEY` в `.env`
- Проверьте баланс на proxyapi.ru
- Убедитесь, что ключ активен

### Бот не отвечает

- Проверьте, что бот запущен: `docker-compose ps`
- Проверьте логи на ошибки
- Попробуйте перезапустить: `docker-compose restart`

---

## 📚 Дальнейшие шаги

После успешного запуска:

1. 📖 Прочитайте [полную документацию](docs/)
2. ⚙️ Настройте [параметры бота](.env.example)
3. 🎨 Изучите [систему промптов](docs/prompts_guide.md)
4. 🚀 Настройте [деплой на production](README.md#-развертывание-на-production)

---

## 🆘 Нужна помощь?

- 📖 [Полная документация](README.md)
- 💬 [GitHub Issues](https://github.com/batoohan/create_idea/issues)
- 📧 Email: your-email@example.com

---

**Время запуска:** ~5 минут  
**Сложность:** Легко 🟢

Удачи! 🚀
