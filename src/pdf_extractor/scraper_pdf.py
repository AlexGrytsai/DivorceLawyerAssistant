from abc import abstractmethod, ABC
from typing import List, Dict, Any, Tuple, TypeAlias

import fitz

ScrapedPage: TypeAlias = Tuple[List[Dict[str, Any]], List[fitz.Widget]]


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
            block: dict[str, list]

            if block.get("lines"):
                for line in block["lines"]:
                    line: dict

                    for span in line.get("spans"):
                        if span["text"].strip() != "":
                            list_spans_with_parameters.append(span)

        return list_spans_with_parameters

    @staticmethod
    def __extract_widgets_from_page(page: fitz.Page) -> List[fitz.Widget]:
        widgets_list: List[fitz.Widget] = []
        for widget in page.widgets():
            widgets_list.append(widget)
        return widgets_list

    def scrap_data(
        self,
    ) -> List[ScrapedPage]:
        doc: fitz.Document = fitz.open(self.file_path)
        scraped_pages: List[ScrapedPage] = []
        for page in doc:
            scraped_pages.append(
                (
                    self.__extract_text_from_page(page),
                    self.__extract_widgets_from_page(page),
                )
            )

        return scraped_pages
