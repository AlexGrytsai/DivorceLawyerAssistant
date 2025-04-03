from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Union, Literal

from pydantic import HttpUrl, BaseModel, Field


class FileSchema(BaseModel):
    filename: str
    url: HttpUrl | str
    size: Optional[int] = None
    content_type: Optional[str] = None


class FileDeleteSchema(BaseModel):
    file: Path | str
    date_deleted: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class FileItem(BaseModel):
    name: str
    path: str
    type: Literal["file"]
    size: int
    updated: Optional[str]
    url: Optional[str] = None


class FolderItem(BaseModel):
    name: str
    path: str
    type: Literal["folder"]


class FolderContents(BaseModel):
    current_path: str
    items: List[Union[FileItem, FolderItem]]


class FolderBaseSchema(BaseModel):
    folder_name: str


class FolderDataSchema(FolderBaseSchema):
    folder_path: str
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class FolderRenameSchema(FolderBaseSchema):
    old_name: str
    folder_path: str


class FolderDeleteSchema(FolderBaseSchema):
    deleted_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
