from typing import List

from fastapi import APIRouter, File, UploadFile, Request
from fastapi.params import Body

from src.core.config import settings
from src.core.constants import ALLOWED_MIME_TYPES_FOR_FORMS
from src.core.storage.shemas import FileDataSchema, FileDeleteSchema
from src.services.ai_service.ai_text_validator import OpenAITextAnalyzer
from src.services.check_pdf_fields import main_check_pdf_fields
from src.utils.validators.validate_file_mime import validate_file_mime

router_pdf_check = APIRouter(
    prefix="/api/v1/pdf-forms-check", tags=["Check PDF forms"]
)


@router_pdf_check.post(
    "/simple-check-pdf-forms",
    status_code=201,
    name="simple_check_pdf_forms",
    response_model=List[FileDataSchema],
    tags=["Check PDF forms"],
)
async def simple_check_pdf_forms(
    request: Request,
    files: List[UploadFile] = File(..., multiple=True),
) -> List[FileDataSchema]:
    checked_files: List[UploadFile] = await validate_file_mime(
        files, ALLOWED_MIME_TYPES_FOR_FORMS
    )

    uploaded = await settings.STORAGE(files=checked_files, request=request)

    if isinstance(uploaded, FileDataSchema):
        uploaded = [uploaded]

    return await main_check_pdf_fields(
        [str(file.path) for file in uploaded],
        ai_assistant=OpenAITextAnalyzer(),
        request=request,
    )


@router_pdf_check.delete(
    "/delete-file",
    status_code=200,
    name="delete_file",
    response_model=FileDeleteSchema,
    tags=["Check PDF forms"],
)
async def delete_file(
    request: Request, file_path=Body(..., embed=True)
) -> FileDeleteSchema:
    return await settings.STORAGE.delete(
        file_path=str(file_path), request=request
    )
