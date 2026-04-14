# Фонотека — Веб-приложение для личной музыкальной коллекции

Многопользовательское веб-приложение для формирования, хранения и интеллектуального анализа личной музыкальной фонотеки с рекомендательной системой и ИИ-ассистентом на базе Claude API.

## Архитектура

```
┌─────────────┐    REST API    ┌─────────────────────┐
│  Vue 3 SPA  │ ──────────── ▶ │   FastAPI Backend    │
│  (Vite +    │                │   (Python 3.11)      │
│  Pinia +    │                │   Port 8000          │
│  Tailwind)  │                └──────────┬───────────┘
└─────────────┘                           │
                                    ┌─────┴──────┐
                              ┌─────┤ PostgreSQL  │
                              │     └────────────┘
                              │     ┌────────────┐
                              ├─────┤   Redis     │ (Celery broker)
                              │     └────────────┘
                              │     ┌────────────┐
                              └─────┤    MinIO    │ (Audio files)
                                    └────────────┘
                                          ▲
                                   ┌──────┴──────────┐
                                   │   ML Worker      │
                                   │ (Celery + librosa)│
                                   └──────────────────┘
```

## Быстрый старт

### 1. Клонировать / скопировать проект

```bash
cp .env.example .env
# Отредактируйте .env если нужно
```

### 2. Запустить все сервисы

```bash
docker compose up --build
```

Приложение будет доступно по адресу: **http://localhost**

API документация: **http://localhost:8000/docs**

### 3. Загрузить музыкальный датасет

**Вариант A — Jamendo API (реальные треки CC):**
```bash
# Зарегистрируйтесь на https://developer.jamendo.com/v3.0 и получите client_id
docker compose exec backend python /app/../scripts/load_dataset.py \
    --client-id YOUR_CLIENT_ID \
    --limit 200 \
    --no-upload      # использовать Jamendo URL напрямую (без загрузки в MinIO)
```

**Вариант B — демо-данные (без ключа):**
```bash
docker compose exec backend python /app/../scripts/seed_demo.py
```

### 4. Запустить извлечение аудиохарактеристик

```bash
docker compose exec backend python /app/../scripts/trigger_features.py
```

ML-воркер начнёт асинхронно обрабатывать треки. Прогресс можно отслеживать:
```bash
docker compose logs -f ml-worker
```

## Включить реальный ИИ-ассистент (Claude API)

1. Получите API ключ на https://console.anthropic.com/
2. Добавьте в `.env`:
   ```
   CLAUDE_API_KEY=sk-ant-...
   ```
3. Перезапустите: `docker compose restart backend`

По умолчанию используется **заглушка** (mock), которая корректно работает без ключа.

## Технологический стек

| Компонент       | Технология                        |
|-----------------|-----------------------------------|
| Фронтенд        | Vue 3, Pinia, Vue Router, Vite, Tailwind CSS |
| Бэкенд          | Python 3.11, FastAPI, SQLAlchemy 2, Alembic |
| ML-воркер       | Celery, librosa, scikit-learn, NumPy |
| База данных      | PostgreSQL 15                     |
| Очередь задач   | Redis 7                           |
| Файловый сервер  | MinIO                             |
| Контейнеризация | Docker, Docker Compose            |
| ИИ-ассистент    | Claude API (Anthropic)            |

## Структура проекта

```
phonoteka/
├── docker-compose.yml
├── .env.example
├── backend/                    # FastAPI main backend
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/             # SQLAlchemy ORM (17 таблиц)
│   │   ├── routers/            # REST API endpoints
│   │   ├── schemas/            # Pydantic schemas
│   │   └── services/           # Business logic + AI assistant
│   └── migrations/             # Alembic migrations
├── ml-worker/                  # Celery ML worker
│   └── app/
│       ├── ml/
│       │   ├── feature_extractor.py  # librosa pipeline
│       │   ├── similarity.py         # косинусное сходство MFCC
│       │   ├── ratings.py            # неявные оценки
│       │   └── recommender.py        # рекомендательная система
│       └── worker.py           # Celery tasks
├── frontend/                   # Vue 3 SPA
│   └── src/
│       ├── views/              # Страницы приложения
│       ├── components/         # UI компоненты
│       ├── stores/             # Pinia stores
│       └── api/                # API клиент
└── scripts/
    ├── load_dataset.py         # Загрузка Jamendo
    ├── seed_demo.py            # Демо-данные
    └── trigger_features.py    # Запуск ML-обработки
```

## База данных

17 таблиц PostgreSQL:
`users`, `artists`, `albums`, `genres`, `tracks`, `track_genres`, `track_features`, `track_similarities`, `user_library`, `playlists`, `playlist_tracks`, `play_events`, `implicit_ratings`, `user_artist_preferences`, `user_genre_preferences`, `recommendations`

## API Endpoints

- `POST /api/auth/register` — регистрация
- `POST /api/auth/login` — вход
- `GET /api/tracks` — каталог с поиском и фильтрацией
- `GET /api/library` — личная фонотека
- `POST /api/library/{track_id}` — добавить в фонотеку
- `POST /api/events` — записать событие прослушивания
- `GET /api/recommendations` — получить рекомендации
- `GET /api/playlists` — список плейлистов
- `POST /api/playlists/ai/create` — создать плейлист через ИИ
