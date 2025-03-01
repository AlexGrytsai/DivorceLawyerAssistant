from typing import Dict, Any, List, Optional

import fitz
from pydantic import BaseModel, model_validator


class SpanPDF(BaseModel):
    text: str
    rect: fitz.Rect

    @model_validator(mode="before")
    def extract_rect(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        values["rect"] = fitz.Rect(values["bbox"])
        return values

    class Config:
        arbitrary_types_allowed = True


class LinePDF(BaseModel):
    spans: List[SpanPDF]


class PagePDF(BaseModel):
    page_number: Optional[int] = None
    lines: List[LinePDF]
    widgets: Optional[List[fitz.Widget]] = None

    class Config:
        arbitrary_types_allowed = True


class DocumentPDF(BaseModel):
    pages: List[PagePDF]
