from typing import Dict, Any, List, Optional, Union

import fitz
from pydantic import BaseModel, model_validator
from pymupdf.table import Table


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
    text: List[Union[fitz.Widget, SpanPDF]]

    class Config:
        arbitrary_types_allowed = True


class PagePDF(BaseModel):
    page_number: Optional[int] = None
    lines: List[LinePDF]
    widgets: Optional[List[fitz.Widget]] = None
    tables: Optional[List[Table]] = None

    class Config:
        arbitrary_types_allowed = True


class DocumentPDF(BaseModel):
    pages: List[PagePDF]
