# Фонотека — Веб-приложение для личной музыкальной коллекции

Многопользовательское веб-приложение для формирования, хранения и интеллектуального анализа личной музыкальной фонотеки с рекомендательной системой и ИИ-ассистентом на базе Groq API.

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
| ИИ-ассистент    | Groq API (Anthropic)            |

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
