from pathlib import Path

from pydantic import HttpUrl, BaseModel


class FileDataUpload(BaseModel):
    path: Path | str
    size: int = 0
    filename: str
    content_type: str
    status_code: int
    message: str


class CheckedForm(BaseModel):
    path: Path | str
    url: HttpUrl | str
    size: int = 0
    filename: str
    content_type: str
    status_code: int
    message: str
