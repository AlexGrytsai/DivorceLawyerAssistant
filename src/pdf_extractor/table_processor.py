from abc import ABC, abstractmethod
from itertools import chain
from typing import List

import pymupdf as fitz
from pymupdf.table import Table

from src.pdf_extractor.geometry_utils import GeometryBaseUtils
from src.pdf_extractor.schemas import PagePDF, LinePDF


class TableBaseProcessor(ABC):
    def __init__(self, geometry_utils: GeometryBaseUtils) -> None:
        self._geometry_utils = geometry_utils

    @abstractmethod
    def find_text_lines_in_tables(self, page: PagePDF) -> List[LinePDF]:
        pass

    @staticmethod
    @abstractmethod
    def update_page_excluding_table_lines(
        table_lines: List[LinePDF], page: PagePDF
    ) -> None:
        pass

    @abstractmethod
    def create_table(self, table_rows: List[LinePDF], page: PagePDF) -> None:
        pass


class TableProcessor(TableBaseProcessor):

    def find_text_lines_in_tables(self, page: PagePDF) -> List[LinePDF]:
        return list(
            filter(
                lambda line: any(
                    self._geometry_utils.is_rect_inside(
                        fitz.Rect(table.bbox), line.rect
                    )
                    for table in page.tables
                ),
                chain.from_iterable(page.lines for _ in page.tables),
            )
        )

    @staticmethod
    def update_page_excluding_table_lines(
        table_lines: List[LinePDF],
        page: PagePDF,
    ) -> None:
        table_lines_set = {id(line) for line in table_lines}
        page.lines = [
            line for line in page.lines if id(line) not in table_lines_set
        ]

    def _delete_duplicates_in_header(
        self,
        table_rows: List[LinePDF],
        table: Table,
    ) -> None:
        pass

    @staticmethod
    def _split_words_into_columns(
        table_rows: List[LinePDF],
        page: PagePDF,
    ) -> None:
        pass

    def create_table(self, table_rows: List[LinePDF], page: PagePDF) -> None:
        pass
