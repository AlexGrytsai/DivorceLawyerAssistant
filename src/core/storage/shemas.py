from datetime import datetime
from pathlib import Path
from typing import Optional, List, Union

from pydantic import HttpUrl, BaseModel


class FolderItem(BaseModel):
    name: str
    path: str
    type: str


class FileItem(FolderItem):
    size: int
    updated: Optional[str]


class FolderContents(BaseModel):
    current_path: str
    items: List[Union[FileItem, FolderItem]]


class FileDataSchema(BaseModel):
    path: Path | str
    url: HttpUrl | str
    size: Optional[int] = None
    filename: Optional[str] = None
    content_type: Optional[str] = None
    status_code: int = 200
    message: str = "File operation successful"
    date_created: str = datetime.now().isoformat()
    creator: str = "system"


class FolderDataSchema(BaseModel):
    path: Path | str
    name: str
    status_code: int = 200
    message: str = "Folder operation successful"
    date_created: Optional[str] = datetime.now().isoformat()
    creator: str = "system"
    parent_folder: Optional[Path | str] = None
    is_empty: bool = True


class FileDeleteSchema(BaseModel):
    file: Path | str
    message: str = "File deleted successfully"
    status_code: int = 200
    date_deleted: str = datetime.now().isoformat()
    deleted_by: str = "system"


class FolderDeleteSchema(BaseModel):
    folder: Path | str
    message: str = "Folder deleted successfully"
    status_code: int = 200
    date_deleted: str = datetime.now().isoformat()
    deleted_by: str = "system"
    deleted_files_count: int = 0
