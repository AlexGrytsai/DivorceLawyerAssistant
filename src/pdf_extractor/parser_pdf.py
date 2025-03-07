from abc import ABC, abstractmethod
from typing import List, Dict, Any, TypeAlias

import pymupdf as fitz  # type: ignore

from src.pdf_extractor.schemas import SpanPDF, DocumentPDF, TableParsed
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
        self._document_as_str = self._convert_document_to_string(
            self._document
        )

    @abstractmethod
    def _prepare_data(self, scraped_data: List[ScrapedPage]) -> DocumentPDF:
        pass

    @abstractmethod
    def _convert_document_to_string(self, document: DocumentPDF) -> str:
        pass

    @property
    @abstractmethod
    def document_as_text(self) -> str:
        pass


class ParserPDF(BaseParserPDF):
    @property
    def document_as_text(self) -> str:
        return self._document_as_str

    def _convert_document_to_string(self, document: DocumentPDF) -> str:
        text_from_document_list = []
        for page in document.pages:
            page_str_list = [f"Page # {page.page_number}\n\n"]
            list_with_line_and_table = (
                self._text_processor.sort_spans_by_vertical_position(
                    page.lines + page.parsed_tables
                )
            )
            for line in list_with_line_and_table:
                line_str_list = []
                if isinstance(line, TableParsed):
                    page_str_list.append(
                        self._table_processor.format_table_to_string(line)
                    )
                    page_str_list.append("\n")
                else:
                    checked_line = self._widget_processor.handle_widget_span_intersections(
                        line
                    )
                    for span in checked_line.text:
                        if isinstance(span, SpanPDF):
                            line_str_list.append(f"{span.text}")
                        else:
                            span = self._widget_processor.get_widget_value(
                                span
                            )
                            line_str_list.append(f"[{span}]")
                    page_str_list.append(" ".join(line_str_list))
                    page_str_list.append("\n")
            text_from_document_list.append("".join(page_str_list) + "\n")
        return "".join(text_from_document_list)

    def _prepare_data(self, scraped_data: List[ScrapedPage]) -> DocumentPDF:
        pages = self._text_processor.process_text(scraped_data)
        self._table_processor.process_tables(pages, scraped_data)

        return DocumentPDF(pages=pages)
