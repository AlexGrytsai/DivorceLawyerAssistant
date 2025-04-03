from typing import List, Optional

from fastapi import APIRouter, UploadFile, Request, File, Form

from src.core.config import settings
from src.core.constants import ALLOWED_MIME_TYPES_FOR_RAG
from src.core.storage.shemas import (
    FileDataSchema,
    FileDeleteSchema,
    FolderBaseSchema,
    FolderDeleteSchema,
)
from src.utils.validators.validate_file_mime import validate_file_mime

router = APIRouter(prefix="/api/v1/data-for-rag", tags=["Data for RAG"])


def _process_file_path(
    file: UploadFile, folder_path: Optional[str] = None
) -> None:
    if folder_path:
        original_filename = file.filename
        file.filename = f"{folder_path.rstrip('/')}/{original_filename}"


@router.get(
    "/files-in-folder/{folder_path:path}",
    status_code=200,
)
async def list_folder_contents(folder_path: str = ""):
    """List contents of a specific folder"""
    return await settings.RAG_STORAGE.get_folder_contents(folder_path)


@router.post("/upload", response_model=FileDataSchema)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    folder_path: Optional[str] = Form(None),
):
    """Upload a single file to storage"""
    _process_file_path(file, folder_path)
    return await settings.RAG_STORAGE.upload(file, request)


@router.post("/upload/multiple", response_model=List[FileDataSchema])
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


@router.delete("/files/{file_path:path}", response_model=FileDeleteSchema)
async def delete_file(
    file_path: str,
    request: Request,
):
    """Delete a file from storage"""
    return await settings.RAG_STORAGE.delete(file_path, request)


@router.post("/folders", response_model=FolderBaseSchema)
async def create_folder(
    request: Request,
    folder_path: str = Form(...),
):
    """Create a new folder in storage"""
    return await settings.RAG_STORAGE.create_folder(folder_path, request)


@router.put("/folders/{folder_path:path}", response_model=FolderBaseSchema)
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
    "/folders/{folder_path:path}", response_model=FolderDeleteSchema
)
async def delete_folder(
    folder_path: str,
    request: Request,
):
    """Delete a folder and its contents from storage"""
    return await settings.RAG_STORAGE.delete_folder(folder_path, request)


@router.put("/files/{file_path:path}", response_model=FileDataSchema)
async def rename_file(
    file_path: str,
    request: Request,
    new_path: str = Form(...),
):
    """Rename a file in storage"""
    return await settings.RAG_STORAGE.rename_file(file_path, new_path, request)


@router.get("/files/{file_path:path}")
async def get_file(
    file_path: str,
):
    """Get file details by path"""
    return await settings.RAG_STORAGE.get_file(file_path)


@router.get("/files")
async def list_files(
    prefix: Optional[str] = None,
):
    """List all files in storage with optional prefix filter"""
    return await settings.RAG_STORAGE.list_files(prefix)


@router.get("/folders")
async def list_folders(
    prefix: Optional[str] = None,
):
    """List folders with optional prefix filter"""
    return await settings.RAG_STORAGE.list_folders(prefix)


@router.get("/folder/{folder_path:path}")
async def get_folder_contents(
    folder_path: str,
):
    """Get contents of a specific folder"""
    return await settings.RAG_STORAGE.get_folder_contents(folder_path)


@router.get("/search-files")
async def search_files(
    query: str,
    case_sensitive: bool = False,
):
    """Search files by name with optional case sensitivity"""
    return await settings.RAG_STORAGE.search_files_by_name(
        query, case_sensitive
    )
