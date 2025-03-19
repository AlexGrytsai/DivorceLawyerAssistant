from pathlib import Path
from typing import Optional

from pydantic import HttpUrl, BaseModel


class FileDataSchema(BaseModel):
    path: Path | str
    url: HttpUrl | str
    size: Optional[int] = None
    filename: Optional[str] = None
    content_type: Optional[str] = None
    status_code: int
    message: str
    date_created: str
    creator: str


class FileDeleteSchema(BaseModel):
    file: Path | str
    message: str
    status_code: int
    date_deleted: str
    deleted_by: str
