from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        username: str,
        email: str,
        password_hash: str,
        *,
        is_admin: bool = False,
        is_active: bool = True,
    ) -> User:
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            is_admin=is_admin,
            is_active=is_active,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def update(self, user: User, username: str, email: str) -> User:
        user.username = username
        user.email = email
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_admin_state(
        self, user: User, *, is_admin: bool | None = None, is_active: bool | None = None
    ) -> User:
        if is_admin is not None:
            user.is_admin = is_admin
        if is_active is not None:
            user.is_active = is_active
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def upsert_admin(self, username: str, email: str, password_hash: str) -> User:
        user = await self.get_by_email(email)
        if user is None:
            user = await self.get_by_username(username)
        if user is None:
            return await self.create(
                username=username,
                email=email,
                password_hash=password_hash,
                is_admin=True,
                is_active=True,
            )
        user.username = username
        user.email = email
        user.password_hash = password_hash
        user.is_admin = True
        user.is_active = True
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def list_all(self) -> list[User]:
        result = await self.session.execute(select(User).order_by(User.id))
        return list(result.scalars().all())

    async def search(self, query: str, exclude_user_id: int | None = None) -> list[User]:
        statement = select(User).where(
            or_(
                User.username.ilike(f"%{query}%"),
                User.email.ilike(f"%{query}%"),
            )
        )
        if exclude_user_id is not None:
            statement = statement.where(User.id != exclude_user_id)
        result = await self.session.execute(statement.order_by(User.username.asc()).limit(20))
        return list(result.scalars().all())
