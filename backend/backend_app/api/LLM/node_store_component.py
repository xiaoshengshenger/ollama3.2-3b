from injector import singleton
from llama_index.core.storage.docstore import BaseDocumentStore, SimpleDocumentStore
from llama_index.core.storage.index_store import SimpleIndexStore
from llama_index.core.storage.index_store.types import BaseIndexStore

from backend_app.constants import get_local_data_path,get_local_kg_data_path
from backend_app.api.settings.settings import settings


@singleton
class NodeStoreComponent:
    index_store: BaseIndexStore
    doc_store: BaseDocumentStore

    def __init__(self) -> None:
        database = settings().nodestore.database
        match database:
            case "simple":
                try:
                    self.index_store = SimpleIndexStore.from_persist_dir(
                        persist_dir=str(get_local_data_path())
                    )
                except FileNotFoundError:
                    self.index_store = SimpleIndexStore()

                try:
                    self.doc_store = SimpleDocumentStore.from_persist_dir(
                        persist_dir=str(get_local_data_path())
                    )
                except FileNotFoundError:
                    self.doc_store = SimpleDocumentStore()

            case _:
                # Should be unreachable
                # The settings validator should have caught this
                raise ValueError(
                    f"Database {settings().nodestore.database} not supported"
                )

class NodeKgStoreComponent:
    index_store: BaseIndexStore
    doc_store: BaseDocumentStore

    def __init__(self) -> None:
        database = settings().nodestore.database
        match database:
            case "simple":
                try:
                    self.index_store = SimpleIndexStore.from_persist_dir(
                        persist_dir=str(get_local_kg_data_path())
                    )
                except FileNotFoundError:
                    self.index_store = SimpleIndexStore()

                try:
                    self.doc_store = SimpleDocumentStore.from_persist_dir(
                        persist_dir=str(get_local_kg_data_path())
                    )
                except FileNotFoundError:
                    self.doc_store = SimpleDocumentStore()

            case _:
                # Should be unreachable
                # The settings validator should have caught this
                raise ValueError(
                    f"Database {settings().nodestore.database} not supported"
                )