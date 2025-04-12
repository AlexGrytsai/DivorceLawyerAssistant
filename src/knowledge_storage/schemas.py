from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class KnowledgeSchema(BaseModel):
    name: str
    description: Optional[str] = None

    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
