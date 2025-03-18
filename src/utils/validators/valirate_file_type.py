import magic

ALLOWED_MIME_TYPES_FOR_FORMS = (
    "application/pdf",
    "application/msword",  # .doc
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
)


def get_real_mime_type(file: bytes) -> str:
    mime = magic.Magic(mime=True)
    return mime.from_buffer(file)


def is_allowed_mime_type_for_forms(file_bytes: bytes) -> bool:
    real_mime = get_real_mime_type(file_bytes)
    return real_mime in ALLOWED_MIME_TYPES_FOR_FORMS
