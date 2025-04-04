from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Literal, List, Union

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


class FileSchemaForFolder(FileSchema):
    type: Literal["file"]


class FolderItem(FolderDataSchema):
    type: Literal["folder"]


class FolderContentsSchema(BaseModel):
    current_path: str
    items: List[Union[FileSchemaForFolder, FolderItem]]
