from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Union, TypeAlias, Set

import pymupdf as fitz  # type: ignore
from pymupdf import Widget  # type: ignore

from src.pdf_extractor.geometry_utils import GeometryBaseUtils
from src.pdf_extractor.schemas import PagePDF, LinePDF, SpanPDF, TableParsed
from src.pdf_extractor.scraper_pdf import ScrapedPage

LineType: TypeAlias = List[Union[SpanPDF, fitz.Widget]]


class TextBaseProcessor(ABC):

    @staticmethod
    @abstractmethod
    def remove_underscores(text: str) -> str:
        pass

    @staticmethod
    @abstractmethod
    def sort_spans_by_vertical_position(
        spans: List[Union[SpanPDF, TableParsed]],
    ) -> List[Union[SpanPDF, TableParsed]]:
        pass

    @abstractmethod
    def process_text(self, scraped_data: List[ScrapedPage]) -> List[PagePDF]:
        pass


class TextProcessor(TextBaseProcessor):
    def __init__(self, geometry_utils: GeometryBaseUtils) -> None:
        self._geometry_utils = geometry_utils

    @staticmethod
    def _convert_raw_spans_to_span_pdf(
        raw_span: List[Dict[str, Any]],
    ) -> List[SpanPDF]:
        return [SpanPDF(**span) for span in raw_span]

    @staticmethod
    def sort_spans_by_vertical_position(
        spans: List[Union[SpanPDF, TableParsed]],
    ) -> List[Union[SpanPDF, TableParsed]]:
        return sorted(spans, key=lambda y: y.rect.y0)

    @staticmethod
    def _sort_spans_by_horizontal_position(
        spans: List[SpanPDF],
    ) -> List[SpanPDF]:
        return sorted(spans, key=lambda x: x.rect.x0)

    @staticmethod
    def _remove_widget_text_duplicates(
        text_line: LineType,
    ) -> LineType:
        widget_value_set: Set[str] = set(
            span.field_value
            for span in text_line
            if isinstance(span, Widget) and span.field_value
        )
        filtered_spans = []
        for span in text_line:
            if isinstance(span, SpanPDF) and span.text not in widget_value_set:
                filtered_spans.append(span)
        filtered_spans += [
            span for span in text_line if isinstance(span, Widget)
        ]

        return filtered_spans

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
                text_line_without_duplicates = (
                    self._remove_widget_text_duplicates(spans_on_same_line)
                )
                groups_spans_on_page.append(
                    LinePDF(
                        text=self._sort_spans_by_horizontal_position(
                            text_line_without_duplicates
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

    @staticmethod
    def remove_underscores(text: str) -> str:
        return text.replace("_", "")

    def _group_text_on_page(
        self,
        spans_and_widgets_list: List[SpanPDF | fitz.Widget],
        page_number: Optional[int] = None,
    ) -> Optional[PagePDF]:
        if not spans_and_widgets_list:
            return None

        sorted_spans_and_widgets_list = self.sort_spans_by_vertical_position(
            spans_and_widgets_list
        )
        groups_spans_on_page = self._group_spans_into_lines(
            sorted_spans_and_widgets_list
        )

        return PagePDF(page_number=page_number, lines=groups_spans_on_page)

    def process_text(self, scraped_data: List[ScrapedPage]) -> List[PagePDF]:
        pages = []
        for i, page_data in enumerate(scraped_data):
            span_pdf_list = self._convert_raw_spans_to_span_pdf(
                raw_span=page_data.text_data
            )
            page = self._group_text_on_page(
                spans_and_widgets_list=span_pdf_list + page_data.widgets,
                page_number=i + 1,
            )
            if page:
                page.widgets = page_data.widgets
                pages.append(page)
        return pages
