
import abc
import threading
from pathlib import Path
from typing import Any

from llama_index.core.data_structs import IndexDict
from llama_index.core.embeddings.utils import EmbedType
from llama_index.core.indices import VectorStoreIndex, load_index_from_storage
from llama_index.core.indices.base import BaseIndex
from llama_index.core.schema import Document, TransformComponent
from llama_index.core.storage import StorageContext

from app.api.ingest.ingest_helper import IngestionHelper
from app.constants import get_local_data_path
from app.api.settings.settings import Settings


class BaseIngestComponent(abc.ABC):
    def __init__(
        self,
        storage_context: StorageContext,
        embed_model: EmbedType,
        transformations: list[TransformComponent],
        *args: Any,
        **kwargs: Any,
    ) -> None:

        self.storage_context = storage_context
        self.embed_model = embed_model
        self.transformations = transformations

    @abc.abstractmethod
    def ingest(self, file_name: str, file_data: Path) -> list[Document]:
        pass

    @abc.abstractmethod
    def bulk_ingest(self, files: list[tuple[str, Path]]) -> list[Document]:
        pass

    @abc.abstractmethod
    def delete(self, doc_id: str) -> None:
        pass


class BaseIngestComponentWithIndex(BaseIngestComponent, abc.ABC):
    def __init__(
        self,
        storage_context: StorageContext,
        embed_model: EmbedType,
        transformations: list[TransformComponent],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(storage_context, embed_model, transformations, *args, **kwargs)

        self.show_progress = True
        self._index_thread_lock = (
            threading.Lock()
        )  # Thread lock! Not Multiprocessing lock
        self._index = self._initialize_index()

    def _initialize_index(self) -> BaseIndex[IndexDict]:
        """Initialize the index from the storage context."""
        try:
            # Load the index with store_nodes_override=True to be able to delete them
            index = load_index_from_storage(
                storage_context=self.storage_context,
                store_nodes_override=True,  # Force store nodes in index and document stores
                show_progress=self.show_progress,
                embed_model=self.embed_model,
                transformations=self.transformations,
            )
        except ValueError:

            index = VectorStoreIndex.from_documents(
                [],
                storage_context=self.storage_context,
                store_nodes_override=True,  # Force store nodes in index and document stores
                show_progress=self.show_progress,
                embed_model=self.embed_model,
                transformations=self.transformations,
            )
            index.storage_context.persist(persist_dir=get_local_data_path())
        return index

    def _save_index(self) -> None:
        self._index.storage_context.persist(persist_dir=get_local_data_path())

    def delete(self, doc_id: str) -> None:
        with self._index_thread_lock:
            # Delete the document from the index
            self._index.delete_ref_doc(doc_id, delete_from_docstore=True)

            # Save the index
            self._save_index()


class SimpleIngestComponent(BaseIngestComponentWithIndex):
    def __init__(
        self,
        storage_context: StorageContext,
        embed_model: EmbedType,
        transformations: list[TransformComponent],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(storage_context, embed_model, transformations, *args, **kwargs)

    def ingest(self, file_name: str, file_data: Path) -> list[Document]:

        documents = IngestionHelper.transform_file_into_documents(file_name, file_data)

        return self._save_docs(documents)

    def bulk_ingest(self, files: list[tuple[str, Path]]) -> list[Document]:
        saved_documents = []
        for file_name, file_data in files:
            documents = IngestionHelper.transform_file_into_documents(
                file_name, file_data
            )
            saved_documents.extend(self._save_docs(documents))
        return saved_documents

    def _save_docs(self, documents: list[Document]) -> list[Document]:

        with self._index_thread_lock:
            for document in documents:
                self._index.insert(document)

            # persist the index and nodes
            self._save_index()

        return documents



class BaseIngestComponentWithIndex(BaseIngestComponent, abc.ABC):
    def __init__(
        self,
        storage_context: StorageContext,
        embed_model: EmbedType,
        transformations: list[TransformComponent],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(storage_context, embed_model, transformations, *args, **kwargs)

        self.show_progress = True
        self._index_thread_lock = (
            threading.Lock()
        )  # Thread lock! Not Multiprocessing lock
        self._index = self._initialize_index()

    def _initialize_index(self) -> BaseIndex[IndexDict]:
        """Initialize the index from the storage context."""
        try:
            # Load the index with store_nodes_override=True to be able to delete them
            index = load_index_from_storage(
                storage_context=self.storage_context,
                store_nodes_override=True,  # Force store nodes in index and document stores
                show_progress=self.show_progress,
                embed_model=self.embed_model,
                transformations=self.transformations,
            )
        except ValueError:

            index = VectorStoreIndex.from_documents(
                [],
                storage_context=self.storage_context,
                store_nodes_override=True,  # Force store nodes in index and document stores
                show_progress=self.show_progress,
                embed_model=self.embed_model,
                transformations=self.transformations,
            )
            index.storage_context.persist(persist_dir=get_local_data_path())
        return index

    def _save_index(self) -> None:
        self._index.storage_context.persist(persist_dir=get_local_data_path())

    def delete(self, doc_id: str) -> None:
        with self._index_thread_lock:
            # Delete the document from the index
            self._index.delete_ref_doc(doc_id, delete_from_docstore=True)

            # Save the index
            self._save_index()

  
def get_ingestion_component(
    storage_context: StorageContext,
    embed_model: EmbedType,
    transformations: list[TransformComponent],
    settings: Settings,
) -> BaseIngestComponent:

    ingest_mode = settings.embedding.ingest_mode
    if ingest_mode == "simple":
        return SimpleIngestComponent(
            storage_context=storage_context,
            embed_model=embed_model,
            transformations=transformations,
        )
