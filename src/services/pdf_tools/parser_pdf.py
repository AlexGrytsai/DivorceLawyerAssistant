import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, TypeAlias

import pymupdf as fitz  # type: ignore

from src.services.pdf_tools.page_formatter import PageFormatterBase
from src.services.pdf_tools.schemas import DocumentPDF
from src.services.pdf_tools.scraper_pdf import ScrapedPage
from src.services.pdf_tools.table_processor import TableBaseProcessor
from src.services.pdf_tools.text_processor import TextBaseProcessor
from src.services.pdf_tools.widger_processor import WidgetSpanBaseProcessor

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
    def widget_data_dict(self) -> Dict[str, Dict[str, str]]:
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
        self._widget_data: Dict[str, Dict[str, str]] = {
            "Text": {},
            "Table": {},
        }

    @property
    def document_as_text(self) -> str:
        return self._document_as_str

    @property
    def widget_data_dict(self) -> Dict[str, Dict[str, str]]:
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

        self._widget_data["Table"] = (
            self._table_processor.value_widgets_in_table
        )

        self._document_as_str = self._convert_document_to_string(
            DocumentPDF(pages=pages), use_widget_label=use_widget_label
        )
        self._widget_data["Text"] = (
            self._widget_processor.extract_text_widgets(
                [
                    widget
                    for page in pages
                    for widget in page.widgets
                    if widget not in set(self._widget_data["Table"].keys())
                ]
            )
        )


class ParserPDFWidget(ParserPDFBase):
    __slots__ = ("_widget_dict",)

    def __init__(self) -> None:
        self._widget_dict: Dict[str, Dict[str, str]] = {}

    def prepare_data(
        self, scraped_data: List[ScrapedPage], use_widget_label: bool = True
    ) -> None:
        for page in scraped_data:
            if page.widgets:
                for widget in page.widgets:
                    if widget.field_type_string == "Text":
                        self._widget_dict[widget.field_name] = {
                            "value": widget.field_value,
                            "widget_instance": widget,
                        }

    @property
    def document_as_text(self) -> str:
        return json.dumps(
            {key: value["value"] for key, value in self._widget_dict.items()}
        )

    @property
    def widget_data_dict(self) -> Dict[str, Dict[str, str]]:
        return self._widget_dict
