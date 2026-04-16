# Async Messenger

`Async Messenger` — это асинхронный мессенджер на базе FastAPI с веб-интерфейсом, приватными чатами, стенами пользователей, файловыми вложениями, инструментами администратора, Redis pub/sub и Redis-кэшем.

## Возможности

- регистрация и вход через JWT
- приватные чаты один на один
- обновления в реальном времени через WebSocket
- сообщения с файловыми вложениями
- статус прочтения для сообщений
- стены пользователей вместо глобальной ленты постов
- лайки и комментарии для постов
- редактирование и удаление собственных сообщений и постов
- действия администратора: бан/разбан пользователей, просмотр пользовательских чатов, модерация контента
- настройка Docker Compose
- миграции Alembic
- Redis-кэш и pub/sub

## Стек

- Python 3.13
- FastAPI
- SQLAlchemy 2.x
- PostgreSQL
- Redis
- Alembic
- Jinja2
- Bootstrap
- Pytest
- Ruff
- Mypy

## Краткое описание архитектуры

Проект разделён на чёткие слои:

- `app/api` - HTTP- и WebSocket-эндпоинты
- `app/services` - бизнес-логика
- `app/repositories` - запросы SQLAlchemy
- `app/models` - ORM-модели
- `app/schemas` - схемы Pydantic и мапперы
- `app/websocket` - менеджер realtime-соединений
- `app/core` - конфиг, логирование, Redis, безопасность

Сервисы возвращают внутренние модели. Слой API преобразует их в схемы ответа `...Out`.

## Использование Redis

Redis используется в двух реальных задачах:

- `pub/sub` для событий чата
  события сообщений публикуются в Redis и могут доставляться между несколькими экземплярами приложения
- кэширование
  список пользователей и стены пользователей кэшируются в Redis

Если Redis недоступен, доставка чата откатывается к локальной внутрипроцессной рассылке в памяти внутри текущего процесса.

## Docker Compose

[docker-compose.yml](C:/Users/admin/PycharmProjects/ProjectWork_OTUS_Professional/docker-compose.yml) запускает:

- `app` на [http://127.0.0.1:8000](http://127.0.0.1:8000)
- `app2` на [http://127.0.0.1:8001](http://127.0.0.1:8001)
- `db` для PostgreSQL
- `redis` для Redis

Эта настройка полезна для демонстрации поведения Redis pub/sub с несколькими экземплярами.

## Быстрый старт

### 1. Подготовьте `.env`

Скопируйте шаблон:

```bash
cp .env.example .env
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

Проверьте эти значения:

- `JWT_SECRET_KEY`
- `DB_*`
- `REDIS_URL`
- `ADMIN_USERNAME`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`

Bootstrap-пользователь администратора создаётся автоматически при запуске приложения.

### 2. Запуск с Docker

```bash
docker compose up --build
```

Доступно после запуска:

- UI: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- второй экземпляр приложения: [http://127.0.0.1:8001/](http://127.0.0.1:8001/)

### 3. Запуск локально без Docker

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

## Основные сценарии

### Аутентификация

1. Зарегистрируйтесь через `POST /api/v1/auth/register`
2. Войдите через `POST /api/v1/auth/login`
3. Получите Bearer-токен
4. Используйте токен для доступа по HTTP и WebSocket

### Чаты

1. Создайте или повторно используйте приватный чат
2. Откройте список чатов
3. Отправьте сообщение или сообщение с вложениями
4. Получайте обновления в реальном времени через `/api/v1/ws?token=<jwt>`

### Стены пользователей

1. Откройте свою собственную стену или стену другого пользователя
2. Создайте пост
3. Отредактируйте или удалите свой пост
4. Комментируйте посты и ставьте лайки

### Администрирование

Администраторы могут:

- просматривать список пользователей
- банить и разбанивать пользователей
- просматривать чаты конкретного пользователя
- писать в любой чат и редактировать любое сообщение
- редактировать и удалять любой пост

Панель администратора встроена в UI главной страницы и появляется после входа администратора.

## Группы API

### Auth

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

### Users

- `GET /api/v1/users`
- `PATCH /api/v1/users/me`
- `GET /api/v1/users/{user_id}`

### Chats and Messages

- `POST /api/v1/chats/private`
- `GET /api/v1/chats`
- `POST /api/v1/chats/{chat_id}/messages`
- `GET /api/v1/chats/{chat_id}/messages`
- `POST /api/v1/messages/{message_id}/read`
- `PATCH /api/v1/messages/{message_id}`
- `DELETE /api/v1/messages/{message_id}`

### Files

- `POST /api/v1/files/upload`
- `GET /api/v1/files/{file_id}/download`
- `DELETE /api/v1/files/{file_id}`

### Posts

- `POST /api/v1/posts`
- `PATCH /api/v1/posts/{post_id}`
- `DELETE /api/v1/posts/{post_id}`
- `GET /api/v1/posts/user/{user_id}`
- `POST /api/v1/posts/{post_id}/comments`
- `POST /api/v1/posts/{post_id}/like`
- `DELETE /api/v1/posts/{post_id}/like`

### Admin

- `GET /api/v1/admin/users`
- `GET /api/v1/admin/users/{user_id}/chats`
- `POST /api/v1/admin/users/{user_id}/ban`
- `POST /api/v1/admin/users/{user_id}/unban`
- `DELETE /api/v1/admin/posts/{post_id}`

### WebSocket

- `GET /api/v1/ws?token=<jwt>`

## Состояние качества

Текущее состояние:

- `ruff format .` - проходит
- `ruff check .` - проходит
- `pytest -q -p no:cacheprovider` - `22 passed`

## Документация

- [Architecture](C:/Users/admin/PycharmProjects/ProjectWork_OTUS_Professional/docs/ARCHITECTURE.md)
- [API and business rules](C:/Users/admin/PycharmProjects/ProjectWork_OTUS_Professional/docs/API.md)
