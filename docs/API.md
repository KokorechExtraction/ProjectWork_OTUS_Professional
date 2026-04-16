# API Notes

## Authentication

All protected HTTP endpoints require:

```text
Authorization: Bearer <token>
```

The WebSocket endpoint expects:

```text
/api/v1/ws?token=<token>
```

## Common Responses

- `400 Bad Request`: invalid business action such as sending an empty message
- `401 Unauthorized`: invalid or missing JWT
- `404 Not Found`: missing resource

## Important Business Rules

### Private chats

- a user cannot create a chat with themselves
- the second participant must exist
- an existing private chat is reused instead of duplicated

### Messages

- the sender must be a chat participant
- a message must contain text or at least one attachment
- attached files must belong to the current user

### Files

- files are uploaded first and then referenced by `file_ids`
- downloads are allowed for the uploader and for participants of the chat where the file was attached

### Posts

- likes are idempotent
- unlikes are idempotent
- feed items return both `likes_count` and `liked_by_me`
