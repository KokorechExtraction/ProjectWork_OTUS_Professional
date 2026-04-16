# Async Messenger

`Async Messenger` is an async FastAPI-based messenger with a web UI, private chats, user walls, file attachments, admin tools, Redis pub/sub, and Redis cache.

## Features

- JWT registration and login
- private one-to-one chats
- realtime updates over WebSocket
- messages with file attachments
- read status for messages
- user walls instead of a global post feed
- likes and comments for posts
- edit and delete own messages and posts
- admin actions: ban/unban users, inspect user chats, moderate content
- Docker Compose setup
- Alembic migrations
- Redis cache and pub/sub

## Stack

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

## Architecture Summary

The project is split into clear layers:

- `app/api` - HTTP and WebSocket endpoints
- `app/services` - business logic
- `app/repositories` - SQLAlchemy queries
- `app/models` - ORM models
- `app/schemas` - Pydantic schemas and mappers
- `app/websocket` - realtime connection manager
- `app/core` - config, logging, Redis, security

Services return internal models. The API layer converts them into `...Out` response schemas.

## Redis Usage

Redis is used in two real tasks:

- `pub/sub` for chat events
  message events are published into Redis and can be delivered between multiple app instances
- caching
  the user list and user walls are cached in Redis

If Redis is unavailable, chat delivery falls back to local in-memory dispatch inside the current process.

## Docker Compose

[docker-compose.yml](C:/Users/admin/PycharmProjects/ProjectWork_OTUS_Professional/docker-compose.yml) starts:

- `app` on [http://127.0.0.1:8000](http://127.0.0.1:8000)
- `app2` on [http://127.0.0.1:8001](http://127.0.0.1:8001)
- `db` for PostgreSQL
- `redis` for Redis

This setup is useful for demonstrating multi-instance Redis pub/sub behavior.

## Quick Start

### 1. Prepare `.env`

Copy the template:

```bash
cp .env.example .env
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

Check these values:

- `JWT_SECRET_KEY`
- `DB_*`
- `REDIS_URL`
- `ADMIN_USERNAME`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`

The bootstrap admin user is created automatically on app startup.

### 2. Run with Docker

```bash
docker compose up --build
```

Available after startup:

- UI: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- second app instance: [http://127.0.0.1:8001/](http://127.0.0.1:8001/)

### 3. Run locally without Docker

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

## Main Scenarios

### Authentication

1. Register with `POST /api/v1/auth/register`
2. Login with `POST /api/v1/auth/login`
3. Receive a Bearer token
4. Use the token for HTTP and WebSocket access

### Chats

1. Create or reuse a private chat
2. Open the chat list
3. Send a message or a message with attachments
4. Receive realtime updates through `/api/v1/ws?token=<jwt>`

### User Walls

1. Open your own wall or another user's wall
2. Create a post
3. Edit or delete your own post
4. Comment and like posts

### Administration

Admins can:

- list users
- ban and unban users
- inspect chats for a specific user
- write into any chat and edit any message
- edit and delete any post

The admin panel is embedded into the main page UI and appears after admin login.

## API Groups

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

## Quality Status

Current state:

- `ruff format .` - passes
- `ruff check .` - passes
- `pytest -q -p no:cacheprovider` - `22 passed`

## Documentation

- [Architecture](C:/Users/admin/PycharmProjects/ProjectWork_OTUS_Professional/docs/ARCHITECTURE.md)
- [API and business rules](C:/Users/admin/PycharmProjects/ProjectWork_OTUS_Professional/docs/API.md)
