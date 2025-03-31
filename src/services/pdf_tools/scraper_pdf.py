from abc import abstractmethod, ABC
from typing import List, Dict, Any, NamedTuple

import pymupdf as fitz  # type: ignore
from pymupdf.table import Table  # type: ignore

from src.services.pdf_tools.decorators import handle_pymupdf_exceptions


class ScrapedPage(NamedTuple):
    text_data: List[Dict[str, Any]]
    widgets: List[fitz.Widget]
    tables: List[Table]


class BaseScraperPDF(ABC):
    __slots__ = ("_file_path",)

    def __init__(self, file_path: str) -> None:
        self._file_path = file_path

    @property
    def file_path(self) -> str:
        return self._file_path

    @abstractmethod
    def scrap_data(self) -> List[ScrapedPage]:
        pass


class ScraperPDF(BaseScraperPDF):
    __slots__ = ()

    @staticmethod
    def __extract_text_from_page(page: fitz.Page) -> List[Dict[str, Any]]:
        list_spans_with_parameters: List[Dict[str, Any]] = []

        for block in page.get_text("dict").get("blocks"):
            if block.get("lines"):
                for line in block["lines"]:
                    list_spans_with_parameters.extend(
                        span
                        for span in line.get("spans")
                        if span["text"].strip() != ""
                    )
        return list_spans_with_parameters

    @staticmethod
    def __extract_tables_from_page(page: fitz.Page) -> List[Table]:
        return list(page.find_tables(strategy="lines_strict"))

    @staticmethod
    def __extract_widgets_from_page(page: fitz.Page) -> List[fitz.Widget]:
        return list(page.widgets())

    def _scrap_page(self, page: fitz.Page) -> ScrapedPage:
        return ScrapedPage(
            self.__extract_text_from_page(page),
            self.__extract_widgets_from_page(page),
            self.__extract_tables_from_page(page),
        )

    @handle_pymupdf_exceptions
    def scrap_data(
        self,
    ) -> List[ScrapedPage]:
        doc: fitz.Document = fitz.open(self.file_path)
        scraped_pages: List[ScrapedPage] = []
        scraped_pages.extend(self._scrap_page(page) for page in doc)
        doc.close()

        return scraped_pages


class ScraperWidgetFromPDF(BaseScraperPDF):
    __slots__ = ()

    @handle_pymupdf_exceptions
    def scrap_data(self) -> List[ScrapedPage]:
        doc: fitz.Document = fitz.open(self.file_path)
        scraped_pages: List[ScrapedPage] = []
        scraped_pages.extend(
            ScrapedPage([], list(page.widgets()), []) for page in doc
        )
        doc.close()

        return scraped_pages
