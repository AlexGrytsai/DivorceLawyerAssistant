from datetime import datetime
from pathlib import Path
from typing import Optional, List, Union, Literal

from pydantic import HttpUrl, BaseModel, Field


class BaseFileSchema(BaseModel):
    filename: Optional[str] = None
    url: HttpUrl | str
    size: Optional[int] = None
    content_type: Optional[str] = None


class BaseFolderSchema(BaseModel):
    path: Path | str
    name: str
    parent_folder: Optional[Path | str] = None
    is_empty: bool = True


class BaseDeleteSchema(BaseModel):
    date_deleted: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )
    deleted_by: str = "system"


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


class FileDataSchema(BaseFileSchema):
    pass


class FolderDataSchema(BaseFolderSchema):
    pass


class FileDeleteSchema(BaseDeleteSchema):
    file: Path | str


class FolderDeleteSchema(BaseDeleteSchema):
    folder: Path | str
    deleted_files_count: int = 0
