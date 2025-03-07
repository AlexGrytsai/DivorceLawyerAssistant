from abc import ABC, abstractmethod
from typing import List, Dict, Any, TypeAlias

import pymupdf as fitz  # type: ignore

from src.pdf_extractor.page_formatter import PageFormatter, PageFormatterBase
from src.pdf_extractor.schemas import SpanPDF, DocumentPDF, TableParsed
from src.pdf_extractor.scraper_pdf import ScrapedPage
from src.pdf_extractor.table_processor import TableBaseProcessor
from src.pdf_extractor.text_processor import TextBaseProcessor
from src.pdf_extractor.widger_processor import WidgetSpanBaseProcessor

LineType: TypeAlias = List[Dict[str, Any]] | fitz.Widget


class BaseParserPDF(ABC):

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
    def __init__(
        self,
        scraped_data: List[ScrapedPage],
        text_processor: TextBaseProcessor,
        table_processor: TableBaseProcessor,
        page_formatter: PageFormatterBase,
    ) -> None:
        self._text_processor = text_processor
        self._table_processor = table_processor
        self._page_formatter = page_formatter
        self._document = self._prepare_data(scraped_data)
        self._document_as_str = self._convert_document_to_string(
            self._document
        )

    @property
    def document_as_text(self) -> str:
        return self._document_as_str

    def _convert_document_to_string(self, document: DocumentPDF) -> str:
        return "".join(
            self._page_formatter.format_page(page) for page in document.pages
        )

    def _prepare_data(self, scraped_data: List[ScrapedPage]) -> DocumentPDF:
        pages = self._text_processor.process_text(scraped_data)
        self._table_processor.process_tables(pages, scraped_data)

        return DocumentPDF(pages=pages)
