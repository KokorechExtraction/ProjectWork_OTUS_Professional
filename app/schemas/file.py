from datetime import datetime

from app.schemas.base import ORMBase


class FileOut(ORMBase):
    id: int
    owner_id: int
    original_name: str
    content_type: str
    size: int
    created_at: datetime
