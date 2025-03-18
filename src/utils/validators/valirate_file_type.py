import magic
from fastapi import UploadFile

ALLOWED_MIME_TYPES_FOR_FORMS = (
    "application/pdf",
    "application/msword",  # .doc
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
)


def get_real_mime_type(file: bytes) -> str:
    mime = magic.Magic(mime=True)
    return mime.from_buffer(file)


async def is_allowed_mime_type_for_forms(file: UploadFile) -> bool:
    file_bytes = await file.read()

    return get_real_mime_type(file_bytes) in ALLOWED_MIME_TYPES_FOR_FORMS
