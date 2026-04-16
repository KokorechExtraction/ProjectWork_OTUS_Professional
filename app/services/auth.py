from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user import UserRepository


class AuthService:
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def register(self, username: str, email: str, password: str) -> User:
        password_hash = hash_password(password)
        return await self.user_repo.create(username=username, email=email, password_hash=password_hash)

    async def login(self, email: str, password: str) -> str:
        user = await self.user_repo.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")
        return create_access_token(str(user.id))
