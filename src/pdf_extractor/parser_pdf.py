from abc import ABC, abstractmethod
from itertools import chain
from typing import List, Dict, Any, TypeAlias, Optional

import pymupdf as fitz

from src.pdf_extractor.schemas import SpanPDF, LinePDF, PagePDF, DocumentPDF
from src.pdf_extractor.scraper_pdf import ScrapedPage

LineType: TypeAlias = List[Dict[str, Any]] | fitz.Widget


class BaseParserPDF(ABC):
    def __init__(self, scraped_data: List[ScrapedPage]) -> None:
        self._document = self._prepare_data(scraped_data)

    @abstractmethod
    def _prepare_data(self, scraped_data: List[ScrapedPage]) -> DocumentPDF:
        pass

    @property
    @abstractmethod
    def all_fields_in_document(self) -> List[fitz.Widget]:
        pass

    @property
    @abstractmethod
    def text_from_document(self) -> None:
        pass


class ParserPDF(BaseParserPDF):
    @property
    def text_from_document(self) -> None:
        text_from_document = ""
        for page in self._document.pages:
            page_str = f"Page # {page.page_number}\n\n"
            for line in page.lines:
                line_str = ""
                for span in line.text:
                    if isinstance(span, SpanPDF):
                        line_str += span.text
                    else:
                        if span.field_value:
                            line_str += span.field_value
                        else:
                            line_str += f"{'_' * 10} "
                page_str += line_str + "\n"
            text_from_document += f"{page_str}\n"
        return text_from_document

    @property
    def all_fields_in_document(self) -> List[fitz.Widget]:
        return [
            widget for page in self._document.pages for widget in page.widgets
        ]

    def _prepare_data(self, scraped_data: List[ScrapedPage]) -> DocumentPDF:
        clean_document = []
        for i in range(len(scraped_data)):
            page = self.__group_spans_on_page(
                scraped_data[i].text_data, page_number=i + 1
            )
            if scraped_data[i].tables:
                page.tables = scraped_data[i].tables

                table_lines = self._find_text_lines_in_tables(page)
                self._update_page_excluding_table_lines(
                    table_lines=table_lines,
                    page=page,
                )
                self._create_parser_table(table_lines, page)

            page.widgets = scraped_data[i].widgets

            self._remove_text_duplicates_with_equal_value_of_the_widget(page)

            self.__add_widgets_to_lines_on_page(page=page)

            clean_document.append(page)

        return DocumentPDF(pages=clean_document)

    @staticmethod
    def __is_same_line(rect1: fitz.Rect, rect2: fitz.Rect, tolerance=5):
        return (
            abs(rect1.y0 - rect2.y0) < tolerance
            or abs(rect1.y1 - rect2.y1) < tolerance
        )

    @staticmethod
    def __is_rect_inside(
        outer_rect: fitz.Rect, inner_rect: fitz.Rect, tolerance=5
    ):
        return (
            outer_rect.x0 - tolerance
            <= inner_rect.x0
            <= outer_rect.x1 + tolerance
            and outer_rect.y0 - tolerance
            <= inner_rect.y0
            <= outer_rect.y1 + tolerance
            and outer_rect.x0 - tolerance
            <= inner_rect.x1
            <= outer_rect.x1 + tolerance
            and outer_rect.y0 - tolerance
            <= inner_rect.y1
            <= outer_rect.y1 + tolerance
        )

    @staticmethod
    def _update_page_excluding_table_lines(
        table_lines: List[LinePDF], page: PagePDF
    ) -> None:
        table_lines_set = {id(line) for line in table_lines}

        page.lines = [
            line for line in page.lines if id(line) not in table_lines_set
        ]

    def _find_text_lines_in_tables(
        self,
        page: PagePDF,
    ) -> List[LinePDF]:
        return list(
            filter(
                lambda line: any(
                    self.__is_rect_inside(fitz.Rect(table.bbox), line.rect)
                    for table in page.tables
                ),
                chain.from_iterable(page.lines for _ in page.tables),
            )
        )

    def _create_parser_table(
        self,
        table_lines: List[LinePDF],
        page: PagePDF,
    ) -> None:
        pass

    def __add_widgets_to_lines_on_page(self, page: PagePDF) -> None:
        for line in page.lines:
            for widget in page.widgets:
                if self.__is_same_line(line.text[0].rect, widget.rect):
                    line.text.append(widget)
            line.text.sort(key=lambda x: x.rect.x0)

    @staticmethod
    def _remove_text_duplicates_with_equal_value_of_the_widget(
        page: PagePDF,
    ) -> None:
        widget_value_set = set(
            widget.field_value for widget in page.widgets if widget.field_value
        )
        page.lines = [
            line
            for line in page.lines
            if not any(span.text in widget_value_set for span in line.text)
        ]

    def __group_spans_on_page(
        self,
        spans_from_page: LineType,
        page_number: Optional[int] = None,
    ) -> PagePDF | None:
        if not spans_from_page:
            return None

        groups_spans_on_page: List[LinePDF] = []
        spans_on_same_line: List[SpanPDF] = []

        line_rect: fitz.Rect = fitz.Rect(spans_from_page[0].get("bbox"))

        for raw_span in spans_from_page:
            span = SpanPDF(**raw_span)
            if self.__is_same_line(line_rect, span.rect):
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
