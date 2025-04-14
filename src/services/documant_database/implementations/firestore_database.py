from enum import Enum
from typing import Optional, Union, List, Any, Dict

from dotenv import load_dotenv
from google.cloud import firestore

from src.services.documant_database.decorators import (
    handle_firestore_database_errors,
)
from src.services.documant_database.exceptions import (
    DocumentNotFoundError,
)
from src.services.documant_database.interfaces import DocumentDatabase
from src.services.documant_database.schemas import (
    DocumentDetailSchema,
    DocumentSchema,
)

load_dotenv()


class SortDirection(str, Enum):
    ASCENDING = "ASCENDING"
    DESCENDING = "DESCENDING"


class FirestoreDatabase(DocumentDatabase):
    def __init__(self, project_id: str, database: str) -> None:
        self._project_id = project_id
        self._database = database
        self._client: Optional[firestore.Client] = None

    @property
    @handle_firestore_database_errors
    def client(self) -> firestore.Client:
        if self._client is None:
            self._client = firestore.Client(
                project=self._project_id,  # type: ignore
                database=self._database,  # type: ignore
            )
        return self._client

    @handle_firestore_database_errors
    async def save(
        self,
        collection: str,
        document: DocumentDetailSchema,
    ) -> str:
        self.client.collection(collection).document(document.name).set(
            document.model_dump(), merge=True
        )

        return document.name

    @handle_firestore_database_errors
    async def get_document(
        self, collection: str, document_id: str, is_detail: bool = False
    ) -> Union[DocumentSchema, DocumentDetailSchema]:
        document = (
            self.client.collection(collection).document(document_id).get()
        )
        if not document.exists:
            raise DocumentNotFoundError(f"Document '{document_id}' not found")

        if is_detail:
            return DocumentDetailSchema(**document.to_dict())

        return DocumentSchema(**document.to_dict())

    @handle_firestore_database_errors
    async def get_collection(
        self,
        collection: str,
        order_by: str = "name",
        limit: int = 0,
        sort_direction: SortDirection = SortDirection.ASCENDING,
        is_detail: bool = False,
    ) -> List[Union[DocumentSchema, DocumentDetailSchema]]:
        documents = (
            self.client.collection(collection)
            .order_by(order_by, direction=sort_direction)
            .limit(limit)
            .stream()
        )

        if is_detail:
            return [
                DocumentDetailSchema(**document.to_dict())
                for document in documents
            ]
        return [DocumentSchema(**document.to_dict()) for document in documents]

    @handle_firestore_database_errors
    async def update(
        self,
        collection: str,
        document_name: str,
        updates: DocumentDetailSchema,
    ) -> None:
        document = self.client.collection(collection).document(document_name)
        if not document.get().exists:
            raise DocumentNotFoundError(
                f"Document '{document_name}' not found"
            )
        document.update(updates.model_dump())

    @handle_firestore_database_errors
    async def delete(self, collection: str, document_id: str) -> None:
        document = self.client.collection(collection).document(document_id)
        if not document.get().exists:
            raise DocumentNotFoundError(f"Document '{document_id}' not found")
        document.delete()

    @handle_firestore_database_errors
    async def filter(
        self,
        collection: str,
        field: str,
        operator: str,
        value: Any,
        limit: int = 0,
    ) -> List[DocumentDetailSchema]:

        query = (
            self.client.collection(collection)
            .where(field, operator, value)
            .limit(limit)
        )

        return [
            DocumentDetailSchema(**document.to_dict())
            for document in query.stream()
        ]

    @handle_firestore_database_errors
    async def find(
        self,
        collection: str,
        query: Dict[str, Any],
        limit: Optional[int] = None,
        skip: Optional[int] = None,
    ) -> List[DocumentSchema]:
        query = self.client.collection(collection).where(**query)
        if limit:
            query = query.limit(limit)
        if skip:
            query = query.offset(skip)
        return [
            DocumentSchema(**document.to_dict()) for document in query.stream()
        ]
