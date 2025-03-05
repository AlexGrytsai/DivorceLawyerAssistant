from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

import pymupdf as fitz

from src.pdf_extractor.geometry_utils import GeometryBaseUtils
from src.pdf_extractor.schemas import PagePDF, LinePDF, SpanPDF


class TextBaseProcessor(ABC):
    def __init__(self, geometry_utils: GeometryBaseUtils) -> None:
        self._geometry_utils = geometry_utils

    @abstractmethod
    def group_text_on_page(
        self,
        spans_and_widgets_list: List[SpanPDF | fitz.Widget],
        page_number: Optional[int] = None,
    ) -> PagePDF | None:
        pass

    @staticmethod
    @abstractmethod
    def remove_text_duplicates(page: PagePDF) -> None:
        pass

    @staticmethod
    @abstractmethod
    def convert_raw_spans_to_span_pdf(
        raw_span: List[Dict[str, Any]],
    ) -> List[SpanPDF]:
        pass


class TextProcessor(TextBaseProcessor):
    @staticmethod
    def convert_raw_spans_to_span_pdf(
        raw_span: List[Dict[str, Any]],
    ) -> List[SpanPDF]:
        return [SpanPDF(**span) for span in raw_span]

    @staticmethod
    def _sort_spans_by_vertical_position(
        spans: List[SpanPDF],
    ) -> List[SpanPDF]:
        return sorted(spans, key=lambda y: y.rect.y0)

    @staticmethod
    def _sort_spans_by_horizontal_position(
        spans: List[SpanPDF],
    ) -> List[SpanPDF]:
        return sorted(spans, key=lambda x: x.rect.x0)

    def _group_spans_into_lines(
        self, sorted_spans: List[SpanPDF]
    ) -> List[LinePDF]:
        groups_spans_on_page: List[LinePDF] = []
        spans_on_same_line: List[SpanPDF] = []
        line_rect: fitz.Rect = fitz.Rect(sorted_spans[0].rect)

        for span in sorted_spans:
            if self._geometry_utils.is_same_line(line_rect, span.rect):
                spans_on_same_line.append(span)
            else:
                groups_spans_on_page.append(
                    LinePDF(
                        text=self._sort_spans_by_horizontal_position(
                            spans_on_same_line
                        ),
                        rect=line_rect,
                    )
                )
                spans_on_same_line = [span]
                line_rect = span.rect

        if spans_on_same_line:
            groups_spans_on_page.append(
                LinePDF(text=spans_on_same_line, rect=line_rect)
            )

        return groups_spans_on_page

    def group_text_on_page(
        self,
        spans_and_widgets_list: List[SpanPDF | fitz.Widget],
        page_number: Optional[int] = None,
    ) -> Optional[PagePDF]:
        if not spans_and_widgets_list:
            return None

        sorted_spans_and_widgets_list = self._sort_spans_by_vertical_position(
            spans_and_widgets_list
        )
        groups_spans_on_page = self._group_spans_into_lines(
            sorted_spans_and_widgets_list
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
