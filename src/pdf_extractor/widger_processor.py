from abc import ABC, abstractmethod
from typing import Optional

import pymupdf as fitz  # type: ignore
from pymupdf import Widget  # type: ignore

from src.pdf_extractor.geometry_utils import GeometryBaseUtils
from src.pdf_extractor.schemas import SpanPDF, LinePDF


class WidgetSpanBaseProcessor(ABC):
    def __init__(self, geometry_utils: GeometryBaseUtils) -> None:
        self._geometry_utils = geometry_utils

    @staticmethod
    @abstractmethod
    def get_widget_value(widget: fitz.Widget) -> Optional[str]:
        pass

    @abstractmethod
    def handle_widget_span_intersections(
        self,
        lien_list: LinePDF,
    ) -> LinePDF:
        pass


class WidgetSpanProcessor(WidgetSpanBaseProcessor):

    @staticmethod
    def get_widget_value(widget: fitz.Widget) -> Optional[str]:
        if widget.field_type_string in ("Text", "ComboBox"):
            return widget.field_value if widget.field_value else f"{'_' * 10} "
        elif widget.field_type_string == "CheckBox":
            return "[ON]" if widget.field_value else "[OFF]"
        return None

    def _replace_text_in_span(
        self,
        target_span: SpanPDF,
        replacement_span: fitz.Widget,
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
            text_before = target_span.text[:start_index]
            text_after = target_span.text[end_index:]

            target_span.text = (
                f"{text_before} "
                f"{self.get_widget_value(replacement_span)} {text_after}"
            )

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
