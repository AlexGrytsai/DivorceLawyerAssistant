from langchain_core.embeddings import Embeddings
from langchain_pinecone import PineconeVectorStore

from src.services.rag_service.factory import VectorStoreFactory


class PineconeVectorStoreFactory(VectorStoreFactory):
    def create_vector_store(
        self,
        index_name: str,
        namespace: str,
        embeddings: Embeddings,
    ) -> PineconeVectorStore:
        return PineconeVectorStore(
            index_name=index_name,
            embedding=embeddings,
            namespace=namespace,
        )
