from abc import abstractmethod, ABC
from typing import List, Dict, Any

import fitz


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
    def __is_same_line(rect1: fitz.Rect, rect2: fitz.Rect, tolerance=5):
        return (
            abs(rect1.y0 - rect2.y0) < tolerance
            and abs(rect1.y1 - rect2.y1) < tolerance
        )

    def __group_spans_into_lines(
        self,
        spans_from_page: List[Dict[str, Any]],
    ) -> List[List[Dict[str, Any]]]:
        if not spans_from_page:
            return []

        groups_spans_on_page: List[List[Dict[str, Any]]] = []
        spans_on_same_line: List[Dict[str, Any]] = []

        line_rect: fitz.Rect = fitz.Rect(spans_from_page[0].get("bbox"))

        for span in spans_from_page:
            if self.__is_same_line(line_rect, fitz.Rect(span["bbox"])):
                spans_on_same_line.append(span)
            else:
                groups_spans_on_page.append(spans_on_same_line)
                spans_on_same_line = [span]
                line_rect = fitz.Rect(span["bbox"])

        if spans_on_same_line:
            groups_spans_on_page.append(spans_on_same_line)

        return groups_spans_on_page

    @staticmethod
    def show_scraped_text(spans: List[List[Dict[str, Any]]]) -> None:
        pass

    @staticmethod
    def __extract_widgets_from_page(page: fitz.Page) -> List[fitz.Widget]:
        widgets_list: List[fitz.Widget] = []
        for widget in page.widgets():
            widgets_list.append(widget)
        return widgets_list

    def scrap_data(self) -> None:
        doc: fitz.Document = fitz.open(self.file_path)
        for page in doc:
            grouped_spans_on_page = self.__group_spans_into_lines(
                self.__extract_text_from_page(page)
            )
            widgets = self.__extract_widgets_from_page(page)
