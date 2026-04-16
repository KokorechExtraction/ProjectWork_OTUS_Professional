from collections.abc import Iterable

from app.models.chat import Chat
from app.models.message import Message
from app.models.post import Post, PostComment
from app.models.user import User
from app.repositories.chat import ChatRepository
from app.repositories.user import UserRepository
from app.schemas.chat import AdminChatOut, ChatOut
from app.schemas.file import FileOut
from app.schemas.message import MessageOut
from app.schemas.post import PostCommentOut, PostOut
from app.schemas.user import UserBrief, UserOut


def to_user_brief(user: User | None) -> UserBrief | None:
    if user is None:
        return None
    return UserBrief.model_validate(user)


def to_user_out(user: User) -> UserOut:
    return UserOut.model_validate(user)


def to_message_out(message: Message, sender: User | None = None) -> MessageOut:
    attachments = [
        FileOut.model_validate(attachment.file)
        for attachment in getattr(message, "attachments", [])
        if getattr(attachment, "file", None) is not None
    ]
    return MessageOut(
        id=message.id,
        chat_id=message.chat_id,
        sender_id=message.sender_id,
        sender=to_user_brief(sender),
        text=message.text,
        attachments=attachments,
        status=message.status,
        created_at=message.created_at,
    )


def to_message_out_list(
    messages: Iterable[Message], sender_map: dict[int, User]
) -> list[MessageOut]:
    return [to_message_out(message, sender_map.get(message.sender_id)) for message in messages]


async def to_chat_out(
    chat: Chat,
    current_user_id: int,
    user_repo: UserRepository,
    chat_repo: ChatRepository,
) -> ChatOut:
    participant_ids = await chat_repo.list_participant_ids(chat.id)
    other_user = None
    for participant_id in participant_ids:
        if participant_id == current_user_id:
            continue
        user = await user_repo.get_by_id(participant_id)
        if user is not None:
            other_user = to_user_brief(user)
        break
    return ChatOut(id=chat.id, created_at=chat.created_at, other_user=other_user)


async def to_chat_out_list(
    chats: Iterable[Chat],
    current_user_id: int,
    user_repo: UserRepository,
    chat_repo: ChatRepository,
) -> list[ChatOut]:
    return [await to_chat_out(chat, current_user_id, user_repo, chat_repo) for chat in chats]


async def to_admin_chat_out(
    chat: Chat, user_repo: UserRepository, chat_repo: ChatRepository
) -> AdminChatOut:
    participant_ids = await chat_repo.list_participant_ids(chat.id)
    participants: list[UserBrief] = []
    for participant_id in participant_ids:
        user = await user_repo.get_by_id(participant_id)
        if user is not None:
            brief = to_user_brief(user)
            if brief is not None:
                participants.append(brief)
    return AdminChatOut(id=chat.id, created_at=chat.created_at, participants=participants)


async def to_admin_chat_out_list(
    chats: Iterable[Chat], user_repo: UserRepository, chat_repo: ChatRepository
) -> list[AdminChatOut]:
    return [await to_admin_chat_out(chat, user_repo, chat_repo) for chat in chats]


def to_post_comment_out(comment: PostComment) -> PostCommentOut:
    return PostCommentOut(
        id=comment.id,
        post_id=comment.post_id,
        author_id=comment.author_id,
        author=to_user_brief(comment.author),
        text=comment.text,
        created_at=comment.created_at,
    )


def to_post_out(post: Post, likes_count: int, liked_by_me: bool) -> PostOut:
    comments = [
        to_post_comment_out(comment)
        for comment in sorted(post.comments, key=lambda item: item.created_at)
    ]
    return PostOut(
        id=post.id,
        author_id=post.author_id,
        author=to_user_brief(post.author),
        text=post.text,
        created_at=post.created_at,
        likes_count=likes_count,
        liked_by_me=liked_by_me,
        comments_count=len(comments),
        comments=comments,
    )
