from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.repositories.file import FileRepository
from app.schemas.file import FileOut
from app.services.file import FileService

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=FileOut)
async def upload_file(
    upload: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> FileOut:
    service = FileService(FileRepository(session))
    file = await service.upload_file(current_user.id, upload)
    return FileOut.model_validate(file)


@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = FileService(FileRepository(session))
    file = await service.get_file_for_user(file_id, current_user.id)
    if file is None:
        raise HTTPException(status_code=404, detail="File not found or unavailable")
    return FileResponse(path=Path(file.path), filename=file.original_name, media_type=file.content_type)
