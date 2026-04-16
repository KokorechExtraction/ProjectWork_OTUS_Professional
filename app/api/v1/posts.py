from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_user
from app.core.cache import (
    USER_WALL_CACHE_TTL_SECONDS,
    invalidate_wall_cache_for_user,
    user_wall_cache_key,
)
from app.core.redis import redis_runtime
from app.db.session import get_db_session
from app.models.post import Post
from app.models.user import User
from app.repositories.post import PostRepository
from app.schemas.mappers import to_post_comment_out, to_post_out
from app.schemas.post import (
    CreateCommentRequest,
    CreatePostRequest,
    PostCommentOut,
    PostOut,
    UpdatePostRequest,
)
from app.services.post import PostService

router = APIRouter(prefix="/posts", tags=["posts"])


async def build_post_out(
    post_repo: PostRepository,
    post_id: int,
    current_user_id: int,
    *,
    fallback: Post | None = None,
) -> PostOut:
    post = await post_repo.get_by_id(post_id)
    if post is None:
        if fallback is None:
            raise HTTPException(status_code=404, detail="Post not found")
        post = fallback
    likes_count = await post_repo.likes_count(post.id)
    liked_by_me = await post_repo.has_like(post.id, current_user_id)
    return to_post_out(post, likes_count=likes_count, liked_by_me=liked_by_me)


@router.post("", response_model=PostOut)
async def create_post(
    payload: CreatePostRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PostOut:
    post_repo = PostRepository(session)
    post = await PostService(post_repo).create_post(current_user.id, payload.text)
    await invalidate_wall_cache_for_user(current_user.id)
    return await build_post_out(post_repo, post.id, current_user.id, fallback=post)


@router.patch("/{post_id}", response_model=PostOut)
async def edit_post(
    post_id: int,
    payload: UpdatePostRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PostOut:
    post_repo = PostRepository(session)
    try:
        post = await PostService(post_repo).edit_post(
            current_user.id, post_id, payload.text, is_admin=current_user.is_admin
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await invalidate_wall_cache_for_user(post.author_id)
    return await build_post_out(post_repo, post.id, current_user.id, fallback=post)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    try:
        post_repo = PostRepository(session)
        post = await post_repo.get_by_id(post_id)
        if post is None:
            raise HTTPException(status_code=400, detail="Post not found")
        await PostService(post_repo).delete_post(
            current_user.id, post_id, is_admin=current_user.is_admin
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await invalidate_wall_cache_for_user(post.author_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/user/{user_id}", response_model=list[PostOut])
async def user_posts(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[PostOut]:
    cache_key = user_wall_cache_key(current_user.id, user_id)
    cached = await redis_runtime.get_json(cache_key)
    if isinstance(cached, list):
        return [PostOut.model_validate(item) for item in cached]

    post_repo = PostRepository(session)
    posts = await PostService(post_repo).user_posts(current_user.id, user_id)
    result: list[PostOut] = []
    for post in posts:
        result.append(await build_post_out(post_repo, post.id, current_user.id, fallback=post))
    await redis_runtime.set_json(
        cache_key,
        [post.model_dump(mode="json") for post in result],
        USER_WALL_CACHE_TTL_SECONDS,
    )
    return result


@router.post("/{post_id}/comments", response_model=PostCommentOut)
async def create_comment(
    post_id: int,
    payload: CreateCommentRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PostCommentOut:
    post_repo = PostRepository(session)
    try:
        comment = await PostService(post_repo).create_comment(
            current_user.id, post_id, payload.text
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    post = await post_repo.get_by_id(post_id)
    if post is not None:
        await invalidate_wall_cache_for_user(post.author_id)
    return to_post_comment_out(comment)


@router.post("/{post_id}/like", response_model=PostOut)
async def like_post(
    post_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PostOut:
    post_repo = PostRepository(session)
    try:
        post = await PostService(post_repo).like_post(current_user.id, post_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await invalidate_wall_cache_for_user(post.author_id)
    return await build_post_out(post_repo, post.id, current_user.id, fallback=post)


@router.delete("/{post_id}/like", response_model=PostOut)
async def unlike_post(
    post_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PostOut:
    post_repo = PostRepository(session)
    try:
        post = await PostService(post_repo).unlike_post(current_user.id, post_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await invalidate_wall_cache_for_user(post.author_id)
    return await build_post_out(post_repo, post.id, current_user.id, fallback=post)
