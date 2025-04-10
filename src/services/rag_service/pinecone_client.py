import logging
from typing import Dict, List, Optional, Any

from fastapi import HTTPException, status
from pinecone import Pinecone, ServerlessSpec

from src.core.config import settings
from src.services.rag_service.decorators import (
    handle_pinecone_init_exceptions,
    handle_boolean_operation_exceptions,
    handle_list_operation_exceptions,
    handle_dict_operation_exceptions,
    handle_index_stats_exceptions,
)
from src.services.rag_service.interfaces import (
    VectorDBInterface,
)
from src.services.rag_service.schemas import (
    PineconeIndexStatsSchema,
    PineconeNamespaceStatsSchema,
)

logger = logging.getLogger(__name__)


class PineconeVectorDataBase(VectorDBInterface):
    @handle_pinecone_init_exceptions
    def __init__(self, vector_db_client: Optional[Pinecone] = None):
        self.client = (
            vector_db_client or settings.VECTOR_DATABASE_DEFAULT_CLIENT
        )

    @handle_boolean_operation_exceptions
    def create_index(
        self,
        name: str,
        dimension: int = settings.DIMENSIONS_EMBEDDING,
        vector_type: str = "dense",
        metric: str = "cosine",
        cloud: str = "aws",
        region: str = "us-east-1",
        **kwargs,
    ) -> bool:
        if name in set(self.list_indexes()):
            logger.warning(f"Index {name} already exists")

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "Index already exists",
                    "message": f"Index '{name}' already exists",
                },
            )

        spec = ServerlessSpec(cloud=cloud, region=region)
        self.client.create_index(
            name=name,
            dimension=dimension,
            vector_type=vector_type,
            metric=metric,
            spec=spec,
            **kwargs,
        )

        # Wait for index to be ready
        is_ready = False
        while not is_ready:
            try:
                status_ = self.client.describe_index(name).status
                is_ready = status_.get("ready", False)
            except Exception as exc:
                logger.warning(f"Error checking index status: {exc}")

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error": "Unexpected error",
                        "message": f"Error checking index status: {exc}",
                    },
                ) from exc

        return True

    @handle_boolean_operation_exceptions
    def delete_index(self, name: str) -> bool:
        if name not in set(self.list_indexes()):
            logger.warning(f"Index {name} does not exist")

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "Index does not exist",
                    "message": f"Index {name} does not exist",
                },
            )

        self.client.delete_index(name)
        return True

    @handle_list_operation_exceptions
    def list_indexes(self) -> List[str]:
        response = self.client.list_indexes()
        return response.names()

    @handle_dict_operation_exceptions
    def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        index = self.client.Index(index_name)
        return index.describe_index_stats()

    @handle_index_stats_exceptions
    def get_index_stats_schema(
        self, index_name: str
    ) -> PineconeIndexStatsSchema:
        stats = self.get_index_stats(index_name)

        namespaces = {}
        if "namespaces" in stats:
            for ns_name, ns_data in stats["namespaces"].items():
                namespaces[ns_name] = PineconeNamespaceStatsSchema(
                    vector_count=ns_data.get("vector_count", 0)
                )

        return PineconeIndexStatsSchema(
            namespaces=namespaces,
            dimension=stats.get("dimension", settings.DIMENSIONS_EMBEDDING),
            index_fullness=stats.get("index_fullness", 0.0),
            total_vector_count=stats.get("total_vector_count", 0),
        )

    @handle_boolean_operation_exceptions
    def delete_from_namespace(
        self,
        index_name: str,
        namespace: str,
        ids: Optional[List[str]] = None,
        delete_all: bool = False,
        filter_: Optional[Dict[str, Any]] = None,
    ) -> bool:
        index = self.client.Index(index_name)

        if delete_all:
            index.delete(delete_all=True, namespace=namespace)
        elif ids:
            index.delete(ids=ids, namespace=namespace)
        elif filter_:
            index.delete(filter=filter_, namespace=namespace)
        else:
            logger.warning("No deletion criteria provided")

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No deletion criteria provided",
            )

        return True

    @handle_list_operation_exceptions
    def list_namespaces(self, index_name: str) -> List[str]:
        stats = self.get_index_stats(index_name)
        return list(stats.get("namespaces", {}).keys())
