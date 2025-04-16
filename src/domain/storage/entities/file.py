from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field


class File(BaseModel):
    filename: str
    path: str
    url: str
    size: Optional[int] = None
    content_type: Optional[str] = None


class FileDelete(BaseModel):
    file: Path | str
    date_deleted: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class FileForFolder(File):
    type: Literal["file"]
