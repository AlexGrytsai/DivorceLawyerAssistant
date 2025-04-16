from typing import List, Optional

from fastapi import APIRouter, UploadFile, Request, File, Form, Body

from src.core.config import settings
from src.core.constants import ALLOWED_MIME_TYPES_FOR_RAG
from src.interfaces.api.v1.data_for_rag.schemas import (
    KnowledgeBaseSchema,
    KnowledgeBaseCreateSchema,
    KnowledgeBaseGetSchema,
)
from src.services.storage.shemas import (
    FileSchema,
    FileDeleteSchema,
    FolderDataSchema,
    FolderContentsSchema,
    FolderDeleteSchema,
)
from src.utils.validators.validate_file_mime import validate_file_mime

router = APIRouter(prefix="/api/v1/knowledge-base", tags=["Knowledge Base"])


def _process_file_path(
    file: UploadFile, folder_path: Optional[str] = None
) -> None:
    if folder_path:
        original_filename = file.filename
        file.filename = f"{folder_path.rstrip('/')}/{original_filename}"


@router.post(
    "/", response_model=KnowledgeBaseCreateSchema, tags=["Knowledge Base"]
)
async def create_new_knowledge_base(
    request: Request, name_knowledge_base: KnowledgeBaseSchema = Body(...)
):
    """
    Creates a new knowledge base for RAG (Retrieval-Augmented Generation).

    The knowledge base represents a new index in the vector database, which
    will be used for retrieving relevant documents during response generation.
    The process of creating a knowledge base includes:
    - Creating a new index in the vector database
    - Initializing storage structure for documents
    - Generating a unique knowledge base identifier
    """
    base = await settings.RAG_STORAGE.create_folder(
        name_knowledge_base.name_knowledge_base, request
    )
    return KnowledgeBaseCreateSchema(
        name_knowledge_base=name_knowledge_base.name_knowledge_base,
        create_time=base.create_time,
    )


@router.get(
    "/{name_knowledge_base}",
    response_model=KnowledgeBaseGetSchema,
    tags=["Knowledge Base"],
)
async def get_knowledge_base(request: Request):
    pass


@router.put(
    "/", response_model=KnowledgeBaseCreateSchema, tags=["Knowledge Base"]
)
async def rename_knowledge_base(
    request: Request, name_knowledge_base: KnowledgeBaseSchema = Body(...)
):
    pass


@router.delete(
    "/", response_model=KnowledgeBaseCreateSchema, tags=["Knowledge Base"]
)
async def delete_knowledge_base(
    request: Request, name_knowledge_base: KnowledgeBaseSchema = Body(...)
):
    pass


@router.get(
    "/files/{file_path:path}",
    response_model=FileSchema,
    tags=["RAG Files"],
)
async def get_file(
    file_path: str,
):
    """Get file details by path"""
    return await settings.RAG_STORAGE.get_file(file_path)


@router.get("/files", response_model=List[FileSchema], tags=["RAG Files"])
async def list_files(
    prefix: Optional[str] = "",
    search_query: Optional[str] = "",
    case_sensitive: Optional[bool] = False,
):
    """List all files in storage with optional prefix filter"""
    return await settings.RAG_STORAGE.list_files(
        prefix,
        search_query,
        case_sensitive,
    )


@router.post("/upload", response_model=FileSchema, tags=["RAG Files"])
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    folder_path: Optional[str] = Form(None),
):
    """Upload a single file to storage"""
    _process_file_path(file, folder_path)
    return await settings.RAG_STORAGE.upload(file, request)


@router.post(
    "/upload/multiple",
    response_model=List[FileSchema],
    tags=["RAG Files"],
)
async def upload_multiple_files(
    request: Request,
    files: List[UploadFile] = File(...),
    folder_path: Optional[str] = Form(None),
):
    """Upload multiple files to storage"""
    for file in files:
        _process_file_path(file, folder_path)

    checked_files: List[UploadFile] = await validate_file_mime(
        files, ALLOWED_MIME_TYPES_FOR_RAG
    )
    return await settings.RAG_STORAGE.multi_upload(checked_files, request)


@router.put(
    "/files/{file_path:path}",
    response_model=FileSchema,
    tags=["RAG Files"],
)
async def rename_file(
    file_path: str,
    request: Request,
    new_file_name: str = Form(...),
):
    """Rename a file in storage"""
    return await settings.RAG_STORAGE.rename_file(
        file_path, new_file_name, request
    )


@router.delete(
    "/files/{file_path:path}",
    response_model=FileDeleteSchema,
    tags=["RAG Files"],
)
async def delete_file(
    file_path: str,
    request: Request,
):
    """Delete a file from storage"""
    return await settings.RAG_STORAGE.delete_file(file_path, request)


@router.get(
    "/folders",
    response_model=List[FolderDataSchema],
    tags=["RAG Folders"],
)
async def list_folders(
    prefix: Optional[str] = None,
):
    """List folders with optional prefix filter"""
    return await settings.RAG_STORAGE.list_folders(prefix)


@router.get(
    "/folder/{folder_path:path}",
    response_model=FolderContentsSchema,
    tags=["RAG Folders"],
)
async def get_folder_contents(
    folder_path: str,
):
    """Get contents of a specific folder"""
    return await settings.RAG_STORAGE.get_folder_contents(folder_path)


@router.get(
    "/files-in-folder/{folder_path:path}",
    status_code=200,
    tags=["RAG Folders"],
)
async def list_folder_contents(folder_path: str = ""):
    """List contents of a specific folder"""
    return await settings.RAG_STORAGE.get_folder_contents(folder_path)


@router.post(
    "/folders",
    response_model=FolderDataSchema,
    tags=["RAG Folders"],
)
async def create_folder(
    request: Request,
    folder_path: str = Form(...),
):
    """Create a new folder in storage"""
    return await settings.RAG_STORAGE.create_folder(folder_path, request)


@router.put(
    "/folders/{folder_path:path}",
    response_model=FolderDataSchema,
    tags=["RAG Folders"],
)
async def rename_folder(
    folder_path: str,
    request: Request,
    new_path: str = Form(...),
):
    """Rename a folder in storage"""
    return await settings.RAG_STORAGE.rename_folder(
        folder_path, new_path, request
    )


@router.delete(
    "/folders/{folder_path:path}",
    response_model=FolderDeleteSchema,
    tags=["RAG Folders"],
)
async def delete_folder(
    folder_path: str,
    request: Request,
):
    """Delete a folder and its contents from storage"""
    return await settings.RAG_STORAGE.delete_folder(folder_path, request)
