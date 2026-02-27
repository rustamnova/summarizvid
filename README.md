# Bot Template

Шаблон Telegram-бота. Используется как основа для быстрого создания новых ботов.

## Структура

```
bot-template.py   # Основной файл бота (переименовать по имени нового бота)
install.sh        # Установка с нуля
start.sh          # Запуск
stop.sh           # Остановка
restart.sh        # Перезапуск
requirements.txt  # Python-зависимости
.env              # Переменные окружения (заполнить перед установкой)
logs/
├── worklog.txt   # Рабочий лог (INFO+)
├── errors.txt    # Ошибки (ERROR+)
└── install.txt   # Лог установки
```

## Переменные окружения (`.env`)

| Переменная | Описание |
|---|---|
| `BOT_TOKEN` | Токен Telegram-бота (от @BotFather) |
| `XAI_API_KEY` / `GROK_API` | API-ключ xAI (Grok) |
| `XAI_MODEL` | Модель Grok, например `grok-4-latest` |
| `OPENAI_API_KEY` | API-ключ OpenAI для финальной редактуры текста |
| `OPENAI_MODEL` | Модель OpenAI, например `gpt-4o-mini` |
| `TRANSCRIPT_LANGS` | Предпочтительные языки субтитров через запятую (`ru,en`) |
| `MAX_COMMENTS` | Макс. комментариев для анализа (по умолчанию `80`) |
| `GITHUB_TOKEN` | GitHub Personal Access Token |
| `USER_IDS` | Разрешённые Telegram user ID через запятую |
| `REPO_URL` | URL репозитория нового бота |

Пример:

```env
BOT_TOKEN=...
XAI_API_KEY=...
XAI_MODEL=grok-4-latest
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
TRANSCRIPT_LANGS=ru,en
MAX_COMMENTS=80
USER_IDS=123456789
```

## Установка

```bash
bash install.sh
```

Скрипт запросит содержимое `.env`, клонирует репозиторий, установит зависимости и запустит бота.

## Управление

```bash
bash start.sh      # Запуск
bash stop.sh       # Остановка
bash restart.sh    # Перезапуск
screen -r BOTNAME  # Подключиться к сессии
```

## Использование бота

```text
/sum https://www.youtube.com/watch?v=VIDEO_ID
/sum https://www.tiktok.com/@user/video/VIDEO_ID
```

Также можно просто отправить ссылку YouTube/TikTok сообщением.

Бот вернет:
- читабельный суммариз видео (без таймкодов);
- отдельный блок по комментариям:
  - основная мысль комментариев;
  - важные комментарии;
  - популярные комментарии.

## Логи

| Файл | Что пишется |
|---|---|
| `logs/worklog.txt` | Запуск, остановка, вся рабочая активность (INFO+) |
| `logs/errors.txt` | Только ошибки (ERROR+) |
| `logs/install.txt` | Лог установки (только при установке) |

## Создание нового бота на основе шаблона

1. Создать новый репозиторий на GitHub
2. Скопировать содержимое шаблона
3. Переименовать `bot-template.py` → `<botname>.py`
4. Заполнить `.env`
5. Написать логику бота в `.py` файле
6. Запушить и запустить `bash install.sh`
