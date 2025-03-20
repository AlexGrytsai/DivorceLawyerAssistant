from typing import List

from fastapi import APIRouter, File, UploadFile, Request

from src.api.v1.check_pdf_forms.validate_file import validate_files
from src.core import settings
from src.core.storage.shemas import FileDataSchema
from src.services.ai_service.ai_text_validator import OpenAITextAnalyzer
from src.services.check_pdf_fields import main_check_pdf_fields

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
    checked_files: List[UploadFile] = await validate_files(files)

    uploaded = await settings.STORAGE(files=checked_files, request=request)

    checked_forms = await main_check_pdf_fields(
        [file.path for file in uploaded],
        ai_assistant=OpenAITextAnalyzer(),
        request=request,
    )

    return checked_forms
