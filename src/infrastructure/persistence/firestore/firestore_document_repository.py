import logging
import uuid
from enum import Enum
from typing import Optional, List, Any, Union

from dotenv import load_dotenv
from google.cloud.firestore import Client
from google.cloud.firestore_v1 import FieldFilter, DocumentSnapshot
from google.cloud.firestore_v1.stream_generator import StreamGenerator

from src.domain.document.entities import (
    DocumentDetail,
    Document,
    DocumentDelete,
)
from src.domain.document.exceptions import (
    DocumentNotFoundError,
    InvalidQueryParameterError,
    UnsupportedOperatorError,
    DocumentAlreadyExistsError,
)
from src.domain.document.repositories.document_repository import (
    DocumentRepository,
)
from src.domain.document.value_objects import SearchQuery
from src.infrastructure.persistence.firestore import (
    handle_firestore_database_errors_sync,
    handle_firestore_database_errors_async,
)

load_dotenv()

logger = logging.getLogger(__name__)


class SortDirection(str, Enum):
    ASCENDING = "ASCENDING"
    DESCENDING = "DESCENDING"


class FirestoreDocumentRepository(DocumentRepository):
    def __init__(self, project_id: str, database_name: str) -> None:
        self._project_id = project_id
        self._database = database_name
        self._client: Optional[Client] = None

    @property
    @handle_firestore_database_errors_sync
    def client(self) -> Client:
        if self._client is None:
            self._client = Client(
                project=self._project_id,  # type: ignore
                database=self._database,  # type: ignore
            )
        return self._client

    @handle_firestore_database_errors_async
    async def save(
        self,
        collection: str,
        document: DocumentDetail,
    ) -> str:
        is_exists = await self._find_document_by_name(
            collection=collection, document_name=document.name
        )

        if is_exists:
            raise DocumentAlreadyExistsError(
                f"Document '{document.name}' already exists"
            )

        self.client.collection(collection).document(
            document_id=str(uuid.uuid4())
        ).set(document.model_dump(), merge=True)

        return document.name

    @handle_firestore_database_errors_async
    async def get_document(
        self, collection: str, document_name: str, is_detail: bool = False
    ) -> Union[Document, DocumentDetail]:
        document: DocumentSnapshot = await self._find_document_by_name(
            collection, document_name
        )

        document_dict = document.to_dict()
        if document_dict:
            if is_detail:
                return DocumentDetail(**document_dict)

            return Document(**document_dict)

        logger.warning(f"Document '{document_name}' not found")
        raise DocumentNotFoundError(f"Document '{document_name}' not found")

    @handle_firestore_database_errors_async
    async def get_collection(
        self,
        collection: str,
        sort_direction: str = SortDirection.ASCENDING,
        limit: Optional[int] = None,
        order_by: str = "name",
        is_detail: bool = False,
    ) -> List[Union[Document, DocumentDetail]]:

        documents: StreamGenerator = await self._prepare_collection(
            collection=collection,
            order_by=order_by,
            limit=limit,
            sort_direction=sort_direction,
        )

        if is_detail:
            return [
                DocumentDetail(**document.to_dict()) for document in documents
            ]
        return [Document(**document.to_dict()) for document in documents]

    @handle_firestore_database_errors_async
    async def update(
        self,
        collection: str,
        document_name: str,
        updates: DocumentDetail,
    ) -> None:
        document: DocumentSnapshot = await self._find_document_by_name(
            collection, document_name
        )
        document.reference.update(updates.model_dump())

    @handle_firestore_database_errors_async
    async def delete(
        self, collection: str, document_name: str
    ) -> DocumentDelete:
        document: DocumentSnapshot = await self._find_document_by_name(
            collection, document_name
        )
        document.reference.delete()

        return DocumentDelete(name=document_name)

    @handle_firestore_database_errors_async
    async def filter(
        self,
        collection: str,
        field: str,
        operator: str,
        value: Any,
        limit: Optional[int] = None,
    ) -> List[DocumentDetail]:
        query = (
            self.client.collection(collection)
            .where(field, operator, value)
            .limit(limit)
        )

        return [
            DocumentDetail(**document.to_dict()) for document in query.stream()
        ]

    @handle_firestore_database_errors_async
    async def find(
        self,
        collection: str,
        query: List[SearchQuery],
        limit: Optional[int] = None,
        skip: Optional[int] = None,
    ) -> List[Document]:
        self._validate_query(query)

        query_ = self.client.collection(collection)

        for param in query:
            query_ = query_.where(
                filter=FieldFilter(param.field, param.operator, param.value)
            )
        if limit:
            query_ = query_.limit(limit)
        if skip:
            query_ = query_.offset(skip)
        return [Document(**document.to_dict()) for document in query_.stream()]

    @handle_firestore_database_errors_async
    async def _prepare_collection(
        self,
        collection: str,
        order_by: str = "name",
        limit: Optional[int] = None,
        sort_direction: str = SortDirection.ASCENDING,
    ) -> StreamGenerator:
        documents = self.client.collection(collection).order_by(
            order_by, direction=sort_direction
        )
        if limit:
            documents = documents.limit(limit)
        return documents.stream()

    @handle_firestore_database_errors_async
    async def _find_document_by_name(
        self, collection: str, document_name: str
    ) -> DocumentSnapshot:
        try:
            return next(
                (
                    self.client.collection(collection)
                    .where(filter=FieldFilter("name", "==", document_name))
                    .limit(1)
                    .stream()
                )
            )
        except StopIteration as exc:
            logger.warning(f"Document '{document_name}' not found")
            raise DocumentNotFoundError(
                f"Document '{document_name}' not found"
            ) from exc

    @staticmethod
    def _validate_query(query: List[SearchQuery]) -> bool:
        if not query:
            raise InvalidQueryParameterError(
                "Query parameters list cannot be empty"
            )

        valid_operators = {"==", "<", "<=", ">", ">=", "array_contains"}
        valid_fields = set(Document.model_fields.keys())

        for param in query:
            if param.field not in valid_fields:
                raise InvalidQueryParameterError(
                    f"Invalid field: {param.field}"
                )
            if param.operator not in valid_operators:
                raise UnsupportedOperatorError(
                    f"Unsupported operator: {param.operator}"
                )
            if not isinstance(param.value, (str, int, float, bool, list)):
                raise InvalidQueryParameterError(
                    f"Invalid value type for field {param.field}"
                )

        return True
