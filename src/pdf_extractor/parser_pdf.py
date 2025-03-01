from abc import ABC, abstractmethod
from typing import List, Dict, Any, TypeAlias, Optional

import fitz

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
            page_str = ""
            for line in page.lines:
                line_str = ""
                for span in line.text:
                    if isinstance(span, SpanPDF):
                        line_str += span.text
                    else:
                        if span.field_value:
                            line_str += span.field_value
                        else:
                            line_str += "_" * 10
                page_str += line_str + "\n"
            text_from_document += page_str
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
            page.widgets = scraped_data[i].widgets

            self.__add_widgets_to_lines_on_page(page=page)

            clean_document.append(page)

        return DocumentPDF(pages=clean_document)

    @staticmethod
    def __is_same_line(rect1: fitz.Rect, rect2: fitz.Rect, tolerance=5):
        return (
            abs(rect1.y0 - rect2.y0) < tolerance
            and abs(rect1.y1 - rect2.y1) < tolerance
        )

    def __add_widgets_to_lines_on_page(self, page: PagePDF) -> None:
        for line in page.lines:
            for widget in page.widgets:
                if self.__is_same_line(line.text[0].rect, widget.rect):
                    line.text.append(widget)
            line.text.sort(key=lambda x: x.rect.x0)

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
                groups_spans_on_page.append(LinePDF(text=spans_on_same_line))
                spans_on_same_line = [span]
                line_rect = span.rect

        if spans_on_same_line:
            groups_spans_on_page.append(LinePDF(text=spans_on_same_line))

        return PagePDF(page_number=page_number, lines=groups_spans_on_page)
