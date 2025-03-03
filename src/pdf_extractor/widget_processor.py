from abc import ABC, abstractmethod

from src.pdf_extractor.geometry_utils import GeometryBaseUtils
from src.pdf_extractor.schemas import PagePDF


class WidgetBaseProcessor(ABC):
    def __init__(self, geometry_utils: GeometryBaseUtils) -> None:
        self._geometry_utils = geometry_utils

    @abstractmethod
    def add_widgets_to_lines_on_page(self, page: PagePDF) -> None:
        pass


class WidgetProcessor(WidgetBaseProcessor):
    def add_widgets_to_lines_on_page(self, page: PagePDF) -> None:
        for line in page.lines:
            for widget in page.widgets:
                if self._geometry_utils.is_same_line(
                    line.text[0].rect, widget.rect
                ):
                    line.text.append(widget)
            line.text.sort(key=lambda x: x.rect.x0)
