import logging
import os
from typing import Dict, List, Optional, Any

from pinecone import Pinecone, ServerlessSpec

from src.services.rag_service.exceptions import (
    ErrorWithInitializationVectorDBClient,
)
from src.services.rag_service.schemas import (
    PineconeIndexStatsSchema,
    PineconeNamespaceStatsSchema,
)
from src.services.rag_service.vector_db_interface import VectorDBInterface

logger = logging.getLogger(__name__)


class PineconeClient(VectorDBInterface):
    def __init__(self, vector_db_client: Optional[Pinecone] = None):
        try:
            self.client = vector_db_client or Pinecone(
                api_key=os.environ.get("PINECONE_API_KEY")
            )
        except Exception as exc:
            logger.error(
                f"Error initializing Pinecone client: {exc}", exc_info=True
            )
            raise ErrorWithInitializationVectorDBClient(
                f"Error initializing Pinecone client: {exc}"
            ) from exc

    def create_index(
        self,
        name: str,
        dimension: int = 1024,
        vector_type: str = "dense",
        metric: str = "cosine",
        cloud: str = "aws",
        region: str = "us-east-1",
        **kwargs,
    ) -> bool:
        try:
            if name in set(self.list_indexes()):
                logger.warning(f"Index {name} already exists")
                return False

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
                    status = self.client.describe_index(name).status
                    is_ready = status.get("ready", False)
                except Exception as e:
                    logger.warning(f"Error checking index status: {e}")
                    break

            return True
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            return False

    def delete_index(self, name: str) -> bool:
        try:
            if name not in set(self.list_indexes()):
                logger.warning(f"Index {name} does not exist")
                return False

            self.client.delete_index(name)
            return True
        except Exception as e:
            logger.error(f"Error deleting index: {e}")
            return False

    def list_indexes(self) -> List[str]:
        try:
            response = self.client.list_indexes()
            return response.names()
        except Exception as e:
            logger.error(f"Error listing indexes: {e}")
            return []

    def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        """Returns the statistics of the index in the form of a dictionary"""
        try:
            index = self.client.Index(index_name)
            return index.describe_index_stats()
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {}

    def get_index_stats_schema(
        self, index_name: str
    ) -> PineconeIndexStatsSchema:
        """
        Returns the statistics of the index in the form of a Pydantic model
        """
        try:
            stats = self.get_index_stats(index_name)

            namespaces = {}
            if "namespaces" in stats:
                for ns_name, ns_data in stats["namespaces"].items():
                    namespaces[ns_name] = PineconeNamespaceStatsSchema(
                        vector_count=ns_data.get("vector_count", 0)
                    )

            return PineconeIndexStatsSchema(
                namespaces=namespaces,
                dimension=stats.get("dimension", 1024),
                index_fullness=stats.get("index_fullness", 0.0),
                total_vector_count=stats.get("total_vector_count", 0),
            )
        except Exception as e:
            logger.error(f"Error converting index stats to schema: {e}")
            return PineconeIndexStatsSchema()

    def delete_from_namespace(
        self,
        index_name: str,
        namespace: str,
        ids: Optional[List[str]] = None,
        delete_all: bool = False,
        filter_: Optional[Dict[str, Any]] = None,
    ) -> bool:
        try:
            index = self.client.Index(index_name)

            if delete_all:
                index.delete(delete_all=True, namespace=namespace)
            elif ids:
                index.delete(ids=ids, namespace=namespace)
            elif filter_:
                index.delete(filter=filter_, namespace=namespace)
            else:
                logger.warning("No deletion criteria provided")
                return False

            return True
        except Exception as e:
            logger.error(f"Error deleting from namespace: {e}")
            return False

    def list_namespaces(self, index_name: str) -> List[str]:
        try:
            stats = self.get_index_stats(index_name)
            return list(stats.get("namespaces", {}).keys())
        except Exception as e:
            logger.error(f"Error listing namespaces: {e}")
            return []
