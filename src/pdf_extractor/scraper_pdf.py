from abc import ABCMeta, abstractmethod

import fitz


class BaseScraperPDF(ABCMeta):
    __slots__ = ("_file_path",)
    _file_path: str

    @abstractmethod
    @property
    def file_path(self) -> str:
        return self._file_path


class ScraperPDF(BaseScraperPDF):
    @property
    def file_path(self) -> str:
        return self._file_path

    def _extract_text_from_page(self, page: fitz.Page) -> None:
        pass

    def _extract_widgets_from_page(self, page: fitz.Page) -> None:
        pass

    def scrap_data(self) -> None:
        doc: fitz.Document = fitz.open(self.file_path)
        for page in doc:
            self._extract_text_from_page(page)
            self._extract_widgets_from_page(page)
