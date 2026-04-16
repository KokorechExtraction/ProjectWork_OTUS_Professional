from app.repositories.post import PostRepository
from app.schemas.post import PostOut


class PostService:
    def __init__(self, post_repo: PostRepository) -> None:
        self.post_repo = post_repo

    async def create_post(self, current_user_id: int, text: str) -> PostOut:
        post = await self.post_repo.create(author_id=current_user_id, text=text)
        return PostOut(id=post.id, author_id=post.author_id, text=post.text, created_at=post.created_at, likes_count=0, liked_by_me=False)

    async def feed(self, current_user_id: int) -> list[PostOut]:
        posts = await self.post_repo.feed()
        result: list[PostOut] = []
        for post in posts:
            likes_count = await self.post_repo.likes_count(post.id)
            liked = await self.post_repo.has_like(post.id, current_user_id)
            result.append(PostOut(id=post.id, author_id=post.author_id, text=post.text, created_at=post.created_at, likes_count=likes_count, liked_by_me=liked))
        return result

    async def user_posts(self, current_user_id: int, user_id: int) -> list[PostOut]:
        posts = await self.post_repo.user_posts(user_id)
        result: list[PostOut] = []
        for post in posts:
            likes_count = await self.post_repo.likes_count(post.id)
            liked = await self.post_repo.has_like(post.id, current_user_id)
            result.append(PostOut(id=post.id, author_id=post.author_id, text=post.text, created_at=post.created_at, likes_count=likes_count, liked_by_me=liked))
        return result

    async def like_post(self, current_user_id: int, post_id: int) -> PostOut:
        post = await self.post_repo.get_by_id(post_id)
        if post is None:
            raise ValueError("Post not found")
        if not await self.post_repo.has_like(post_id, current_user_id):
            await self.post_repo.add_like(post_id, current_user_id)
        likes_count = await self.post_repo.likes_count(post_id)
        return PostOut(id=post.id, author_id=post.author_id, text=post.text, created_at=post.created_at, likes_count=likes_count, liked_by_me=True)

    async def unlike_post(self, current_user_id: int, post_id: int) -> PostOut:
        post = await self.post_repo.get_by_id(post_id)
        if post is None:
            raise ValueError("Post not found")
        if await self.post_repo.has_like(post_id, current_user_id):
            await self.post_repo.remove_like(post_id, current_user_id)
        likes_count = await self.post_repo.likes_count(post_id)
        return PostOut(id=post.id, author_id=post.author_id, text=post.text, created_at=post.created_at, likes_count=likes_count, liked_by_me=False)
