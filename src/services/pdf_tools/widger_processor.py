from abc import ABC, abstractmethod
from typing import Optional, List, Dict

import pymupdf as fitz  # type: ignore
from pymupdf import Widget  # type: ignore

from src.services.pdf_tools.geometry_utils import GeometryBaseUtils
from src.services.pdf_tools.schemas import LinePDF, SpanPDF
from src.services.pdf_tools.text_processor import TextBaseProcessor


class WidgetSpanBaseProcessor(ABC):
    __slots__ = ("_geometry_utils", "_text_processor")

    def __init__(
        self,
        geometry_utils: GeometryBaseUtils,
        text_processor: TextBaseProcessor,
    ) -> None:
        self._geometry_utils = geometry_utils
        self._text_processor = text_processor

    @staticmethod
    @abstractmethod
    def get_widget_value(
        widget: fitz.Widget, use_widget_label: bool = False
    ) -> Optional[str]:
        pass

    @staticmethod
    @abstractmethod
    def extract_text_widgets(
        widgets: List[fitz.Widget],
    ) -> Dict[str, str]:
        pass

    @abstractmethod
    def handle_widget_span_intersections(
        self,
        lien_list: LinePDF,
    ) -> LinePDF:
        pass


class WidgetSpanProcessor(WidgetSpanBaseProcessor):
    __slots__ = ()

    @staticmethod
    def extract_text_widgets(
        widgets: List[fitz.Widget],
    ) -> Dict[str, str]:
        return {
            widget.field_name: widget.field_value
            for widget in widgets
            if widget.field_type_string in {"Text"} and widget.field_value
        }

    @staticmethod
    def get_widget_value(
        widget: fitz.Widget,
        use_widget_label: bool = True,
    ) -> Optional[str]:
        if use_widget_label:
            if widget.field_type_string in ("Text", "ComboBox"):
                return (
                    f"{widget.field_name}: {widget.field_value}"
                    if widget.field_value
                    else f"{widget.field_name}: N/A"
                )
            elif widget.field_type_string == "CheckBox":
                return (
                    f"{widget.field_name}: ON"
                    if widget.field_value
                    else f"{widget.field_name}: OFF"
                )

        if widget.field_type_string in ("Text", "ComboBox"):
            return f"{widget.field_value}" if widget.field_value else "N/A"
        elif widget.field_type_string == "CheckBox":
            return "ON" if widget.field_value else "OFF"
        return None

    def _replace_text_in_span(
        self,
        target_span: SpanPDF,
        replacement_span: fitz.Widget,
        tolerance_before_index: int = 2,
        tolerance_after_index: int = 1,
    ) -> SpanPDF:
        """
        Replaces the text in the target span with the value of
        the replacement span.

        This method calculates the intersection of the target span and
        the replacement span, and then replaces the text in the target span
        with the value of the replacement span.

        Args:
            target_span (SpanPDF): The span to replace the text in.
            replacement_span (fitz.Widget): The widget to replace the text with

        Returns:
            SpanPDF: The target span with the replaced text.
        """

        intersection = self._geometry_utils.get_intersection_rect(
            target_span.rect, replacement_span.rect
        )

        if intersection:
            # Calculate the start and end indices of the intersection
            start_index = int(
                (intersection.x0 - target_span.rect.x0)
                / (target_span.rect.x1 - target_span.rect.x0)
                * len(target_span.text)
            )
            end_index = int(
                (intersection.x1 - target_span.rect.x0)
                / (target_span.rect.x1 - target_span.rect.x0)
                * len(target_span.text)
            )
            # Split the text in the target span into three parts: before,
            # intersection, and after
            text_before = target_span.text[
                : start_index + tolerance_before_index
            ]
            text_after = target_span.text[end_index - tolerance_after_index :]

            new_text = self._text_processor.remove_underscores(
                f"{text_before}"
                f"[{self.get_widget_value(replacement_span)}]{text_after}"
            )

            target_span.text = new_text

        return target_span

    def handle_widget_span_intersections(
        self,
        lien_list: LinePDF,
    ) -> LinePDF:
        widgets = [span for span in lien_list.text if isinstance(span, Widget)]
        spans = [span for span in lien_list.text if isinstance(span, SpanPDF)]
        processed_widgets = set()
        updated_line = []

        for span in spans:
            was_span_modified = False
            for widget in widgets:
                if self._geometry_utils.get_intersection_rect(
                    span.rect, widget.rect
                ):
                    updated_line.append(
                        self._replace_text_in_span(span, widget)
                    )
                    processed_widgets.add(widget)
                    was_span_modified = True
                    break
            if not was_span_modified:
                updated_line.append(span)

        widgets = [
            widget for widget in widgets if widget not in processed_widgets
        ]
        updated_line += widgets

        return LinePDF(
            text=sorted(updated_line, key=lambda x: x.rect.x0),
            rect=lien_list.rect,
        )
