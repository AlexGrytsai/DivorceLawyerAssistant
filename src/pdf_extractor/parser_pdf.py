from abc import ABC, abstractmethod
from typing import List, Dict, Any, TypeAlias

import pymupdf as fitz  # type: ignore

from src.pdf_extractor.page_formatter import PageFormatterBase
from src.pdf_extractor.schemas import DocumentPDF
from src.pdf_extractor.scraper_pdf import ScrapedPage
from src.pdf_extractor.table_processor import TableBaseProcessor
from src.pdf_extractor.text_processor import TextBaseProcessor

LineType: TypeAlias = List[Dict[str, Any]] | fitz.Widget


class BaseParserPDF(ABC):

    @abstractmethod
    def prepare_data(self, scraped_data: List[ScrapedPage]) -> DocumentPDF:
        pass

    @property
    @abstractmethod
    def document_as_text(self) -> str:
        pass


class ParserPDF(BaseParserPDF):
    __slots__ = (
        "_text_processor",
        "_table_processor",
        "_page_formatter",
        "_document_as_str",
    )

    def __init__(
        self,
        text_processor: TextBaseProcessor,
        table_processor: TableBaseProcessor,
        page_formatter: PageFormatterBase,
    ) -> None:
        self._text_processor = text_processor
        self._table_processor = table_processor
        self._page_formatter = page_formatter
        self._document_as_str = None

    @property
    def document_as_text(self) -> str:
        return self._document_as_str

    def _convert_document_to_string(
        self,
        document: DocumentPDF,
        is_for_ai: bool = True,
    ) -> str:
        return "".join(
            self._page_formatter.format_page(page, is_for_ai=is_for_ai)
            for page in document.pages
        )

    def prepare_data(
        self,
        scraped_data: List[ScrapedPage],
        is_for_ai: bool = True,
    ) -> None:
        pages = self._text_processor.process_text(scraped_data)
        self._table_processor.process_tables(pages, scraped_data)

        self._document_as_str = self._convert_document_to_string(
            DocumentPDF(pages=pages), is_for_ai=is_for_ai
        )
