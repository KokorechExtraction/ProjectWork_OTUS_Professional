from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_user
from app.db.session import get_db_session
from app.repositories.post import PostRepository
from app.schemas.post import CreatePostRequest, PostOut
from app.services.post import PostService

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("", response_model=PostOut)
async def create_post(payload: CreatePostRequest, current_user=Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    return await PostService(PostRepository(session)).create_post(current_user.id, payload.text)


@router.get("/feed", response_model=list[PostOut])
async def feed(current_user=Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    return await PostService(PostRepository(session)).feed(current_user.id)


@router.get("/user/{user_id}", response_model=list[PostOut])
async def user_posts(user_id: int, current_user=Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    return await PostService(PostRepository(session)).user_posts(current_user.id, user_id)


@router.post("/{post_id}/like", response_model=PostOut)
async def like_post(post_id: int, current_user=Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    try:
        return await PostService(PostRepository(session)).like_post(current_user.id, post_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{post_id}/like", response_model=PostOut)
async def unlike_post(post_id: int, current_user=Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    try:
        return await PostService(PostRepository(session)).unlike_post(current_user.id, post_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
