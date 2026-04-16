from app.core.log_config import get_logger
from app.models.post import Post, PostComment
from app.repositories.post import PostRepository

logger = get_logger(__name__)


class PostService:
    def __init__(self, post_repo: PostRepository) -> None:
        self.post_repo = post_repo

    async def create_post(self, current_user_id: int, text: str) -> Post:
        post = await self.post_repo.create(author_id=current_user_id, text=text)
        logger.info("post_created", post_id=post.id, author_id=current_user_id)
        return post

    async def user_posts(self, current_user_id: int, user_id: int) -> list[Post]:
        posts = await self.post_repo.user_posts(user_id)
        logger.info(
            "user_posts_loaded", viewer_id=current_user_id, user_id=user_id, count=len(posts)
        )
        return posts

    async def create_comment(self, current_user_id: int, post_id: int, text: str) -> PostComment:
        post = await self.post_repo.get_by_id(post_id)
        if post is None:
            logger.warning(
                "comment_create_post_not_found", user_id=current_user_id, post_id=post_id
            )
            raise ValueError("Post not found")
        comment = await self.post_repo.create_comment(
            post_id=post_id, author_id=current_user_id, text=text
        )
        logger.info(
            "comment_created", comment_id=comment.id, post_id=post_id, author_id=current_user_id
        )
        return comment

    async def like_post(self, current_user_id: int, post_id: int) -> Post:
        post = await self.post_repo.get_by_id(post_id)
        if post is None:
            logger.warning("post_like_not_found", user_id=current_user_id, post_id=post_id)
            raise ValueError("Post not found")
        if not await self.post_repo.has_like(post_id, current_user_id):
            await self.post_repo.add_like(post_id, current_user_id)
        post = await self.post_repo.get_by_id(post_id) or post
        likes_count = await self.post_repo.likes_count(post_id)
        logger.info("post_liked", post_id=post_id, user_id=current_user_id, likes_count=likes_count)
        return post

    async def unlike_post(self, current_user_id: int, post_id: int) -> Post:
        post = await self.post_repo.get_by_id(post_id)
        if post is None:
            logger.warning("post_unlike_not_found", user_id=current_user_id, post_id=post_id)
            raise ValueError("Post not found")
        if await self.post_repo.has_like(post_id, current_user_id):
            await self.post_repo.remove_like(post_id, current_user_id)
        post = await self.post_repo.get_by_id(post_id) or post
        likes_count = await self.post_repo.likes_count(post_id)
        logger.info(
            "post_unliked", post_id=post_id, user_id=current_user_id, likes_count=likes_count
        )
        return post

    async def edit_post(
        self, current_user_id: int, post_id: int, text: str, *, is_admin: bool = False
    ) -> Post:
        post = await self.post_repo.get_by_id(post_id)
        if post is None:
            logger.warning("post_edit_not_found", user_id=current_user_id, post_id=post_id)
            raise ValueError("Post not found")
        if not is_admin and post.author_id != current_user_id:
            logger.warning("post_edit_forbidden", user_id=current_user_id, post_id=post_id)
            raise ValueError("User cannot edit this post")
        normalized_text = text.strip()
        if not normalized_text:
            logger.warning("post_edit_empty", user_id=current_user_id, post_id=post_id)
            raise ValueError("Post text cannot be empty")
        post = await self.post_repo.update_text(post, normalized_text)
        logger.info("post_edited", post_id=post.id, editor_id=current_user_id, is_admin=is_admin)
        return post

    async def delete_post(
        self, current_user_id: int, post_id: int, *, is_admin: bool = False
    ) -> None:
        post = await self.post_repo.get_by_id(post_id)
        if post is None:
            logger.warning("post_delete_not_found", user_id=current_user_id, post_id=post_id)
            raise ValueError("Post not found")
        if not is_admin and post.author_id != current_user_id:
            logger.warning("post_delete_forbidden", user_id=current_user_id, post_id=post_id)
            raise ValueError("User cannot delete this post")
        await self.post_repo.delete_post(post)
        logger.info("post_deleted", post_id=post_id, deleter_id=current_user_id, is_admin=is_admin)
