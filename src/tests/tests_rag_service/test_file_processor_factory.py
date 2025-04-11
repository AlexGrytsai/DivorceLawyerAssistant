from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.services.rag_service.factory.file_processor_factory import FileProcessorFactory
from src.services.rag_service.interfaces import FileProcessorInterface


class MockProcessor(FileProcessorInterface):
    async def process_file(self, file_path: str, index_name: str, namespace: str, metadata=None):
        pass


@pytest.fixture
def factory():
    return FileProcessorFactory()


@pytest.fixture
def mock_processor():
    return MockProcessor()


def test_initialization(factory):
    assert factory._processors is not None
    assert "pdf" in factory._processors


def test_register_processor(factory, mock_processor):
    factory.register_processor("txt", MockProcessor)
    assert "txt" in factory._processors
    assert factory._processors["txt"] == MockProcessor


def test_register_processor_case_insensitive(factory, mock_processor):
    factory.register_processor("TXT", MockProcessor)
    assert "txt" in factory._processors
    assert factory._processors["txt"] == MockProcessor


def test_register_processor_overwrite(factory, mock_processor):
    factory.register_processor("txt", MockProcessor)
    factory.register_processor("txt", MockProcessor)
    assert "txt" in factory._processors
    assert factory._processors["txt"] == MockProcessor


def test_get_processor_success(factory):
    processor = factory.get_processor("test.pdf")
    assert processor is not None


def test_get_processor_case_insensitive(factory):
    processor = factory.get_processor("test.PDF")
    assert processor is not None


def test_get_processor_unsupported_type(factory):
    with pytest.raises(HTTPException) as exc_info:
        factory.get_processor("test.unsupported")
    
    assert exc_info.value.status_code == 415
    assert "Unsupported file type" in str(exc_info.value.detail)


def test_get_processor_no_extension(factory):
    with pytest.raises(HTTPException) as exc_info:
        factory.get_processor("test")
    
    assert exc_info.value.status_code == 415
    assert "Unsupported file type" in str(exc_info.value.detail)
