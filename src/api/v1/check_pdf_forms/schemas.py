from pathlib import Path

from pydantic import HttpUrl, BaseModel


class FileDataSchema(BaseModel):
    path: Path | str
    url: HttpUrl | str
    size: int = 0
    filename: str
    content_type: str
    status_code: int
    message: str
