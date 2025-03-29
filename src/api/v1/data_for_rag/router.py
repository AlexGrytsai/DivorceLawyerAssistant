from typing import List, Optional

from fastapi import APIRouter, UploadFile, Request, File, Form

from src.core.config import settings
from src.core.storage.shemas import (
    FileDataSchema,
    FileDeleteSchema,
    FolderDataSchema,
    FolderDeleteSchema,
)


router = APIRouter(prefix="/api/v1/data-for-rag", tags=["Data for RAG"])


@router.get(
    "/files-in-folder/{folder_path:path}",
    status_code=200,
)
async def list_folder_contents(folder_path: str = ""):
    blobs = settings.RAG_STORAGE.list_blobs(prefix=folder_path)

    files = []
    folders = []

    for blob in blobs:
        name = blob.name
        if name == folder_path:
            continue

        relative_path = name[len(folder_path) :].lstrip("/")
        if not relative_path:
            continue

        parts = relative_path.split("/")
        if len(parts) == 1:
            files.append(
                {
                    "name": parts[0],
                    "path": name,
                    "size": blob.size,
                    "updated": (
                        blob.updated.isoformat() if blob.updated else None
                    ),
                    "type": "file",
                }
            )
        else:
            folder_path = (
                f"{folder_path}/{parts[0]}" if folder_path else parts[0]
            )
            if folder_path not in [f["path"] for f in folders]:
                folders.append(
                    {"name": parts[0], "path": folder_path, "type": "folder"}
                )

    return {
        "current_path": folder_path,
        "items": sorted(
            folders + files, key=lambda x: (x["type"] == "file", x["name"])
        ),
    }


@router.post("/upload", response_model=FileDataSchema)
async def upload_file(
    file: UploadFile = File(...),
    folder_path: Optional[str] = Form(None),
    request: Request = None,
):
    """Загрузка одного файла"""
    if folder_path:
        file.filename = f"{folder_path.rstrip('/')}/{file.filename}"
    return await settings.RAG_STORAGE.upload(file, request)


@router.post("/upload/multiple", response_model=List[FileDataSchema])
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    folder_path: Optional[str] = Form(None),
    request: Request = None,
):
    """Загрузка нескольких файлов"""
    return await settings.RAG_STORAGE.multi_upload(files, request)


@router.delete("/files/{file_path:path}", response_model=FileDeleteSchema)
async def delete_file(
    file_path: str,
    request: Request = None,
):
    """Удаление файла"""
    return await settings.RAG_STORAGE.delete(file_path, request)


@router.post("/folders", response_model=FolderDataSchema)
async def create_folder(
    folder_path: str = Form(...),
    request: Request = None,
):
    """Создание новой папки"""
    return await settings.RAG_STORAGE.create_folder(folder_path, request)


@router.put("/folders/{folder_path:path}", response_model=FolderDataSchema)
async def rename_folder(
    folder_path: str,
    new_path: str = Form(...),
    request: Request = None,
):
    """Переименование папки"""
    return await settings.RAG_STORAGE.rename_folder(folder_path, new_path, request)


@router.delete(
    "/folders/{folder_path:path}", response_model=FolderDeleteSchema
)
async def delete_folder(
    folder_path: str,
    request: Request = None,
):
    """Удаление папки"""
    return await settings.RAG_STORAGE.delete_folder(folder_path, request)


@router.put("/files/{file_path:path}", response_model=FileDataSchema)
async def rename_file(
    file_path: str,
    new_path: str = Form(...),
    request: Request = None,
):
    """Переименование файла"""
    return await settings.RAG_STORAGE.rename_file(file_path, new_path, request)


@router.get("/files/{file_path:path}")
async def get_file(
    file_path: str,
):
    """Получить файл по пути"""
    return await settings.RAG_STORAGE.get_file(file_path)


@router.get("/files")
async def list_files(
    prefix: Optional[str] = None,
):
    """Получить список всех файлов"""
    return await settings.RAG_STORAGE.list_files(prefix)


@router.get("/folders")
async def list_folders(
    prefix: Optional[str] = None,
):
    """Получить список всех папок"""
    return await settings.RAG_STORAGE.list_folders(prefix)


@router.get("/folder/{folder_path:path}")
async def get_folder_contents(
    folder_path: str,
):
    """Получить содержимое конкретной папки"""
    return await settings.RAG_STORAGE.get_folder_contents(folder_path)
