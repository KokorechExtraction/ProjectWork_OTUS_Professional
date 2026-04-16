from sqlalchemy.exc import IntegrityError

from app.core.log_config import get_logger
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user import UserRepository

logger = get_logger(__name__)


class AuthService:
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def register(self, username: str, email: str, password: str) -> User:
        if await self.user_repo.get_by_username(username):
            logger.warning("register_failed_username_taken", username=username)
            raise ValueError("Username already taken")
        if await self.user_repo.get_by_email(email):
            logger.warning("register_failed_email_taken", email=email)
            raise ValueError("Email already registered")
        password_hash = hash_password(password)
        try:
            user = await self.user_repo.create(
                username=username, email=email, password_hash=password_hash
            )
        except IntegrityError as exc:
            await self.user_repo.session.rollback()
            logger.warning(
                "register_failed_integrity_error",
                username=username,
                email=email,
            )
            raise ValueError("Username or email already exists") from exc
        logger.info("user_registered", user_id=user.id, username=user.username)
        return user

    async def login(self, email: str, password: str) -> dict[str, object]:
        user = await self.user_repo.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            logger.warning("login_failed", email=email)
            raise ValueError("Invalid credentials")
        if not user.is_active:
            logger.warning("login_failed_inactive_user", user_id=user.id)
            raise ValueError("User is inactive")
        logger.info("login_succeeded", user_id=user.id)
        return create_access_token(user=user)
