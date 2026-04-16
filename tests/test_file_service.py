from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services.file import FileService


@pytest.mark.asyncio
async def test_delete_unattached_file_removes_disk_file_and_db_record() -> None:
    temp_dir = Path.cwd() / ".tmp_test_files"
    temp_dir.mkdir(exist_ok=True)
    stored = temp_dir / f"{uuid4().hex}.txt"
    stored.write_text("hello", encoding="utf-8")
    file = SimpleNamespace(id=1, owner_id=5, path=str(stored))

    file_repo = AsyncMock()
    file_repo.get_by_id_owned_by_user.return_value = file
    file_repo.is_attached_to_message.return_value = False

    service = FileService(file_repo)

    await service.delete_unattached_file(1, 5)

    assert not stored.exists()
    file_repo.delete.assert_awaited_once_with(file)
    temp_dir.rmdir()


@pytest.mark.asyncio
async def test_delete_unattached_file_rejects_attached_file() -> None:
    file_repo = AsyncMock()
    file_repo.get_by_id_owned_by_user.return_value = SimpleNamespace(
        id=1, owner_id=5, path="unused"
    )
    file_repo.is_attached_to_message.return_value = True

    service = FileService(file_repo)

    with pytest.raises(ValueError, match="Attached files"):
        await service.delete_unattached_file(1, 5)

    file_repo.delete.assert_not_called()
