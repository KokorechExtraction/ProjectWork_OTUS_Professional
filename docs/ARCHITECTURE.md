# Архитектура проекта

## Высокоуровневая структура

Проект разделён на явные слои:

- `API` - HTTP- и WebSocket-эндпоинты
- `Services` - бизнес-правила и координация
- `Repositories` - доступ SQLAlchemy к базе данных
- `Models` - ORM-сущности
- `Schemas and mappers` - контракты запросов/ответов и преобразование моделей в API
- `WebSocket manager` - активные realtime-соединения и доставка событий чата
- `Core` - конфиг, логирование, Redis, хелперы кэша, безопасность

## Карта директорий

```text
app/
  api/
    deps/
    v1/
  core/
  db/
  models/
  repositories/
  schemas/
  services/
  static/
  templates/
  websocket/
alembic/
docs/
tests/
```

## Ответственность слоёв

### API Layer

Находится в `app/api/v1`.

Ответственность:

- принимать HTTP- и WebSocket-запросы
- получать зависимости FastAPI
- вызывать сервисы
- преобразовывать внутренние результаты в схемы `...Out`
- возвращать HTTP-ответы

Слой API не должен содержать логику SQLAlchemy-запросов или тяжёлые бизнес-правила.

### Service Layer

Находится в `app/services`.

Ответственность:

- обеспечивать выполнение бизнес-правил
- координировать несколько репозиториев
- запускать побочные эффекты, такие как Redis pub/sub и WebSocket-рассылки

Сервисы работают с внутренними моделями, а не со схемами ответов.

### Repository Layer

Находится в `app/repositories`.

Ответственность:

- инкапсулировать SQLAlchemy
- загружать и сохранять ORM-модели
- скрывать детали, такие как `select`, `join`, `selectinload`, `commit` и `refresh`

### Schemas and Mappers

Находится в `app/schemas`.

Ответственность:

- определять контракты запросов (`...Request`)
- определять контракты ответов (`...Out`)
- преобразовывать ORM-модели в структуры, готовые для API

Простое преобразование выполняется с помощью `model_validate(...)`. Более сложные payload собираются в [mappers.py](C:/Users/admin/PycharmProjects/ProjectWork_OTUS_Professional/app/schemas/mappers.py).

## Поток HTTP-запроса

Типичный путь:

1. клиент отправляет HTTP-запрос
2. маршрут FastAPI получает данные запроса
3. зависимости предоставляют текущего пользователя и сессию БД
4. маршрут вызывает сервис
5. сервис вызывает репозитории
6. репозитории читают или записывают ORM-модели
7. маршрут преобразует результат в `...Out`
8. клиент получает JSON-ответ

## WebSocket-поток

Realtime доступен через `/api/v1/ws`.

Путь подключения:

1. клиент открывает WebSocket и передаёт `token` в query string
2. сервер декодирует JWT
3. сервер загружает чаты пользователя через `AsyncSessionLocal`
4. `ConnectionManager` принимает WebSocket и сохраняет принадлежность к чатам
5. позже события чата отправляются правильным подключённым пользователям

## Redis в архитектуре

Redis имеет в системе две реальные роли.

### 1. Pub/Sub для событий чата

`ConnectionManager.broadcast_to_chat(...)` сначала публикует в Redis-канал `chat_events`.

Затем:

1. один экземпляр backend публикует событие
2. listener'ы во всех экземплярах backend читают Redis pub/sub-канал
3. каждый локальный менеджер перенаправляет событие своим собственным подключённым WebSocket-клиентам

Это убирает зависимость realtime от памяти одного процесса.

### 2. Cache

Redis также используется для кэширования:

- списка пользователей и результатов поиска
- стен пользователей

Когда исходные данные меняются, инвалидация кэша запускается через хелпер-функции в [cache.py](C:/Users/admin/PycharmProjects/ProjectWork_OTUS_Professional/app/core/cache.py).

## Конфигурация с несколькими экземплярами

[docker-compose.yml](C:/Users/admin/PycharmProjects/ProjectWork_OTUS_Professional/docker-compose.yml) запускает два экземпляра backend:

- `app` на `8000`
- `app2` на `8001`

Они разделяют:

- один контейнер PostgreSQL
- один контейнер Redis

Это предназначенная демонстрационная конфигурация для Redis-backed pub/sub между несколькими экземплярами приложения.

## Хранение данных и внешние сервисы

### PostgreSQL

Хранит постоянные данные:

- пользователей
- чаты
- участников чатов
- сообщения
- файлы
- посты
- комментарии
- лайки

### Redis

Обрабатывает временные/общие runtime-задачи:

- события чата
- записи кэша

## Слой представления

Фронтенд намеренно простой и не основан на отдельном SPA-фреймворке:

- [index.html](C:/Users/admin/PycharmProjects/ProjectWork_OTUS_Professional/app/templates/index.html)
- [app.js](C:/Users/admin/PycharmProjects/ProjectWork_OTUS_Professional/app/static/js/app.js)
- [app.css](C:/Users/admin/PycharmProjects/ProjectWork_OTUS_Professional/app/static/css/app.css)

UI действует как тонкий клиент:

- вызывает REST API-эндпоинты
- держит одно WebSocket-соединение для realtime
- рендерит чаты, стены и панель администратора

## Почему такой дизайн

- FastAPI хорошо подходит для асинхронного HTTP и WebSocket
- асинхронный SQLAlchemy даёт одну согласованную модель доступа к данным
- сервисы и репозитории уменьшают связанность
- схемы Pydantic определяют стабильный контракт API
- Redis решает и кэш, и доставку realtime между экземплярами
- Jinja2 вместе с Bootstrap сохраняет UI простым и поддерживаемым
