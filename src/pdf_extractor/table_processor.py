import json
from abc import ABC, abstractmethod
from typing import List, TypeAlias, Tuple, Optional

import pymupdf as fitz  # type: ignore
from pymupdf import Widget  # type: ignore
from pymupdf.table import Table  # type: ignore

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
    def remove_table_lines_from_page(
        table_lines: List[LinePDF], page: PagePDF
    ) -> None:
        pass

    @abstractmethod
    def process_scraped_tables(
        self, table_rows: List[LinePDF], page: PagePDF
    ) -> None:
        pass

    @abstractmethod
    def format_table_to_json(
        self, table: TableParsed, is_widget: bool = False
    ) -> str:
        pass


class TableProcessor(TableBaseProcessor):

    def find_text_lines_in_tables(self, page: PagePDF) -> List[LinePDF]:
        if page.scraped_tables:
            table_rects = [
                fitz.Rect(table.bbox) for table in page.scraped_tables
            ]
        else:
            table_rects = []

        result = []
        for line in page.lines:
            if any(
                self._geometry_utils.is_rect_inside(table_rect, line.rect)
                for table_rect in table_rects
            ):
                result.append(line)
        return result

    @staticmethod
    def remove_table_lines_from_page(
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
        header_rects = [fitz.Rect(cell) for cell in table.header.cells]

        return [
            row
            for row in table_rows
            if not any(
                self._geometry_utils.is_rect_inside(cell_rect, row.rect)
                or self._geometry_utils.is_partially_inside_rect(
                    cell_rect, row.rect
                )
                for cell_rect in header_rects
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

    def _filter_lines_inside_table(
        self,
        lines: List[LinePDF],
        table: Table,
    ) -> List[LinePDF]:
        return [
            line
            for line in lines
            if self._geometry_utils.is_rect_inside(
                fitz.Rect(table.bbox), line.rect
            )
        ]

    def _parse_scraped_table(
        self,
        all_rows_in_tables: List[LinePDF],
        table: Table,
    ) -> TableParsed:
        table_without_header = self._split_words_into_columns(
            table_rows=self._delete_duplicates_in_header(
                table_rows=self._filter_lines_inside_table(
                    all_rows_in_tables, table
                ),
                table=table,
            ),
            table=table,
        )

        return TableParsed(
            table=table_without_header,
            header=table.header.names,
            rect=fitz.Rect(table.bbox),
        )

    @staticmethod
    def _extract_text(
        cell_data: List[fitz.Widget | SpanPDF],
        is_widget: bool = False,
    ) -> Optional[str]:
        cell_words = []

        for text in cell_data:
            if isinstance(text, fitz.Widget):
                if is_widget:
                    if text.field_value:
                        value = text.field_value
                    else:
                        value = "N/A"
                    cell_words.append(f"{text.field_name}: {value}")
                elif text.field_value:
                    cell_words.append(text.field_value)
            else:
                cell_words.append(text.text)
        if cell_words:
            return " ".join(cell_words)
        return None

    def _table_to_text_rows(
        self,
        table: TableParsed,
        is_widget: bool = False,
    ) -> List[Tuple[str, ...]]:
        text_rows = []

        for row in table.table:
            text_row = []
            for cell in row:
                cell_str = self._extract_text(cell, is_widget)
                if cell_str:
                    text_row.append(cell_str)
            if text_row:
                text_rows.append(tuple(text_row))
        return text_rows

    def format_table_to_json(
        self,
        table: TableParsed,
        is_widget: bool = False,
    ) -> str:
        rows = []
        for row in table.table:
            row_data = {}
            for i, cell in enumerate(row):
                cell_str = self._extract_text(cell, is_widget)
                if cell_str:
                    row_data[table.header[i]] = cell_str
                else:
                    row_data[table.header[i]] = "The field is not filled"
            rows.append(row_data)

        return json.dumps(rows)

    def process_scraped_tables(
        self, table_rows: List[LinePDF], page: PagePDF
    ) -> None:
        if page.scraped_tables:
            page.parsed_tables = [
                self._parse_scraped_table(table_rows, table)
                for table in page.scraped_tables
            ]
            page.scraped_tables = None

            for table in page.parsed_tables:
                table.table_str_rows = self._table_to_text_rows(table)
                table.table_str_rows_for_ai = self._table_to_text_rows(
                    table, is_widget=True
                )
