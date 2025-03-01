from typing import Dict, Any

import fitz
from pydantic import BaseModel, model_validator


class Span(BaseModel):
    text: str
    rect: fitz.Rect

    @model_validator(mode="before")
    def extract_rect(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        values["rect"] = fitz.Rect(values["bbox"])
        return values

    class Config:
        arbitrary_types_allowed = True
