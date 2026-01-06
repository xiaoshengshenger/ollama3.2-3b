import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, AnyStr, BinaryIO

from injector import inject, singleton
from llama_index.core.node_parser import SentenceWindowNodeParser
from llama_index.core.storage import StorageContext

from backend_app.api.Embedding.embedding_component import EmbeddingComponent
from backend_app.api.ingest.ingest_component import get_ingestion_component
from backend_app.api.LLM.llm_component import LLMComponent
from backend_app.api.LLM.node_store_component import NodeStoreComponent
from backend_app.api.LLM.vector_store_component import (
    VectorStoreComponent,
)
from backend_app.api.llm_api.ingest.model import IngestedDoc
from backend_app.api.settings.settings import settings

if TYPE_CHECKING:
    from llama_index.core.storage.docstore.types import RefDocInfo

import logging

logger = logging.getLogger(__name__)

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
        #logger.info(f"~~~~~~~~~~~~:{node_store_component.index_store}------{node_store_component.doc_store}------{vector_store_component.vector_store}")
        #self.delete_all_ingested_data()

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
        logger.info(f"生成文档：{documents}")
        return [IngestedDoc.from_document(document) for document in documents]

    def ingest_bin_data(
        self, file_name: str, raw_file_data: BinaryIO
    ) -> list[IngestedDoc]:
        file_data = raw_file_data.read()
        return self._ingest_data(file_name, file_data)
    

    def list_ingested(self) -> list[IngestedDoc]:
        ingested_docs: list[IngestedDoc] = []
        try:
            docstore = self.storage_context.docstore
            ref_docs: dict[str, RefDocInfo] | None = docstore.get_all_ref_doc_info()
            logger.info(f"ref_docs:::: {ref_docs}")
            if not ref_docs:
                return ingested_docs

            for doc_id, ref_doc_info in ref_docs.items():
                doc_metadata = None
                if ref_doc_info is not None and ref_doc_info.metadata is not None:
                    doc_metadata = IngestedDoc.curate_metadata(ref_doc_info.metadata)
                ingested_docs.append(
                    IngestedDoc(
                        object="ingest.document",
                        doc_id=doc_id,
                        doc_metadata=doc_metadata,
                    )
                )
        except ValueError:
            logger.warning("Got an exception when getting list of docs", exc_info=True)
            pass
        logger.debug("Found count=%s ingested documents", len(ingested_docs))
        return ingested_docs
    
    # 新增：删除全部数据的核心方法
    def delete_all_ingested_data(self) -> None:
        """
        修复版：移除冗余逻辑，仅通过 delete_ref_doc 彻底清理 DocStore
        利用 delete_ref_doc 级联删除能力，避免关联关系破坏导致的清理失败
        """
        try:
            # 1. 清空向量存储（原有逻辑保留）
            vector_store = self.storage_context.vector_store
            vector_store.clear()
            logger.info("✅ 向量存储全量数据已清空")

            # 2. 清空文档存储（核心修复：移除 delete_document，仅用 delete_ref_doc）
            doc_store = self.storage_context.docstore
            # 先获取所有参考文档（一次性获取，避免遍历中修改存储导致的异常）
            ref_docs = doc_store.get_all_ref_doc_info()
            deleted_ref_doc_count = 0

            if ref_docs and len(ref_docs) > 0:
                # 转换为列表遍历，避免字典遍历中修改（部分 doc_store 实现不支持遍历中删除）
                ref_doc_id_list = list(ref_docs.keys())
                for ref_doc_id in ref_doc_id_list:
                    try:
                        # 仅这一行即可：删除参考文档 + 级联删除关联节点文档
                        doc_store.delete_ref_doc(ref_doc_id)
                        deleted_ref_doc_count += 1
                    except Exception as doc_e:
                        logger.warning(f"⚠️ 单个参考文档 {ref_doc_id} 删除失败：{str(doc_e)}，继续清理下一个")
                        continue
            logger.info(f"✅ 文档存储全量数据已清空：共删除 {deleted_ref_doc_count} 个参考文档（含级联删除关联节点）")

            # 3. 清空索引存储（原有逻辑保留）
            index_store = self.storage_context.index_store
            index_structs_list = index_store.index_structs()
            deleted_index_count = 0
            if index_structs_list:
                for index_struct in index_structs_list:
                    index_store.delete_index_struct(index_struct.index_id)
                    deleted_index_count += 1
            logger.info(f"✅ 索引存储全量数据已清空，共删除 {deleted_index_count} 个索引")

            # 4. 新增：强制刷新 DocStore（解决缓存未更新问题）
            if hasattr(doc_store, 'persist'):
                # 若 doc_store 支持持久化（如 SimpleDocumentStore），强制持久化清理结果
                doc_store.persist()
            if hasattr(doc_store, 'refresh'):
                # 若 doc_store 支持刷新，强制刷新缓存
                doc_store.refresh()
            logger.info("✅ DocStore 清理结果已强制持久化/刷新")

        except Exception as e:
            logger.error("❌ 删除全量摄入数据失败", exc_info=True)
            raise e
        
    def delete(self, doc_id: str) -> None:
        logger.info(
            "Deleting the ingested document=%s in the doc and index store", doc_id
        )
        self.ingest_component.delete(doc_id)