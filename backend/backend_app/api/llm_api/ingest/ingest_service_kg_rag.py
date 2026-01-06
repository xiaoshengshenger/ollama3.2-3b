import os
import re
import tempfile
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, AnyStr, BinaryIO, List, Optional, Tuple
from dataclasses import dataclass

# 项目内部依赖
from injector import inject, singleton
from backend_app.api.LLM.llm_component import LLMComponent
from backend_app.api.Embedding.embedding_component import EmbeddingComponent
from backend_app.api.LLM.node_store_component import NodeKgStoreComponent
from backend_app.api.llm_api.ingest.model import IngestedDoc
from backend_app.api.settings.settings import settings

# LlamaIndex 核心依赖
from llama_index.core import load_index_from_storage, StorageContext
from llama_index.core.indices.knowledge_graph import KnowledgeGraphIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document as LlamaDoc
from llama_index.core.storage.docstore.types import RefDocInfo
from llama_index.graph_stores.neo4j import Neo4jGraphStore


from backend_app.api.LLM.vector_store_component import (
    VectorStoreComponent,
)

if TYPE_CHECKING:
    from llama_index.core import QueryEngine
    from llama_index.core.indices.knowledge_graph import KnowledgeGraphIndex
import datetime

logger = logging.getLogger(__name__)

# ====================== 配置类（解耦Neo4j连接） ======================
@dataclass
class Neo4jConfig:
    """Neo4j 连接配置（从环境变量/项目配置读取）"""
    username: str = os.getenv("NEO4J_USER", settings().neo4j.username)
    password: str = os.getenv("NEO4J_PASSWORD", settings().neo4j.password)
    url: str = os.getenv("NEO4J_URL", settings().neo4j.url)
    database: str = os.getenv("NEO4J_DB", settings().neo4j.database)
    max_triplets_per_chunk: int = int(os.getenv("NEO4J_MAX_TRIPLETS", 3))
    include_embeddings: bool = os.getenv("NEO4J_INCLUDE_EMBEDDINGS", "True") == "True"

# ====================== 知识图谱RAG服务（单例+依赖注入） ======================
@singleton
class Neo4jKGRAGService:
    """
    知识图谱RAG服务（适配项目现有RAG架构）
    核心调整：复用向量RAG的向量数据库，为KG-RAG创建专属的docstore/index_store
    """
    @inject
    def __init__(
        self,
        llm_component: LLMComponent,
        embedding_component: EmbeddingComponent,
        vector_store_component: VectorStoreComponent,
        # 保留node_store_component，但仅作为参考，不复用其存储
        node_kg_store_component: NodeKgStoreComponent,
        neo4j_config: Neo4jConfig = Neo4jConfig()
    ):
        # 复用项目现有组件
        self.llm_component = llm_component
        self.embedding_component = embedding_component
        self.node_kg_store_component = node_kg_store_component
        self.vector_store_component = vector_store_component
        self.neo4j_config = neo4j_config

        # 1. 初始化Neo4j图谱存储（原有逻辑，保持独立）
        self.graph_store = self._init_graph_store()

        logger.info(f"✅ Neo4j图谱存储初始化完成：{self.neo4j_config}")
        
        # 3. 【核心修改】构建存储上下文：复用向量库，其余为KG专属存储
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store_component.vector_store,  # 复用原有向量RAG的向量数据库
            docstore=self.node_kg_store_component.doc_store,  # KG专属文档存储（新创建）
            index_store=self.node_kg_store_component.index_store,  # KG专属索引存储（新创建）
            graph_store=self.graph_store  # KG专属图存储（原有逻辑）
        )

        # 节点分割器（与原有RAG使用相同的分割策略，保持一致）
        self.node_parser = SentenceSplitter.from_defaults()
        
        # KG索引延迟初始化
        self.kg_index: Optional[KnowledgeGraphIndex] = None

        self.kg_index_exists = self._load_kg_index_status_from_neo4j()
        logger.info(f"✅ KG索引状态加载完成：{'已构建' if self.kg_index_exists else '未构建'}")

    def _init_graph_store(self) -> Neo4jGraphStore:
        """初始化Neo4j图谱存储（异常捕获+日志，原有逻辑不变）"""
        try:
            graph_store = Neo4jGraphStore(
                username=self.neo4j_config.username,
                password=self.neo4j_config.password,
                url=self.neo4j_config.url,
                database=self.neo4j_config.database,
            )
            logger.info(f"✅ 成功连接Neo4j: {self.neo4j_config.url} (数据库: {self.neo4j_config.database})")
            return graph_store
        except Exception as e:
            logger.error(f"❌ Neo4j连接失败: {str(e)}", exc_info=True)
            raise ConnectionError(f"Neo4j连接失败: {str(e)}")
    
    def _save_kg_index_status_to_neo4j(self, exists: bool):
        """将KG索引状态持久化到Neo4j（原有逻辑不变）"""
        if not self.graph_store:
            logger.warning("⚠️ Neo4j未初始化，跳过KG索引状态保存")
            return
        
        try:
            # 先删除原有状态节点（保证唯一性）
            delete_status_query = "MATCH (n:KGIndexStatus) DELETE n"
            self.graph_store.query(delete_status_query)
            
            # 创建新状态节点
            create_status_query = """
            CREATE (n:KGIndexStatus {
                exists: $exists,
                update_time: $update_time,
                node_desc: "KG索引状态标记节点，请勿手动删除",
                database: $database
            })
            """
            self.graph_store.query(
                create_status_query,
                {
                    "exists": exists,
                    "update_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "database": self.neo4j_config.database
                }
            )
            
            self.kg_index_exists = exists
            logger.info(f"✅ KG索引状态已持久化到Neo4j：{'已构建' if exists else '未构建'}")
        except Exception as e:
            logger.error(f"❌ 保存KG索引状态到Neo4j失败: {str(e)}", exc_info=True)
            raise

    def _load_kg_index_status_from_neo4j(self) -> bool:
        """从Neo4j加载KG索引状态（原有逻辑不变）"""
        if not self.graph_store:
            logger.warning("⚠️ Neo4j未初始化，默认KG索引未构建")
            return False
        
        try:
            load_status_query = "MATCH (n:KGIndexStatus) RETURN n.exists as exists"
            query_results = self.graph_store.query(load_status_query)
            
            if query_results and len(query_results) > 0:
                return query_results[0]["exists"]
            
            logger.warning("⚠️ Neo4j中未找到KG索引状态节点，默认索引未构建")
            return False
        except Exception as e:
            logger.warning(f"⚠️ 加载KG索引状态失败，默认索引未构建：{str(e)}")
            return False

    # ====================== 清理Neo4j中的无效三元组（原有逻辑不变） ======================
    def _clean_invalid_triples_in_neo4j(self):
        if not self.graph_store:
            logger.warning("⚠️ Neo4j未初始化，跳过无效三元组清理")
            return
        
        # 定义无效关键词（与文本清理逻辑对齐）
        invalid_keywords = ['E:', 'Tmp', 'tmp', '.txt', 'backend_app', 'llama3.2-projec', 'Backend_app', 'Ai']
        
        try:
            # 转义关键词中的特殊字符
            escaped_keywords = [keyword.replace("'", "\\'").replace('"', '\\"') for keyword in invalid_keywords]
            keywords_str = ", ".join([f"'{kw}'" for kw in escaped_keywords])
            
            # 查询所有包含无效关键词的节点
            invalid_node_query = f"""
            MATCH (n) 
            WHERE ANY(keyword IN [{keywords_str}] WHERE 
                ANY(prop IN keys(n) WHERE 
                    toLower(toString(n[prop])) CONTAINS toLower(keyword)
                )
            )
            RETURN elementId(n) as node_id
            """
            invalid_nodes = self.graph_store.query(invalid_node_query)
            
            if not invalid_nodes:
                logger.info("✅ Neo4j中无无效三元组，无需清理")
                return
            
            # 删除这些无效节点及其关联的关系
            delete_invalid_query = f"""
            MATCH (n) 
            WHERE ANY(keyword IN [{keywords_str}] WHERE 
                ANY(prop IN keys(n) WHERE 
                    toLower(toString(n[prop])) CONTAINS toLower(keyword)
                )
            )
            DETACH DELETE n
            """
            self.graph_store.query(delete_invalid_query)
            
            # 验证清理结果
            remaining_triples = self.graph_store.query("MATCH (s)-[r]->(o) RETURN count(*) as total")
            logger.info(f"✅ 成功清理Neo4j中的无效三元组：")
            logger.info(f"   - 清理的无效节点数量：{len(invalid_nodes)}")
            logger.info(f"   - 清理后剩余有效三元组数量：{remaining_triples[0]['total'] if remaining_triples else 0}")
            
        except Exception as e:
            logger.error(f"❌ 清理Neo4j无效三元组失败: {str(e)}", exc_info=True)

    # ====================== 文档处理（原有逻辑不变，仅启用清理方法） ======================
    def _ingest_data(self, file_name: str, file_data: AnyStr) -> list[IngestedDoc]:
        PROJECT_TMP_DIR = Path(__file__).parent.parent.parent.parent / "tmp"
        PROJECT_TMP_DIR.mkdir(exist_ok=True, mode=0o777)
        path_to_tmp = None

        try:
            with tempfile.NamedTemporaryFile(
                dir=str(PROJECT_TMP_DIR),
                suffix=Path(file_name).suffix,
                delete=False
            ) as tmp:
                path_to_tmp = Path(tmp.name)
                if isinstance(file_data, bytes):
                    tmp.write(file_data)
                else:
                    tmp.write(str(file_data).encode("utf-8"))
                tmp.flush()
                os.fsync(tmp.fileno())

            return self.ingest_file(file_name, path_to_tmp)
        finally:
            if path_to_tmp and path_to_tmp.exists():
                try:
                    time.sleep(0.5)
                    path_to_tmp.unlink()
                    logger.debug(f"✅ 临时文件 {path_to_tmp} 已成功清理")
                except Exception as e:
                    logger.warning(f"⚠️ 清理临时文件失败：{str(e)}，文件将残留，建议后续定时清理")

    def _clean_document_text(self, text: str) -> str:
        if not text:
            return ""
        
        # 过滤路径模式
        text = re.sub(r'[A-Za-z]:(\\|/)?[^\\/\n]*', '', text)
        text = re.sub(r'^[A-Za-z]:$', '', text, flags=re.MULTILINE)
        
        # 过滤临时文件名
        text = re.sub(r'Tmp\w+\.txt', '', text)
        
        # 过滤项目关键词
        project_keywords = r'\b(tmp|Tmp|TEMP|temp|Backend_app|Ai)\b'
        text = re.sub(project_keywords, '', text, flags=re.IGNORECASE)
        
        # 过滤多余空格和空行
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def ingest_file(self, file_name: str, file_data: Path) -> list[IngestedDoc]:
        # 1. 加载文档
        from llama_index.core import SimpleDirectoryReader
        documents = SimpleDirectoryReader(input_files=[file_data]).load_data()
        logger.info(f"加载文件 {file_name} 完成，原始文档块数量：{len(documents)}")

        # 2. 文档内容预处理
        processed_docs = []
        for doc in documents:
            clean_text = self._clean_document_text(doc.text)
            if clean_text:
                processed_doc = LlamaDoc(
                    text=clean_text,
                    metadata=doc.metadata,
                    id_=doc.id_
                )
                processed_doc.metadata["original_file_name"] = file_name
                processed_docs.append(processed_doc)
        logger.info(f"文档预处理完成，有效文档块数量：{len(processed_docs)}")

        # 3. 清空历史数据（可选）
        if settings().neo4j.clear_existing_data:
            self.clear_neo4j_data()
            logger.info("✅ 已清空Neo4j现有图谱数据")

        # 4. 构建知识图谱索引（复用向量库，存储到KG专属存储）
        self.kg_index = KnowledgeGraphIndex.from_documents(
            documents=processed_docs,
            storage_context=self.storage_context,
            max_triplets_per_chunk=self.neo4j_config.max_triplets_per_chunk,
            include_embeddings=self.neo4j_config.include_embeddings,
            embed_model=self.embedding_component.embedding_model,
            llm=self.llm_component.llm,
            node_parser=self.node_parser,
            index_id="neo4j_kg_index",
            # 三元组提取提示（原有逻辑不变）
            kg_triple_extract_template="""
            # 任务要求
            从以下文本中仅提取**业务内容相关**的三元组（主体，关系，客体），严格遵守以下规则：

            # 过滤规则（必须遵守）
            1. 完全忽略任何与文件系统相关的内容，包括但不限于：
            - 文件路径（如：E:\、/home/user、C:/）
            - 文件名（如：document.txt、image.png）
            - 目录名（如：tmp、Backend_app、Ai）
            - 盘符（如：C:、D:）
            2. 只提取文本中描述实体、属性、关系的有效信息。
            3. 主体和客体必须是有实际业务含义的名词/短语，关系必须是能体现两者关联的动词/介词短语。

            # 好的示例
            - ("Python", "是一种", "编程语言")
            - ("牛顿", "提出了", "万有引力定律")
            - ("《三体》", "的作者是", "刘慈欣")

            # 坏的示例（请不要输出这样的内容）
            - ("E:", "IS_LOCATED_IN", "Ai")
            - ("Tmpfile.txt", "HAS_CONTENT", "data")

            # 输出格式（仅返回列表，无其他文字）
            [("主体1", "关系1", "客体1"), ("主体2", "关系2", "客体2")]

            # 需要提取的文本
            {text}
            """ 
        )

        # 启用无效三元组清理（原有注释取消）
        #self._clean_invalid_triples_in_neo4j()
        self._save_kg_index_status_to_neo4j(True)

        # 5. 从Neo4j中获取三元组并过滤无效数据
        try:
            cypher_query = """
            MATCH (s)-[r]->(o) 
            RETURN s.id AS subject, type(r) AS relation, o.id AS object
            """
            query_results = self.graph_store.query(cypher_query)
            all_triples = [
                (result["subject"], result["relation"], result["object"]) 
                for result in query_results
            ]
            
            # 后过滤无效三元组
            valid_triples = []
            invalid_keywords = ['E:', 'Tmp', 'tmp', '.txt', 'backend_app', 'llama3.2-projec', 'Backend_app', 'Ai']
            for triple in all_triples:
                if not any(keyword in str(triple) for keyword in invalid_keywords):
                    valid_triples.append(triple)
            
            logger.info(f"✅ 知识图谱索引构建完成：")
            logger.info(f"   - 原始三元组数量：{len(all_triples)}")
            logger.info(f"   - 有效三元组数量：{len(valid_triples)}")
            logger.info(f"   - 有效三元组内容：{valid_triples if valid_triples else '无有效三元组'}")
            
        except Exception as e:
            logger.error(f"获取Neo4j三元组数量失败: {str(e)}", exc_info=True)
            logger.warning(f"⚠️ 无法获取三元组数量，已降级为0（文件：{file_name}）")

        # 6. 映射为项目统一的IngestedDoc模型
        current_ingested_docs = [IngestedDoc.from_document(doc) for doc in processed_docs]
        
        # 7. 查询KG专属存储中所有已入库的全量文档
        all_ingested_docs = self.list_ingested_kg_docs()
        
        logger.info(f"✅ 当前上传文档数：{len(current_ingested_docs)}，KG专属存储全量文档数：{len(all_ingested_docs)}")
        return all_ingested_docs

    def ingest_bin_data(self, file_name: str, raw_file_data: BinaryIO) -> list[IngestedDoc]:
        """处理二进制文件流（原有逻辑不变）"""
        try:
            raw_file_data.seek(0)
            file_data = raw_file_data.read()
            return self._ingest_data(file_name, file_data)
        except Exception as e:
            logger.error(f"处理二进制文件 {file_name} 失败: {str(e)}", exc_info=True)
            raise

    # ====================== 知识图谱RAG查询（原有逻辑不变） ======================
    def get_kg_query_engine(self, **kwargs) -> "QueryEngine":
        if not self.kg_index_exists:
            raise RuntimeError("知识图谱索引未构建，请先上传文档")

        if not self.kg_index:
            try:
                self.kg_index = load_index_from_storage(self.storage_context,index_id="neo4j_kg_index")
                logger.info("✅ 从KG专属存储上下文重新加载KG索引成功")
            except Exception as e:
                logger.error(f"❌ 加载KG索引失败: {str(e)}")
                raise RuntimeError("知识图谱索引已构建，但加载失败，请重新上传文档")

        # 默认配置（可通过kwargs覆盖）
        query_config = {
            "include_text": kwargs.get("include_text", True),
            "response_mode": kwargs.get("response_mode", "tree_summarize"),
            "embedding_mode": kwargs.get("embedding_mode", "hybrid"),
            "similarity_top_k": kwargs.get("similarity_top_k", 5),
            "llm": self.llm_component.llm,
            "embed_model": self.embedding_component.embedding_model
        }

        return self.kg_index.as_query_engine(** query_config)

    def query_kg_rag(self, query_text: str, **kwargs) -> str:
        """执行知识图谱RAG查询"""
        try:
            query_engine = self.get_kg_query_engine(** kwargs)
            response = query_engine.query(query_text)
            return str(response)
        except Exception as e:
            logger.error(f"KG RAG查询失败: {str(e)}", exc_info=True)
            raise

    # ====================== 辅助方法（适配KG专属存储） ======================
    def clear_neo4j_data(self) -> None:
        """清空Neo4j所有节点/关系及KG专属存储数据"""
        if not self.graph_store:
            raise RuntimeError("Neo4j图谱存储未初始化")
        # 清空Neo4j图数据
        self.graph_store.query("MATCH (n) DETACH DELETE n")
        # 清空KG专属文档存储和索引存储
        self.node_kg_store_component.doc_store.clear()
        self.node_kg_store_component.index_store.clear()
        # 重置KG索引
        self.kg_index = None
        # 同步状态到Neo4j
        self._save_kg_index_status_to_neo4j(False)
        logger.warning("⚠️ Neo4j所有数据及KG专属存储数据已清空")

    def list_ingested_kg_docs(self) -> list[IngestedDoc]:
        """查询KG专属存储中已入库的文档（原有逻辑适配新存储）"""
        ingested_docs: list[IngestedDoc] = []
        try:
            # 从KG专属文档存储中获取全量参考文档
            ref_docs: dict[str, RefDocInfo] | None = self.node_kg_store_component.doc_store.get_all_ref_doc_info()
            if not ref_docs:
                return ingested_docs

            for doc_id, ref_doc_info in ref_docs.items():
                doc_metadata = None
                if ref_doc_info and ref_doc_info.metadata:
                    doc_metadata = IngestedDoc.curate_metadata(ref_doc_info.metadata)
                ingested_docs.append(
                    IngestedDoc(
                        object="ingest.kg_document",
                        doc_id=doc_id,
                        doc_metadata=doc_metadata, 
                    )
                )
            logger.debug(f"从KG专属存储查询到 {len(ingested_docs)} 个入库文档")
        except Exception as e:
            logger.warning("获取KG入库文档列表失败", exc_info=True)
        return ingested_docs

    def delete_kg_doc(self, doc_id: str) -> None:
        """删除KG专属存储中指定文档及关联Neo4j三元组"""
        if not self.kg_index_exists:
            raise RuntimeError("知识图谱索引未构建")

        if not self.kg_index:
            raise RuntimeError("KG索引未加载，无法删除文档")
        try:
            # 从KG索引中删除文档（同步删除KG专属存储数据）
            self.kg_index.delete_ref_doc(doc_id, delete_from_docstore=True)
            # 同步删除Neo4j中关联的三元组
            delete_related_query = "MATCH (n) WHERE n.doc_id = $doc_id DETACH DELETE n"
            self.graph_store.query(delete_related_query, {"doc_id": doc_id})
            logger.info(f"删除KG文档成功：{doc_id}")

            remaining_docs = self.list_ingested_kg_docs()
            if not remaining_docs:
                self.kg_index = None
                self._save_kg_index_status_to_neo4j(False)
                logger.info("⚠️ 最后一个KG文档已删除，KG索引状态标记为未构建")
        except Exception as e:
            logger.error(f"删除KG文档失败: {doc_id}", exc_info=True)
            raise