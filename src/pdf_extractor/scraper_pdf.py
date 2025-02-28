from abc import abstractmethod, ABC
from typing import List, Dict, Any

import fitz
from pympler.asizeof import asizeof


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
        list_text_with_parameters: List[Dict[str, Any]] = []

        for block in page.get_text("dict").get("blocks"):
            block: dict[str, list]

            if block.get("lines"):
                for line in block["lines"]:
                    line: dict

                    for span in line.get("spans"):
                        if span["text"].strip() != "":
                            list_text_with_parameters.append(span)

        return list_text_with_parameters

    @staticmethod
    def __is_same_line(rect1: fitz.Rect, rect2: fitz.Rect, tolerance=5):
        return (
            abs(rect1.y0 - rect2.y0) < tolerance
            and abs(rect1.y1 - rect2.y1) < tolerance
        )

    def _extract_widgets_from_page(self, page: fitz.Page) -> None:
        pass

    def scrap_data(self) -> None:
        doc: fitz.Document = fitz.open(self.file_path)
        for page in doc:
            text_with_parameters = self.__extract_text_from_page(page)
            self._extract_widgets_from_page(page)
