# Architecture

## Overview

The application follows a layered architecture:

- API layer: FastAPI routes validate requests, map exceptions to HTTP responses, and serialize outputs.
- Service layer: orchestrates business rules such as chat creation, message delivery, file access, and post likes.
- Repository layer: isolates SQLAlchemy queries and persistence details.
- Model layer: defines the PostgreSQL schema through SQLAlchemy ORM models.
- Presentation layer: Jinja template plus Bootstrap and vanilla JavaScript for the browser UI.

## Request Flow

1. The browser or API client sends an HTTP request with a JWT bearer token.
2. `get_current_user` decodes the token and loads the current user from the database.
3. The route handler delegates work to a service class.
4. The service uses repositories for persistence and, where needed, the WebSocket manager for realtime fan-out.
5. A typed Pydantic schema is returned to the client.

## Realtime Flow

1. The client connects to `/api/v1/ws` with a JWT token.
2. The backend resolves the user and loads the chat ids available to that user.
3. The connection manager stores active sockets and the related chat membership in memory.
4. When a message is sent or read, the message service broadcasts a typed event to all users subscribed to that chat.

## Domain Model

### User

- owns uploaded files
- authors posts
- sends messages
- participates in chats through `chat_participants`

### Chat

- currently represents private conversations
- stores participants separately in `chat_participants`
- stores messages in `messages`

### Message

- belongs to one chat
- has one sender
- tracks a coarse delivery status
- can be linked to multiple uploaded files

### File

- belongs to an uploader
- may be linked to messages through `message_files`
- can be downloaded by the owner or a participant of the related chat

### Post

- belongs to an author
- can be liked by multiple users through `post_likes`

## Design Decisions

- SQLAlchemy async is used for consistency with FastAPI async endpoints.
- Repositories keep raw query logic out of services.
- Services provide a better seam for testing than route handlers.
- The UI is intentionally thin and communicates directly with JSON endpoints.
- WebSocket state is in memory, which is simple for local development but not horizontally scalable yet.
