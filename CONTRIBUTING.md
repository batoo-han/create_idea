# 🤝 Руководство по внесению вклада

Спасибо за интерес к улучшению проекта! Мы приветствуем любой вклад.

## 📋 Содержание

- [Процесс внесения изменений](#процесс-внесения-изменений)
- [Стиль кода](#стиль-кода)
- [Commit-сообщения](#commit-сообщения)
- [Pull Request](#pull-request)
- [Тестирование](#тестирование)

---

## 🔄 Процесс внесения изменений

### 1. Fork репозитория

Нажмите кнопку "Fork" в верхнем правом углу GitHub.

### 2. Клонируйте ваш fork

```bash
git clone https://github.com/ваш-username/telegram-content-bot.git
cd telegram-content-bot
```

### 3. Создайте feature branch

```bash
git checkout -b feature/ваша-фича
# или
git checkout -b fix/описание-багфикса
```

### 4. Внесите изменения

- Следуйте [стилю кода](#стиль-кода)
- Добавляйте комментарии на русском
- Обновляйте документацию

### 5. Закоммитьте изменения

```bash
git add .
git commit -m "feat: описание вашей фичи"
```

### 6. Запушьте в ваш fork

```bash
git push origin feature/ваша-фича
```

### 7. Создайте Pull Request

Откройте Pull Request из вашего fork в основной репозиторий.

---

## 🎨 Стиль кода

### Общие правила

- **Язык комментариев:** Русский
- **Максимальная длина строки:** 120 символов
- **Отступы:** 4 пробела (не табы)
- **Кодировка:** UTF-8

### Python Code Style

Следуйте PEP 8 с учетом специфики проекта:

#### ✅ Хорошо

```python
def generate_post_text(
    self,
    niche: str,
    goal: str,
    format_type: str,
    idea: Dict
) -> Dict:
    """
    Генерирует текст поста на основе выбранной идеи
    
    Args:
        niche: Ниша пользователя
        goal: Цель контента
        format_type: Формат поста
        idea: Данные выбранной идеи
        
    Returns:
        Dict с полями: title, content, hashtags, call_to_action
        
    Raises:
        GenerationError: При ошибке генерации
    """
    try:
        # Формируем промпт
        prompt = self.prompt_builder.build_post_prompt(
            niche=niche,
            goal=goal,
            format_type=format_type,
            idea=idea
        )
        
        # Генерируем текст
        response = await self.api_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model=self.settings.model_final_post,
            temperature=self.settings.temperature_post,
            max_tokens=self.settings.max_tokens_post,
            json_mode=True
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Ошибка генерации поста: {e}")
        raise GenerationError(f"Не удалось сгенерировать пост: {e}")
```

#### ❌ Плохо

```python
def gen_post(n,g,f,i):  # Неясные имена, нет docstring
    p=build_prompt(n,g,f,i)  # Короткие имена переменных
    r=api.call(p)  # Нет обработки ошибок
    return r  # Нет типов возврата
```

### Именование

- **Переменные и функции:** `snake_case`
- **Классы:** `PascalCase`
- **Константы:** `UPPER_SNAKE_CASE`
- **Приватные методы:** `_leading_underscore`

```python
# Переменные
user_id = 12345
post_content = "..."

# Функции
def generate_ideas(niche: str) -> List[Dict]:
    pass

# Классы
class IdeaGenerator:
    pass

# Константы
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# Приватные
def _internal_helper():
    pass
```

### Docstrings

Используйте Google Style с описанием на русском:

```python
def complex_function(param1: str, param2: int) -> Dict:
    """
    Краткое описание функции
    
    Более детальное описание того, что делает функция,
    если это необходимо.
    
    Args:
        param1: Описание первого параметра
        param2: Описание второго параметра
        
    Returns:
        Описание возвращаемого значения
        
    Raises:
        ValueError: Когда возникает эта ошибка
        TypeError: Когда возникает другая ошибка
        
    Example:
        >>> result = complex_function("test", 42)
        >>> print(result)
        {"status": "success"}
    """
```

### Комментарии

```python
# ✅ Хорошо: Объясняют ПОЧЕМУ, а не ЧТО
# Используем retry механизм, т.к. ProxyAPI иногда временно недоступен
for attempt in range(max_retries):
    try:
        return await api.call()
    except NetworkError:
        await asyncio.sleep(2)

# ❌ Плохо: Описывают очевидное
# Инкрементируем счетчик
counter += 1
```

### Type Hints

Всегда используйте type hints:

```python
from typing import List, Dict, Optional, Union

def process_data(
    items: List[str],
    config: Optional[Dict] = None
) -> Union[str, None]:
    """Обрабатывает данные"""
    pass
```

---

## 💬 Commit-сообщения

Используйте [Conventional Commits](https://www.conventionalcommits.org/):

### Формат

```
<тип>(<область>): краткое описание

[опционально: подробное описание]

[опционально: footer с issue номерами]
```

### Типы

- `feat`: Новая функциональность
- `fix`: Исправление бага
- `docs`: Изменения в документации
- `style`: Форматирование, не влияющее на код
- `refactor`: Рефакторинг без изменения функциональности
- `perf`: Улучшение производительности
- `test`: Добавление тестов
- `chore`: Обновление зависимостей, конфигов и т.д.

### Примеры

```bash
feat(bot): добавлена поддержка голосовых сообщений

fix(api): исправлена ошибка retry механизма при сетевых сбоях

docs(readme): обновлена инструкция по установке

refactor(services): упрощена логика генерации идей

perf(prompts): оптимизированы промпты для GPT-5
```

---

## 📤 Pull Request

### Checklist перед созданием PR

- [ ] Код следует стилю проекта
- [ ] Добавлены комментарии на русском
- [ ] Обновлена документация (если нужно)
- [ ] Нет конфликтов с main веткой
- [ ] Код протестирован локально
- [ ] Commit-сообщения следуют конвенции

### Шаблон PR

```markdown
## Описание

Краткое описание изменений и причин их внесения.

## Тип изменения

- [ ] Баг-фикс
- [ ] Новая функциональность
- [ ] Улучшение производительности
- [ ] Рефакторинг
- [ ] Документация

## Тестирование

Опишите как вы тестировали изменения:

- [ ] Локальный запуск
- [ ] Docker запуск
- [ ] Проверка всех сценариев использования

## Скриншоты (если применимо)

Добавьте скриншоты или видео демонстрации.

## Чеклист

- [ ] Код следует стилю проекта
- [ ] Добавлены комментарии
- [ ] Обновлена документация
- [ ] Нет linter ошибок
- [ ] Протестировано локально
```

---

## 🧪 Тестирование

### Перед отправкой PR

1. **Запустите бота локально:**
   ```bash
   python src/main.py
   ```

2. **Проверьте основные сценарии:**
   - `/start` команда работает
   - Генерация идей работает
   - Генерация поста работает
   - Голосовые сообщения работают

3. **Проверьте в Docker:**
   ```bash
   docker-compose up --build
   ```

4. **Проверьте логи на ошибки:**
   ```bash
   docker-compose logs
   ```

---

## 📝 Обновление документации

Если ваши изменения затрагивают:

- **Функциональность:** Обновите `docs/user_guide.md`
- **API или архитектуру:** Обновите `docs/architecture.md`
- **Промпты:** Обновите `docs/prompts_guide.md`
- **Установку:** Обновите `README.md` и `QUICKSTART.md`

---

## 🎯 Области для вклада

### Высокий приоритет

- 🐛 Исправление багов
- 📖 Улучшение документации
- 🌐 Интернационализация (i18n)
- 🧪 Добавление тестов

### Средний приоритет

- ⚡ Оптимизация производительности
- 🎨 Улучшение промптов
- 🔧 Новые конфигурационные опции

### Идеи для новых функций

- 📊 Аналитика использования
- 💾 Сохранение истории постов
- 🔄 Планирование публикаций
- 🎯 A/B тестирование промптов

---

## ❓ Вопросы?

- 💬 Создайте [Issue](https://github.com/yourusername/telegram-content-bot/issues)
- 📧 Напишите на email: your-email@example.com

---

**Спасибо за вклад в проект!** 🎉

