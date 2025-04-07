from fastapi import HTTPException, status
from pydantic import BaseModel, field_validator


class KnowledgeBaseSchema(BaseModel):
    name_knowledge_base: str

    @field_validator("name_knowledge_base")
    def validate_name_knowledge_base(cls, value: str) -> str:
        if not value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "'name_knowledge_base' must not be empty",
                    "message": "'name_knowledge_base' must not be empty",
                },
            )
        if "/" in value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "'name_knowledge_base' cannot contain "
                    "path separators ('/')",
                    "message": "'name_knowledge_base' cannot contain "
                    "path separators ('/')",
                },
            )
        return value


class KnowledgeBaseCreateSchema(KnowledgeBaseSchema):
    create_time: str


class KnowledgeBaseGetSchema(KnowledgeBaseCreateSchema):
    update_time: str
