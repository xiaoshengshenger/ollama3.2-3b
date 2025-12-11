import tempfile
from pathlib import Path
from typing import AnyStr, BinaryIO

from injector import inject, singleton
from llama_index.core.node_parser import SentenceWindowNodeParser
from llama_index.core.storage import StorageContext

from app.api.Embedding.embedding_component import EmbeddingComponent
from app.api.ingest.ingest_component import get_ingestion_component
from app.api.LLM.llm_component import LLMComponent
from app.api.LLM.node_store_component import NodeStoreComponent
from app.api.LLM.vector_store_component import (
    VectorStoreComponent,
)
from app.api.llm_api.ingest.model import IngestedDoc
from app.api.settings.settings import settings



@singleton
class IngestService:
    @inject
    def __init__(
        self,
        llm_component: LLMComponent,
        vector_store_component: VectorStoreComponent,
        embedding_component: EmbeddingComponent,
        node_store_component: NodeStoreComponent,
    ) -> None:
        self.llm_service = llm_component
        self.storage_context = StorageContext.from_defaults(
            vector_store=vector_store_component.vector_store,
            docstore=node_store_component.doc_store,
            index_store=node_store_component.index_store,
        )
        node_parser = SentenceWindowNodeParser.from_defaults()

        self.ingest_component = get_ingestion_component(
            self.storage_context,
            embed_model=embedding_component.embedding_model,
            transformations=[node_parser, embedding_component.embedding_model],
            settings=settings(),
        )

    def _ingest_data(self, file_name: str, file_data: AnyStr) -> list[IngestedDoc]:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            try:
                path_to_tmp = Path(tmp.name)
                if isinstance(file_data, bytes):
                    path_to_tmp.write_bytes(file_data)
                else:
                    path_to_tmp.write_text(str(file_data))
                return self.ingest_file(file_name, path_to_tmp)
            finally:
                tmp.close()
                path_to_tmp.unlink()

    def ingest_file(self, file_name: str, file_data: Path) -> list[IngestedDoc]:
        documents = self.ingest_component.ingest(file_name, file_data)
        return [IngestedDoc.from_document(document) for document in documents]

    def ingest_bin_data(
        self, file_name: str, raw_file_data: BinaryIO
    ) -> list[IngestedDoc]:
        file_data = raw_file_data.read()
        return self._ingest_data(file_name, file_data)

