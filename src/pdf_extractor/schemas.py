from typing import Dict, Any, List, Optional, Union, Tuple

import pymupdf as fitz  # type: ignore
from pydantic import BaseModel, model_validator
from pymupdf.table import Table  # type: ignore


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
    rect: fitz.Rect

    class Config:
        arbitrary_types_allowed = True


class TableParsed(BaseModel):
    table: List[List[List[fitz.Widget | SpanPDF]]]
    header: Optional[List[str]] = None
    table_str_rows: Optional[List[Tuple[str, ...]]] = None
    table_str_rows_for_ai: Optional[List[Tuple[str, ...]]] = None
    rect: fitz.Rect

    class Config:
        arbitrary_types_allowed = True


class PagePDF(BaseModel):
    page_number: Optional[int] = None
    lines: List[LinePDF]
    widgets: Optional[List[fitz.Widget]] = []
    scraped_tables: Optional[List[Table]] = []
    parsed_tables: Optional[List[TableParsed]] = []

    class Config:
        arbitrary_types_allowed = True


class DocumentPDF(BaseModel):
    pages: List[PagePDF]
