from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_user
from app.db.session import get_db_session
from app.repositories.user import UserRepository
from app.schemas.user import UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
async def list_users(_: object = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    users = await UserRepository(session).list_all()
    return [UserOut.model_validate(user) for user in users]


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int, _: object = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    user = await UserRepository(session).get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut.model_validate(user)
