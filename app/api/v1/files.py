from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_user
from app.core.log_config import get_logger
from app.db.session import get_db_session
from app.models.user import User
from app.repositories.file import FileRepository
from app.schemas.file import FileOut
from app.services.file import FileService

router = APIRouter(prefix="/files", tags=["files"])
logger = get_logger(__name__)


@router.post("/upload", response_model=FileOut)
async def upload_file(
    upload: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> FileOut:
    service = FileService(FileRepository(session))
    file = await service.upload_file(current_user.id, upload)
    logger.info(
        "file_uploaded",
        user_id=current_user.id,
        file_id=file.id,
        content_type=file.content_type,
        size=file.size,
    )
    return FileOut.model_validate(file)


@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    service = FileService(FileRepository(session))
    file = await service.get_file_for_user(file_id, current_user.id)
    if file is None:
        logger.warning("file_download_not_found", user_id=current_user.id, file_id=file_id)
        raise HTTPException(status_code=404, detail="File not found or unavailable")
    logger.info("file_downloaded", user_id=current_user.id, file_id=file.id)
    return FileResponse(
        path=Path(file.path), filename=file.original_name, media_type=file.content_type
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    service = FileService(FileRepository(session))
    try:
        await service.delete_unattached_file(file_id, current_user.id)
    except ValueError as exc:
        detail = str(exc)
        logger.warning(
            "file_delete_failed", user_id=current_user.id, file_id=file_id, detail=detail
        )
        if detail == "Attached files cannot be deleted":
            raise HTTPException(status_code=409, detail=detail) from exc
        raise HTTPException(status_code=404, detail=detail) from exc

    logger.info("file_deleted", user_id=current_user.id, file_id=file_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
