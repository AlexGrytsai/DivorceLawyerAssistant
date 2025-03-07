from abc import ABC, abstractmethod
from typing import List, Dict, Any, TypeAlias

import pymupdf as fitz  # type: ignore

from src.pdf_extractor.schemas import SpanPDF, DocumentPDF
from src.pdf_extractor.scraper_pdf import ScrapedPage
from src.pdf_extractor.table_processor import TableBaseProcessor
from src.pdf_extractor.text_processor import TextBaseProcessor
from src.pdf_extractor.widger_processor import WidgetSpanBaseProcessor

LineType: TypeAlias = List[Dict[str, Any]] | fitz.Widget


class BaseParserPDF(ABC):
    def __init__(
        self,
        scraped_data: List[ScrapedPage],
        text_processor: TextBaseProcessor,
        table_processor: TableBaseProcessor,
        widget_processor: WidgetSpanBaseProcessor,
    ) -> None:
        self._text_processor = text_processor
        self._table_processor = table_processor
        self._widget_processor = widget_processor
        self._document = self._prepare_data(scraped_data)

    @abstractmethod
    def _prepare_data(self, scraped_data: List[ScrapedPage]) -> DocumentPDF:
        pass

    @property
    @abstractmethod
    def text_from_document(self) -> str:
        pass


class ParserPDF(BaseParserPDF):
    @property
    def text_from_document(self) -> str:
        text_from_document_list = []
        for page in self._document.pages:
            page_str_list = [f"Page # {page.page_number}\n\n"]
            for line in page.lines:
                checked_line = (
                    self._widget_processor.handle_widget_span_intersections(
                        line
                    )
                )
                line_str_list = []
                for span in checked_line.text:
                    if isinstance(span, SpanPDF):
                        line_str_list.append(f"{span.text}")
                    else:
                        span = self._widget_processor.get_widget_value(span)
                        line_str_list.append(f"[{span}]")
                page_str_list.append(" ".join(line_str_list))
                page_str_list.append("\n")
            text_from_document_list.append("".join(page_str_list) + "\n")
        return "".join(text_from_document_list)

    def _prepare_data(self, scraped_data: List[ScrapedPage]) -> DocumentPDF:
        clean_document = []
        for i in range(len(scraped_data)):
            span_pdf_list = self._text_processor.convert_raw_spans_to_span_pdf(
                raw_span=scraped_data[i].text_data
            )
            page = self._text_processor.group_text_on_page(
                spans_and_widgets_list=span_pdf_list + scraped_data[i].widgets,
                page_number=i + 1,
            )
            if page:
                page.widgets = scraped_data[i].widgets

                if scraped_data[i].tables:
                    page.scraped_tables = scraped_data[i].tables

                    table_lines = (
                        self._table_processor.find_text_lines_in_tables(page)
                    )
                    self._table_processor.remove_table_lines_from_page(
                        table_lines=table_lines,
                        page=page,
                    )
                    self._table_processor.process_scraped_tables(
                        table_lines, page
                    )

                clean_document.append(page)

        return DocumentPDF(pages=clean_document)
