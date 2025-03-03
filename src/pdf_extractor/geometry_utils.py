from abc import ABC, abstractmethod

import pymupdf as fitz


class GeometryBaseUtils(ABC):
    @staticmethod
    @abstractmethod
    def is_same_line(rect1: fitz.Rect, rect2: fitz.Rect, tolerance=5):
        pass


class GeometryUtils(GeometryBaseUtils):
    @staticmethod
    def is_same_line(rect1: fitz.Rect, rect2: fitz.Rect, tolerance=5):
        return (
            abs(rect1.y0 - rect2.y0) < tolerance
            or abs(rect1.y1 - rect2.y1) < tolerance
        )
