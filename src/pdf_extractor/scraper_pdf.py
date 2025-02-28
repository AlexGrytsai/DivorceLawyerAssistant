from abc import ABCMeta, abstractmethod


class BaseScraperPDF(ABCMeta):
    _file_path: str

    @abstractmethod
    @property
    def file_path(self) -> str:
        return self._file_path


class ScraperPDF(BaseScraperPDF):
    @property
    def file_path(self) -> str:
        return self._file_path
