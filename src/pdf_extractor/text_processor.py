from abc import ABC, abstractmethod
from typing import Optional, List

import pymupdf as fitz

from src.pdf_extractor.geometry_utils import GeometryUtils
from src.pdf_extractor.parser_pdf import LineType
from src.pdf_extractor.schemas import PagePDF, LinePDF, SpanPDF


class TextBaseProcessor(ABC):
    def __init__(self, geometry_utils: GeometryUtils) -> None:
        self._geometry_utils = geometry_utils

    @abstractmethod
    def group_text_on_page(
        self, spans_from_page: LineType, page_number: Optional[int] = None
    ) -> PagePDF | None:
        pass

    @staticmethod
    @abstractmethod
    def remove_text_duplicates(page: PagePDF) -> None:
        pass


class TextProcessor(TextBaseProcessor):
    def group_text_on_page(
        self, spans_from_page: LineType, page_number: Optional[int] = None
    ) -> PagePDF | None:
        if not spans_from_page:
            return None

        groups_spans_on_page: List[LinePDF] = []
        spans_on_same_line: List[SpanPDF] = []
        line_rect: fitz.Rect = fitz.Rect(spans_from_page[0].get("bbox"))

        for raw_span in spans_from_page:
            span = SpanPDF(**raw_span)
            if self._geometry_utils.is_same_line(line_rect, span.rect):
                spans_on_same_line.append(span)
            else:
                groups_spans_on_page.append(
                    LinePDF(text=spans_on_same_line, rect=line_rect)
                )
                spans_on_same_line = [span]
                line_rect = span.rect

        if spans_on_same_line:
            groups_spans_on_page.append(
                LinePDF(text=spans_on_same_line, rect=line_rect)
            )

        return PagePDF(page_number=page_number, lines=groups_spans_on_page)

    @staticmethod
    def remove_text_duplicates(page: PagePDF) -> None:
        widget_value_set = {
            widget.field_value for widget in page.widgets if widget.field_value
        }
        page.lines = [
            line
            for line in page.lines
            if not any(span.text in widget_value_set for span in line.text)
        ]
