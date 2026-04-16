from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi import UploadFile

from app.core.config import settings
from app.models.file import File
from app.repositories.file import FileRepository


class FileService:
    def __init__(self, file_repo: FileRepository) -> None:
        self.file_repo = file_repo

    async def upload_file(self, current_user_id: int, upload: UploadFile) -> File:
        media_root = Path(settings.media_root)
        media_root.mkdir(parents=True, exist_ok=True)

        suffix = Path(upload.filename or "file").suffix
        stored_name = f"{uuid4().hex}{suffix}"
        file_path = media_root / stored_name
        content = await upload.read()

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        return await self.file_repo.create(
            owner_id=current_user_id,
            original_name=upload.filename or stored_name,
            stored_name=stored_name,
            content_type=upload.content_type or "application/octet-stream",
            size=len(content),
            path=str(file_path),
        )

    async def get_file(self, file_id: int) -> File | None:
        return await self.file_repo.get_by_id(file_id)

    async def get_file_for_user(self, file_id: int, user_id: int) -> File | None:
        return await self.file_repo.get_accessible_by_user(file_id, user_id)
