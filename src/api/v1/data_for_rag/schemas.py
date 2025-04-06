from fastapi import HTTPException, status
from pydantic import BaseModel, field_validator


class IndexRAGSchema(BaseModel):
    name_index: str

    @field_validator("name_index")
    def validate_name_index(cls, value: str) -> str:
        if not value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "'name_index' must not be empty",
                    "message": "'name_index' must not be empty",
                },
            )
        if "/" in value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "'name_index' cannot contain path separators ('/')",
                    "message": "'name_index' cannot contain path separators ('/')",
                },
            )
        return value


class IndexCreateSchema(IndexRAGSchema):
    create_time: str
