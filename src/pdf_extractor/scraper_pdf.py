from abc import abstractmethod, ABC
from typing import List, Dict, Any, NamedTuple

import pymupdf as fitz  # type: ignore
from pymupdf.table import Table  # type: ignore


class ScrapedPage(NamedTuple):
    text_data: List[Dict[str, Any]]
    widgets: List[fitz.Widget]
    tables: List[Table]


class BaseScraperPDF(ABC):
    __slots__ = ("_file_path",)

    def __init__(self, file_path: str) -> None:
        self._file_path = file_path

    @property
    @abstractmethod
    def file_path(self) -> str:
        return self._file_path


class ScraperPDF(BaseScraperPDF):
    @property
    def file_path(self) -> str:
        return self._file_path

    @staticmethod
    def __extract_text_from_page(page: fitz.Page) -> List[Dict[str, Any]]:
        list_spans_with_parameters: List[Dict[str, Any]] = []

        for block in page.get_text("dict").get("blocks"):
            if block.get("lines"):
                for line in block["lines"]:
                    for span in line.get("spans"):
                        if span["text"].strip() != "":
                            list_spans_with_parameters.append(span)

        return list_spans_with_parameters

    @staticmethod
    def __extract_tables_from_page(page: fitz.Page) -> List[Table]:
        return [table for table in page.find_tables(strategy="lines_strict")]

    @staticmethod
    def __extract_widgets_from_page(page: fitz.Page) -> List[fitz.Widget]:
        return [widget for widget in page.widgets()]

    def _scrap_page(self, page: fitz.Page) -> ScrapedPage:
        return ScrapedPage(
            self.__extract_text_from_page(page),
            self.__extract_widgets_from_page(page),
            self.__extract_tables_from_page(page),
        )

    def scrap_data(
        self,
    ) -> List[ScrapedPage]:
        doc: fitz.Document = fitz.open(self.file_path)
        scraped_pages: List[ScrapedPage] = []
        for page in doc:
            scraped_pages.append(self._scrap_page(page))
        doc.close()

        return scraped_pages
