from abc import ABC, abstractmethod

from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore


class VectorStoreFactory(ABC):
    """
    Abstract base class for creating vector stores.

    This class provides a blueprint for creating vector stores, which are
    used to store and manage vector embeddings.
    """

    @abstractmethod
    def create_vector_store(
        self,
        index_name: str,
        namespace: str,
        embeddings: Embeddings,
    ) -> VectorStore:
        """
        Creates a new vector store.

        Args:
            index_name (str): The name of the index.
            namespace (str): The namespace for the vector store.
            embeddings (Embeddings): The embeddings to be stored in
                                     the vector store.

        Returns:
            VectorStore: The created vector store.

        Raises:
            NotImplementedError: If this method is not implemented by
                                 a subclass.
        """
        pass
