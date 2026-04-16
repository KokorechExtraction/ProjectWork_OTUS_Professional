from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Post, PostLike


class PostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, author_id: int, text: str) -> Post:
        post = Post(author_id=author_id, text=text)
        self.session.add(post)
        await self.session.commit()
        await self.session.refresh(post)
        return post

    async def feed(self) -> list[Post]:
        result = await self.session.execute(select(Post).order_by(Post.created_at.desc()))
        return list(result.scalars().all())

    async def user_posts(self, user_id: int) -> list[Post]:
        result = await self.session.execute(select(Post).where(Post.author_id == user_id).order_by(Post.created_at.desc()))
        return list(result.scalars().all())

    async def get_by_id(self, post_id: int) -> Post | None:
        result = await self.session.execute(select(Post).where(Post.id == post_id))
        return result.scalar_one_or_none()

    async def has_like(self, post_id: int, user_id: int) -> bool:
        result = await self.session.execute(select(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == user_id))
        return result.scalar_one_or_none() is not None

    async def add_like(self, post_id: int, user_id: int) -> None:
        self.session.add(PostLike(post_id=post_id, user_id=user_id))
        await self.session.commit()

    async def remove_like(self, post_id: int, user_id: int) -> None:
        await self.session.execute(delete(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == user_id))
        await self.session.commit()

    async def likes_count(self, post_id: int) -> int:
        result = await self.session.execute(select(func.count(PostLike.id)).where(PostLike.post_id == post_id))
        return int(result.scalar_one())
