# API and Business Rules

## Authentication

Protected HTTP endpoints use:

```text
Authorization: Bearer <token>
```

WebSocket uses:

```text
/api/v1/ws?token=<jwt>
```

## Common Status Codes

- `400 Bad Request` - business error or invalid action
- `401 Unauthorized` - missing or invalid token
- `404 Not Found` - entity not found
- `409 Conflict` - state conflict, for example deleting an already attached file

## Endpoints

### Auth

- `POST /api/v1/auth/register` - register a user
- `POST /api/v1/auth/login` - login and receive JWT
- `GET /api/v1/auth/me` - current user

### Users

- `GET /api/v1/users` - list users or search by `q`
- `PATCH /api/v1/users/me` - update current username and email
- `GET /api/v1/users/{user_id}` - get a user by id

### Chats

- `POST /api/v1/chats/private` - create or reuse a private chat
- `GET /api/v1/chats` - list chats for current user

### Messages

- `POST /api/v1/chats/{chat_id}/messages` - send a message
- `GET /api/v1/chats/{chat_id}/messages` - get chat history
- `POST /api/v1/messages/{message_id}/read` - mark a message as read
- `PATCH /api/v1/messages/{message_id}` - edit a message
- `DELETE /api/v1/messages/{message_id}` - delete a message

### Files

- `POST /api/v1/files/upload` - upload a file
- `GET /api/v1/files/{file_id}/download` - download a file
- `DELETE /api/v1/files/{file_id}` - delete own unattached file

### Posts

- `POST /api/v1/posts` - create a post
- `PATCH /api/v1/posts/{post_id}` - edit a post
- `DELETE /api/v1/posts/{post_id}` - delete a post
- `GET /api/v1/posts/user/{user_id}` - get a user's wall
- `POST /api/v1/posts/{post_id}/comments` - add a comment
- `POST /api/v1/posts/{post_id}/like` - add like
- `DELETE /api/v1/posts/{post_id}/like` - remove like

### Admin

- `GET /api/v1/admin/users` - list users
- `GET /api/v1/admin/users/{user_id}/chats` - inspect chats for a specific user
- `POST /api/v1/admin/users/{user_id}/ban` - ban a user
- `POST /api/v1/admin/users/{user_id}/unban` - unban a user
- `DELETE /api/v1/admin/posts/{post_id}` - delete any post

### WebSocket

- `GET /api/v1/ws?token=<jwt>` - connect to the realtime channel

## Business Rules

### Registration and Login

- username and email must be unique
- the password is validated by the registration schema before persistence
- login returns an access token

### Users

- `/users` supports search through `q`
- the user list and search results are cached in Redis
- profile updates invalidate both user-list cache and wall cache

### Private Chats

- you cannot create a chat with yourself
- the other user must exist
- if a private chat already exists, it is reused instead of creating a duplicate

### Messages

- a regular user must belong to the chat
- an admin can read and write in any chat
- a message must contain text or at least one attachment
- attached files must belong to the current user
- the author can edit and delete their own message
- an admin can edit and delete any message

### Files

- files are uploaded first
- later `file_id` values can be passed in `file_ids` while sending a message
- a file can be downloaded by its owner or by a participant of the chat where it was sent
- only an unattached file owned by the current user can be deleted

### Posts and Walls

- there is no global post feed; the project is wall-based
- the author can edit and delete their own post
- an admin can edit and delete any post
- like and unlike are idempotent
- user walls are cached in Redis
- post, like, and comment changes invalidate the wall cache

### Comments

- a comment can be created only for an existing post
- after a new comment is created, the post author's wall cache is invalidated

### Admin

- admin endpoints require an admin user
- the bootstrap admin is created from `ADMIN_*` environment variables
- ban and unban also invalidate user-list and wall caches

## WebSocket Events

The realtime channel is used for message and read-status delivery.

In practice the chat layer uses events such as:

- `message:new`
- `message:read`
- `message:updated`
- `message:deleted`

The websocket endpoint also sends an `ack` response for incoming client messages on the connection channel itself.

## Redis and Cache Behavior

### Pub/Sub

- `broadcast_to_chat(...)` publishes the event into Redis first
- each app instance has a listener for the Redis channel
- the event is then forwarded into local websocket connections for the target chat

### Cache

Cached data includes:

- user list
- user search results
- user walls

Cache invalidation happens on:

- profile updates
- post create, edit, and delete
- new comments
- like and unlike
- user ban and unban
