from app.core.config import settings
from app.core.log_config import get_logger
from app.core.security import hash_password
from app.models.chat import Chat
from app.models.user import User
from app.repositories.chat import ChatRepository
from app.repositories.post import PostRepository
from app.repositories.user import UserRepository

logger = get_logger(__name__)


class AdminService:
    def __init__(
        self, user_repo: UserRepository, post_repo: PostRepository, chat_repo: ChatRepository
    ) -> None:
        self.user_repo = user_repo
        self.post_repo = post_repo
        self.chat_repo = chat_repo

    async def list_users(self) -> list[User]:
        users = await self.user_repo.list_all()
        logger.info("admin_users_list_loaded", count=len(users))
        return users

    async def list_user_chats(self, user_id: int) -> list[Chat]:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise ValueError("User not found")
        chats = await self.chat_repo.list_user_chats(user_id)
        logger.info("admin_user_chats_list_loaded", user_id=user_id, count=len(chats))
        return chats

    async def ban_user(self, admin_user: User, target_user_id: int) -> User:
        if admin_user.id == target_user_id:
            raise ValueError("Admin cannot ban themselves")
        user = await self.user_repo.get_by_id(target_user_id)
        if user is None:
            raise ValueError("User not found")
        user = await self.user_repo.update_admin_state(user, is_active=False)
        logger.info("admin_user_banned", admin_user_id=admin_user.id, target_user_id=user.id)
        return user

    async def unban_user(self, admin_user: User, target_user_id: int) -> User:
        user = await self.user_repo.get_by_id(target_user_id)
        if user is None:
            raise ValueError("User not found")
        user = await self.user_repo.update_admin_state(user, is_active=True)
        logger.info("admin_user_unbanned", admin_user_id=admin_user.id, target_user_id=user.id)
        return user

    async def delete_post(self, admin_user: User, post_id: int) -> None:
        post = await self.post_repo.get_by_id(post_id)
        if post is None:
            raise ValueError("Post not found")
        await self.post_repo.delete_post(post)
        logger.info("admin_post_deleted", admin_user_id=admin_user.id, post_id=post_id)


async def ensure_admin_user(user_repo: UserRepository) -> None:
    if not settings.admin_username and not settings.admin_email and not settings.admin_password:
        return
    if not settings.admin_username or not settings.admin_email or not settings.admin_password:
        logger.warning("admin_bootstrap_skipped_incomplete_config")
        return
    password_hash = hash_password(settings.admin_password)
    user = await user_repo.upsert_admin(
        username=settings.admin_username,
        email=settings.admin_email,
        password_hash=password_hash,
    )
    logger.info("admin_bootstrap_ready", user_id=user.id, username=user.username)
