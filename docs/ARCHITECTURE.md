# Project Architecture

## High-Level Layout

The project is split into explicit layers:

- `API` - HTTP and WebSocket endpoints
- `Services` - business rules and coordination
- `Repositories` - SQLAlchemy access to the database
- `Models` - ORM entities
- `Schemas and mappers` - request/response contracts and model-to-API conversion
- `WebSocket manager` - active realtime connections and chat event delivery
- `Core` - config, logging, Redis, cache helpers, security

## Directory Map

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

## Layer Responsibilities

### API Layer

Located in `app/api/v1`.

Responsibilities:

- accept HTTP and WebSocket requests
- get FastAPI dependencies
- call services
- map internal results into `...Out` schemas
- return HTTP responses

The API layer should not keep SQLAlchemy query logic or heavy business rules.

### Service Layer

Located in `app/services`.

Responsibilities:

- enforce business rules
- coordinate multiple repositories
- trigger side effects such as Redis pub/sub and websocket broadcasts

Services work with internal models, not response schemas.

### Repository Layer

Located in `app/repositories`.

Responsibilities:

- encapsulate SQLAlchemy
- load and persist ORM models
- hide details such as `select`, `join`, `selectinload`, `commit`, and `refresh`

### Schemas and Mappers

Located in `app/schemas`.

Responsibilities:

- define request contracts (`...Request`)
- define response contracts (`...Out`)
- convert ORM models into API-ready structures

Simple mapping is done with `model_validate(...)`. More complex payloads are assembled in [mappers.py](C:/Users/admin/PycharmProjects/ProjectWork_OTUS_Professional/app/schemas/mappers.py).

## HTTP Request Flow

Typical path:

1. the client sends an HTTP request
2. a FastAPI route receives request data
3. dependencies provide the current user and DB session
4. the route calls a service
5. the service calls repositories
6. repositories read or write ORM models
7. the route maps the result into `...Out`
8. the client gets a JSON response

## WebSocket Flow

Realtime is exposed through `/api/v1/ws`.

Connection path:

1. the client opens a WebSocket and passes `token` in the query string
2. the server decodes JWT
3. the server loads the user's chats through `AsyncSessionLocal`
4. `ConnectionManager` accepts the websocket and stores chat membership
5. later chat events are dispatched to the correct connected users

## Redis in the Architecture

Redis has two real roles in the system.

### 1. Pub/Sub for Chat Events

`ConnectionManager.broadcast_to_chat(...)` first publishes into the Redis channel `chat_events`.

Then:

1. one backend instance publishes the event
2. listeners in all backend instances read the Redis pub/sub channel
3. each local manager forwards the event to its own connected websocket clients

This removes the realtime dependency on the memory of a single process.

### 2. Cache

Redis is also used to cache:

- the user list and search results
- user walls

When source data changes, cache invalidation is triggered through helper functions in [cache.py](C:/Users/admin/PycharmProjects/ProjectWork_OTUS_Professional/app/core/cache.py).

## Multi-Instance Setup

[docker-compose.yml](C:/Users/admin/PycharmProjects/ProjectWork_OTUS_Professional/docker-compose.yml) starts two backend instances:

- `app` on `8000`
- `app2` on `8001`

They share:

- one PostgreSQL container
- one Redis container

This is the intended demo setup for Redis-backed pub/sub across multiple app instances.

## Persistence and External Services

### PostgreSQL

Stores persistent data:

- users
- chats
- chat participants
- messages
- files
- posts
- comments
- likes

### Redis

Handles temporary/shared runtime concerns:

- chat events
- cache entries

## Presentation Layer

The frontend is intentionally simple and not based on a separate SPA framework:

- [index.html](C:/Users/admin/PycharmProjects/ProjectWork_OTUS_Professional/app/templates/index.html)
- [app.js](C:/Users/admin/PycharmProjects/ProjectWork_OTUS_Professional/app/static/js/app.js)
- [app.css](C:/Users/admin/PycharmProjects/ProjectWork_OTUS_Professional/app/static/css/app.css)

The UI acts as a thin client:

- it calls REST API endpoints
- it keeps one WebSocket connection for realtime
- it renders chats, walls, and the admin panel

## Why This Design

- FastAPI fits async HTTP and WebSocket well
- async SQLAlchemy provides one consistent data-access model
- services and repositories reduce coupling
- Pydantic schemas define a stable API contract
- Redis solves both cache and cross-instance realtime delivery
- Jinja2 plus Bootstrap keeps the UI simple and maintainable
