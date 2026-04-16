from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_user
from app.core.cache import (
    USER_LIST_CACHE_TTL_SECONDS,
    invalidate_all_wall_caches,
    invalidate_user_list_cache,
    user_list_cache_key,
)
from app.core.log_config import get_logger
from app.core.redis import redis_runtime
from app.db.session import get_db_session
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.mappers import to_user_out
from app.schemas.user import UpdateUserRequest, UserOut

router = APIRouter(prefix="/users", tags=["users"])
logger = get_logger(__name__)


@router.get("", response_model=list[UserOut])
async def list_users(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    q: str | None = Query(default=None, min_length=1, max_length=100),
) -> list[UserOut]:
    cache_key = user_list_cache_key(current_user.id, q)
    cached = await redis_runtime.get_json(cache_key)
    if isinstance(cached, list):
        logger.info("user_list_cache_hit", user_id=current_user.id, query=q)
        return [UserOut.model_validate(item) for item in cached]

    repo = UserRepository(session)
    if q:
        users = await repo.search(q.strip(), exclude_user_id=current_user.id)
        logger.info(
            "user_search", user_id=current_user.id, query=q.strip(), result_count=len(users)
        )
    else:
        users = await repo.list_all()
        logger.info("user_list_loaded", user_id=current_user.id, result_count=len(users))
    result = [to_user_out(user) for user in users]
    await redis_runtime.set_json(
        cache_key,
        [user.model_dump(mode="json") for user in result],
        USER_LIST_CACHE_TTL_SECONDS,
    )
    return result


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UpdateUserRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserOut:
    repo = UserRepository(session)

    existing_by_username = await repo.get_by_username(payload.username)
    if existing_by_username is not None and existing_by_username.id != current_user.id:
        logger.warning(
            "profile_update_username_taken", user_id=current_user.id, username=payload.username
        )
        raise HTTPException(status_code=400, detail="Username already taken")

    existing_by_email = await repo.get_by_email(payload.email)
    if existing_by_email is not None and existing_by_email.id != current_user.id:
        logger.warning("profile_update_email_taken", user_id=current_user.id, email=payload.email)
        raise HTTPException(status_code=400, detail="Email already registered")

    try:
        user = await repo.update(current_user, payload.username, payload.email)
    except IntegrityError as exc:
        await session.rollback()
        logger.warning("profile_update_integrity_error", user_id=current_user.id)
        raise HTTPException(status_code=400, detail="Username or email already exists") from exc

    logger.info("profile_updated", user_id=user.id, username=user.username, email=user.email)
    await invalidate_user_list_cache()
    await invalidate_all_wall_caches()
    return to_user_out(user)


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserOut:
    user = await UserRepository(session).get_by_id(user_id)
    if user is None:
        logger.warning("user_get_not_found", requester_id=current_user.id, user_id=user_id)
        raise HTTPException(status_code=404, detail="User not found")
    logger.info("user_loaded", user_id=user_id)
    return to_user_out(user)
