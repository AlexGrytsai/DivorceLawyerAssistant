from abc import ABC, abstractmethod
from typing import List, Union

from src.services.pdf_tools.schemas import (
    PagePDF,
    LinePDF,
    TableParsed,
    SpanPDF,
)
from src.services.pdf_tools.table_processor import TableBaseProcessor
from src.services.pdf_tools.text_processor import TextBaseProcessor
from src.services.pdf_tools.widger_processor import WidgetSpanBaseProcessor


class PageFormatterBase(ABC):
    @abstractmethod
    def format_page(
        self, page: PagePDF, use_widget_label: bool = False
    ) -> str:
        pass


class PageFormatter(PageFormatterBase):
    __slots__ = ("_text_processor", "_table_processor", "_widget_processor")

    def __init__(
        self,
        text_processor: TextBaseProcessor,
        table_processor: TableBaseProcessor,
        widget_processor: WidgetSpanBaseProcessor,
    ) -> None:
        self._text_processor = text_processor
        self._table_processor = table_processor
        self._widget_processor = widget_processor

    def format_page(
        self,
        page: PagePDF,
        use_widget_label: bool = False,
    ) -> str:
        result = [f"Page # {page.page_number}\n"]

        liens: List[LinePDF] = page.lines if page.lines else []
        tables: List[TableParsed] = (
            page.parsed_tables if page.parsed_tables else []
        )

        elements = self._text_processor.sort_by_vertical_position(
            liens + tables
        )
        element: Union[LinePDF, TableParsed]
        for element in elements:  # type: ignore[assignment]
            if isinstance(element, TableParsed):
                if use_widget_label:

                    result.append(
                        self._table_processor.format_table_to_string_for_ai(
                            element
                        )
                    )
                else:
                    result.append(
                        self._table_processor.format_table_to_string(element)
                    )
            else:
                processed_text = self._process_text_line(element)
                result.append(processed_text)

        return "\n".join(result) + "\n"

    def _process_text_line(self, line: LinePDF) -> str:
        checked_line = self._widget_processor.handle_widget_span_intersections(
            line
        )
        return " ".join(
            (
                span.text
                if isinstance(span, SpanPDF)
                else f"[{self._widget_processor.get_widget_value(span)}]"
            )
            for span in checked_line.text
        )
