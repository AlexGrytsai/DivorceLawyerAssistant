from abc import ABC, abstractmethod
from typing import List, TypeAlias, Tuple, Optional, Dict

import pymupdf as fitz  # type: ignore
from pymupdf import Widget  # type: ignore
from pymupdf.table import Table  # type: ignore
from tabulate import tabulate

from src.services.pdf_extractor.geometry_utils import GeometryBaseUtils
from src.services.pdf_extractor.schemas import (
    PagePDF,
    LinePDF,
    SpanPDF,
    TableParsed,
)
from src.services.pdf_extractor.scraper_pdf import ScrapedPage
from src.services.pdf_extractor.widger_processor import WidgetSpanBaseProcessor

TableType: TypeAlias = List[List[List[Widget | SpanPDF]]]


class TableBaseProcessor(ABC):
    def __init__(self) -> None:
        self._value_widgets_in_table: Dict[str, str] = {}

    @abstractmethod
    def format_table_to_dict(
        self, table: TableParsed, is_widget: bool = False
    ) -> List[Dict[str, str]]:
        pass

    @staticmethod
    @abstractmethod
    def format_table_to_string(table: TableParsed) -> str:
        pass

    @abstractmethod
    def format_table_to_string_for_ai(self, table: TableParsed) -> str:
        pass

    @property
    @abstractmethod
    def value_widgets_in_table(self) -> Dict[str, str]:
        pass

    @abstractmethod
    def process_tables(
        self, pages: List[PagePDF], scraped_data: List[ScrapedPage]
    ) -> None:
        pass


class TableProcessor(TableBaseProcessor):
    __slots__ = ("_geometry_utils",)

    def __init__(
        self,
        geometry_utils: GeometryBaseUtils,
        widget_processor: WidgetSpanBaseProcessor,
    ) -> None:
        super().__init__()
        self._geometry_utils = geometry_utils
        self._widget_processor = widget_processor

    def process_tables(
        self,
        pages: List[PagePDF],
        scraped_data: List[ScrapedPage],
    ) -> None:
        for i, page in enumerate(pages):
            if scraped_data[i].tables:
                page.scraped_tables = scraped_data[i].tables
                table_lines = self._find_text_lines_in_tables(page)
                self._collect_widgets_from_table(table_lines)
                self._remove_table_lines_from_page(table_lines, page)
                self._process_scraped_tables(table_lines, page)

    def format_table_to_string_for_ai(
        self,
        table: TableParsed,
    ) -> str:
        table_data = self.format_table_to_dict(table)

        if not table_data:
            return ""

        headers = table_data[0].keys()

        rows = [" | ".join(headers), "-" * (len(" | ".join(headers)) + 5)]

        for row in table_data:
            row_str = " | ".join(row.get(header, "N/A") for header in headers)
            rows.append(row_str)

        return "\n".join(rows)

    def format_table_to_dict(
        self,
        table: TableParsed,
        use_widget_label: bool = False,
    ) -> List[Dict[str, str]]:
        rows = []
        for row in table.table:
            row_data = {}
            for i, cell in enumerate(row):
                cell_str = self._extract_text(cell, use_widget_label)
                if table.header:
                    if cell_str:
                        row_data[table.header[i]] = cell_str
                    else:
                        row_data[table.header[i]] = "N/A"
            rows.append(row_data)

        return rows

    @property
    def value_widgets_in_table(self) -> Dict[str, str]:
        return self._value_widgets_in_table

    def _collect_widgets_from_table(self, table_lines: List[LinePDF]) -> None:
        for line in table_lines:
            widget_list = [
                widget for widget in line.text if isinstance(widget, Widget)
            ]
            self._value_widgets_in_table.update(
                self._widget_processor.extract_text_widgets(widget_list)
            )

    def _find_text_lines_in_tables(self, page: PagePDF) -> List[LinePDF]:
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
    def _remove_table_lines_from_page(
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
        use_widget_label: bool = False,
    ) -> Optional[str]:
        cell_words = []

        for text in cell_data:
            if isinstance(text, fitz.Widget):
                if use_widget_label:
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
        use_widget_label: bool = False,
    ) -> List[Tuple[str, ...]]:
        text_rows = []

        for row in table.table:
            text_row = []
            for cell in row:
                cell_str = self._extract_text(cell, use_widget_label)
                if cell_str:
                    text_row.append(cell_str)
            if text_row:
                text_rows.append(tuple(text_row))
        return text_rows

    @staticmethod
    def format_table_to_string(table: TableParsed) -> str:
        return tabulate(
            table.table_str_rows or [],
            headers=table.header or [],
            tablefmt="grid",
        )

    def _process_scraped_tables(
        self, table_rows: List[LinePDF], page: PagePDF
    ) -> None:
        if page.scraped_tables:
            page.parsed_tables = [
                self._parse_scraped_table(table_rows, table)
                for table in page.scraped_tables
            ]
            page.scraped_tables = []

            for table in page.parsed_tables:
                table.table_str_rows = self._table_to_text_rows(table)
                table.table_str_rows_for_ai = self._table_to_text_rows(table)
