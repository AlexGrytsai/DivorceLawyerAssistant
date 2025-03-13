from abc import ABC, abstractmethod
from typing import List, Dict, Any, TypeAlias

import pymupdf as fitz  # type: ignore

from src.services.pdf_extractor import (
    TextBaseProcessor,
    TableBaseProcessor,
    WidgetSpanBaseProcessor,
    PageFormatterBase,
)
from src.services.pdf_extractor.schemas import DocumentPDF
from src.services.pdf_extractor.scraper_pdf import ScrapedPage

LineType: TypeAlias = List[Dict[str, Any]] | fitz.Widget


class ParserPDFBase(ABC):

    @abstractmethod
    def prepare_data(
        self, scraped_data: List[ScrapedPage], use_widget_label: bool = True
    ) -> None:
        pass

    @property
    @abstractmethod
    def document_as_text(self) -> str:
        pass

    @property
    @abstractmethod
    def widget_data_dict(self) -> Dict[str, str]:
        pass


class ParserPDF(ParserPDFBase):
    __slots__ = (
        "_text_processor",
        "_table_processor",
        "_widget_processor",
        "_page_formatter",
        "_document_as_str",
        "_widget_data",
    )

    def __init__(
        self,
        text_processor: TextBaseProcessor,
        table_processor: TableBaseProcessor,
        widget_processor: WidgetSpanBaseProcessor,
        page_formatter: PageFormatterBase,
    ) -> None:
        self._text_processor = text_processor
        self._table_processor = table_processor
        self._widget_processor = widget_processor
        self._page_formatter = page_formatter
        self._document_as_str: str = ""
        self._widget_data: Dict[str, str] = {}

    @property
    def document_as_text(self) -> str:
        return self._document_as_str

    @property
    def widget_data_dict(self) -> Dict[str, str]:
        return self._widget_data

    def _convert_document_to_string(
        self,
        document: DocumentPDF,
        use_widget_label: bool = False,
    ) -> str:
        return "".join(
            self._page_formatter.format_page(
                page, use_widget_label=use_widget_label
            )
            for page in document.pages
        )

    def prepare_data(
        self,
        scraped_data: List[ScrapedPage],
        use_widget_label: bool = False,
    ) -> None:
        pages = self._text_processor.process_text(scraped_data)
        self._table_processor.process_tables(pages, scraped_data)

        self._document_as_str = self._convert_document_to_string(
            DocumentPDF(pages=pages), use_widget_label=use_widget_label
        )
        self._widget_data = self._widget_processor.extract_text_widgets(
            [widget for page in pages for widget in page.widgets]
        )
