from abc import ABC, abstractmethod
from typing import List, TypeAlias, Tuple

import pymupdf as fitz
from pymupdf import Widget
from pymupdf.table import Table
from tabulate import tabulate
from src.pdf_extractor.geometry_utils import GeometryBaseUtils
from src.pdf_extractor.schemas import PagePDF, LinePDF, SpanPDF, TableParsed

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
    def process_scraped_tables(
        self, table_rows: List[LinePDF], page: PagePDF
    ) -> None:
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
                for table in page.scraped_tables
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

        filtered_rows = []
        for row in table_rows:
            is_inside = False
            for cell_rect in header_cells_rect:
                if self._geometry_utils.is_rect_inside(
                    cell_rect, row.rect
                ) or self._geometry_utils.is_partially_inside_rect(
                    cell_rect, row.rect
                ):
                    is_inside = True
                    break
            if not is_inside:
                filtered_rows.append(row)

        return filtered_rows

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

    def _parse_scraped_table(
        self, table_rows: List[LinePDF], table: Table
    ) -> TableParsed:
        table_without_header = self._split_words_into_columns(
            self._delete_duplicates_in_header(table_rows, table), table
        )
        return TableParsed(
            table=table_without_header,
            header=table.header.names,
            rect=fitz.Rect(table.bbox),
        )

    @staticmethod
    def _table_to_text_rows(table: TableParsed) -> List[Tuple[str, ...]]:
        text_rows = []
        for row in table.table:
            text_row = []
            for cell in row:
                cell_words = []
                for text in cell:
                    if isinstance(text, fitz.Widget):
                        if text.field_value:
                            cell_words.append(text.field_value)
                    else:
                        cell_words.append(text.text)
                if cell_words:
                    text_row.append(
                        " ".join(cell_words),
                    )
            if text_row:
                text_rows.append(tuple(text_row))
        print(tabulate(text_rows, tablefmt="grid", headers=table.header))
        return text_rows

    def process_scraped_tables(
        self, table_rows: List[LinePDF], page: PagePDF
    ) -> None:
        page.parsed_tables = [
            self._parse_scraped_table(table_rows, table)
            for table in page.scraped_tables
        ]
        page.scraped_tables = None

        for table in page.parsed_tables:
            table_in_text = self._table_to_text_rows(table)
            print("*" * 50)
