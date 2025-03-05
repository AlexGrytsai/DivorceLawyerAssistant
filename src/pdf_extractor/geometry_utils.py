from abc import ABC, abstractmethod

import pymupdf as fitz


class GeometryBaseUtils(ABC):
    @staticmethod
    @abstractmethod
    def is_same_line(rect1: fitz.Rect, rect2: fitz.Rect, tolerance=5) -> bool:
        pass

    @staticmethod
    @abstractmethod
    def is_rect_inside(outer_rect: fitz.Rect, inner_rect: fitz.Rect) -> bool:
        pass

    @staticmethod
    @abstractmethod
    def is_partially_inside_rect(
        outer_rect: fitz.Rect, inner_rect: fitz.Rect
    ) -> bool:
        pass

    @staticmethod
    @abstractmethod
    def is_word_in_column(
        word_rect: fitz.Rect, column_rect: fitz.Rect
    ) -> bool:
        pass


class GeometryUtils(GeometryBaseUtils):
    @staticmethod
    def is_same_line(rect1: fitz.Rect, rect2: fitz.Rect, tolerance=5) -> bool:
        return (
            abs(rect1.y0 - rect2.y0) < tolerance
            or abs(rect1.y1 - rect2.y1) < tolerance
        )

    @staticmethod
    def is_rect_inside(
        outer_rect: fitz.Rect,
        inner_rect: fitz.Rect,
        tolerance=5,
    ) -> bool:
        return (
            outer_rect.x0 - tolerance
            <= inner_rect.x0
            <= outer_rect.x1 + tolerance
            and outer_rect.y0 - tolerance
            <= inner_rect.y0
            <= outer_rect.y1 + tolerance
            and outer_rect.x0 - tolerance
            <= inner_rect.x1
            <= outer_rect.x1 + tolerance
            and outer_rect.y0 - tolerance
            <= inner_rect.y1
            <= outer_rect.y1 + tolerance
        )

    @staticmethod
    def is_partially_inside_rect(
        outer_rect: fitz.Rect,
        inner_rect: fitz.Rect,
    ) -> bool:
        return (
            outer_rect.x0 <= inner_rect.x0
            and outer_rect.x1 >= inner_rect.x1
            and outer_rect.y1 >= inner_rect.y1
        )

    @staticmethod
    def is_word_in_column(
        word_rect: fitz.Rect,
        column_rect: fitz.Rect,
    ) -> bool:
        return column_rect.x0 <= word_rect.x0 <= column_rect.x1
