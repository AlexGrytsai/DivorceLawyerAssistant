from abc import ABC, abstractmethod
from typing import List, TypeAlias

import pymupdf as fitz
from pymupdf import Widget
from pymupdf.table import Table

from src.pdf_extractor.geometry_utils import GeometryBaseUtils
from src.pdf_extractor.schemas import PagePDF, LinePDF, SpanPDF

TableType: TypeAlias = List[List[List[Widget | SpanPDF]]]


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
        return [
            line
            for line in page.lines
            if any(
                self._geometry_utils.is_rect_inside(
                    fitz.Rect(table.bbox), line.rect
                )
                for table in page.tables
            )
        ]

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
    ) -> List[LinePDF]:
        header_cells_rect = [fitz.Rect(cell) for cell in table.header.cells]

        return [
            row
            for row in table_rows
            if all(
                not self._geometry_utils.is_rect_inside(cell_rect, row.rect)
                for cell_rect in header_cells_rect
            )
        ]

    def _split_words_into_columns(
        self,
        table_rows: List[LinePDF],
        table: Table,
    ) -> TableType:
        column_rects = [fitz.Rect(cell) for cell in table.header.cells]

        return [
            [
                [
                    span
                    for span in row.text
                    if self._geometry_utils.is_word_in_column(
                        span.rect, col_rect
                    )
                ]
                for col_rect in column_rects
            ]
            for row in table_rows
        ]

    def _add_header_to_table(
        self,
        table_without_header: TableType,
        table: Table,
    ) -> None:
        pass

    def create_table(self, table_rows: List[LinePDF], page: PagePDF) -> None:
        for table in page.tables:
            table_without_header = self._split_words_into_columns(
                self._delete_duplicates_in_header(table_rows, table), table
            )
