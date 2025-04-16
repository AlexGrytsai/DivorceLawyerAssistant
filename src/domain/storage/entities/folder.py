from datetime import datetime, timezone
from typing import Literal, Union, List, Optional

from pydantic import BaseModel, Field

from src.domain.storage.entities import FileForFolder


class Folder(BaseModel):
    folder_name: str


class FolderData(Folder):
    folder_path: str
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class FolderRename(Folder):
    old_name: str
    folder_path: str


class FolderDelete(Folder):
    deleted_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class FolderItem(FolderData):
    type: Literal["folder"]


class FolderContents(BaseModel):
    current_path: str
    items: List[Union[FileForFolder, FolderItem]]
