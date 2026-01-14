from backend_app.api.settings.settings import settings, Settings
from injector import inject, singleton
from backend_app.api.Embedding.embedding_component import EmbeddingComponent
from backend_app.api.LLM.llm_component import LLMComponent
from backend_app.api.LLM.vector_store_component import VectorStoreComponent
from backend_app.api.LLM.node_store_component import NodeStoreComponent

from llama_index.core.storage import StorageContext
from llama_index.core.llms import ChatMessage, MessageRole
from backend_app.api.LLM.context_filter import ContextFilter

from llama_index.core.indices import VectorStoreIndex
from llama_index.core.storage import StorageContext

from llama_index.core.types import TokenGen
from pydantic import BaseModel
from dataclasses import dataclass
from llama_index.core.postprocessor.types import BaseNodePostprocessor

from llama_index.core.chat_engine.types import (
    BaseChatEngine,
)
from llama_index.core.indices.postprocessor import MetadataReplacementPostProcessor
from llama_index.core.postprocessor import (
    SentenceTransformerRerank,
    SimilarityPostprocessor,
)

from llama_index.core.chat_engine import ContextChatEngine, SimpleChatEngine
from backend_app.api.llm_api.chunks.chunks_service import Chunk

from backend_app.api.llm_api.ingest.ingest_service_kg_rag import Neo4jKGRAGService 

from llama_index.core.storage.index_store import SimpleIndexStore
from datetime import datetime
#redis
from backend_app.api.tools.redis_service import RedisService
import hashlib
import json

import logging

logger = logging.getLogger(__name__)
HYBRID_RAG_CACHE_EXPIRE_SECONDS = 3600  # 1小时过期
CACHE_KEY_PREFIX = "hybrid_rag:cache:" 
@dataclass
class ChatEngineInput:
    system_message: ChatMessage | None = None
    last_message: ChatMessage | None = None
    chat_history: list[ChatMessage] | None = None

    @classmethod
    def from_messages(cls, messages: list[ChatMessage]) -> "ChatEngineInput":
        # Detect if there is a system message, extract the last message and chat history
        system_message = (
            messages[0]
            if len(messages) > 0 and messages[0].role == MessageRole.SYSTEM
            else None
        )
        last_message = (
            messages[-1]
            if len(messages) > 0 and messages[-1].role == MessageRole.USER
            else None
        )
        # Remove from messages list the system message and last message,
        # if they exist. The rest is the chat history.
        if system_message:
            messages.pop(0)
        if last_message:
            messages.pop(-1)
        chat_history = messages if len(messages) > 0 else None

        return cls(
            system_message=system_message,
            last_message=last_message,
            chat_history=chat_history,
        )

class CompletionGen(BaseModel):
    response: TokenGen
    sources: list[Chunk] | None = None

@singleton
class ChatService:
    settings: Settings

    @inject
    def __init__(
        self,
        llm_component: LLMComponent,
        redis_service: RedisService,
        vector_store_component: VectorStoreComponent,
        embedding_component: EmbeddingComponent,
        node_store_component: NodeStoreComponent,
        neo4j_kg_rag_service: Neo4jKGRAGService,
    ) -> None:
        self.settings = settings()
        self.llm_component = llm_component
        self.redis_service = redis_service
        self.embedding_component = embedding_component
        self.neo4j_kg_rag_service = neo4j_kg_rag_service  # 保存KG-RAG服务实例
        self.vector_store_component = vector_store_component
        self.node_store_component = node_store_component
        self.storage_context = StorageContext.from_defaults(
            vector_store=vector_store_component.vector_store,
            docstore=node_store_component.doc_store,
            index_store=node_store_component.index_store,
        )
        self.index = VectorStoreIndex.from_vector_store(
            vector_store_component.vector_store,
            storage_context=self.storage_context,
            llm=llm_component.llm,
            embed_model=embedding_component.embedding_model,
            show_progress=True,
        )

    def clear_vector_and_node_data(self):
        """清空向量数据库、文档存储和索引存储的所有数据（谨慎使用）"""
        try:
            # 2. 清空文档存储（适配SimpleDocumentStore）
            all_ref_doc_info = self.node_store_component.doc_store.get_all_ref_doc_info()
            all_ref_doc_ids = list(all_ref_doc_info.keys())
            
            # 非空判断，避免无效循环
            if all_ref_doc_ids:
                for doc_id in all_ref_doc_ids:
                    self.node_store_component.doc_store.delete_ref_doc(doc_id)
                logger.debug(f"已删除 {len(all_ref_doc_ids)} 个文档")
            else:
                logger.debug("无文档需要删除，跳过文档存储清空步骤")
            
            # 3. 清空索引存储（适配SimpleIndexStore：重新初始化 = 清空所有索引数据）
            self.node_store_component.index_store = SimpleIndexStore()  # 关键修复：重新初始化

            self.neo4j_kg_rag_service.clear_neo4j_data()
        except Exception as e:
            logger.error(f"❌ 清空数据失败：{str(e)}", exc_info=True)
            raise

    def _chat_engine(
        self,
        system_prompt: str | None = None,
        use_context: bool = False,
        context_filter: ContextFilter | None = None,
    ) -> BaseChatEngine:
        if use_context:
            vector_index_retriever = self.vector_store_component.get_retriever(
                index=self.index,
                context_filter=context_filter,
                similarity_top_k=self.settings.rag.similarity_top_k,
            )
            node_postprocessors: list[BaseNodePostprocessor] = [
                MetadataReplacementPostProcessor(target_metadata_key="window"),
            ]
            if self.settings.rag.similarity_value:
                node_postprocessors.append(
                    SimilarityPostprocessor(
                        similarity_cutoff=self.settings.rag.similarity_value,
                    )
                )

            if self.settings.rag.rerank.enabled:
                rerank_postprocessor = SentenceTransformerRerank(
                    model=self.settings.rag.rerank.model, top_n=self.settings.rag.rerank.top_n
                )
                node_postprocessors.append(rerank_postprocessor)

            chat_engine = ContextChatEngine.from_defaults(
                system_prompt=system_prompt or "",
                retriever=vector_index_retriever,
                llm=self.llm_component.llm,  # Takes no effect at the moment
                node_postprocessors=node_postprocessors,
                streaming=True,  # 关键：启用流式响应
                verbose=True,  # 可选：便于调试
            )
            
            return chat_engine
            
        else:
            return SimpleChatEngine.from_defaults(
                system_prompt=system_prompt or "",
                llm=self.llm_component.llm,
                streaming=True,
            )

    def stream_chat(
        self,
        messages: list[ChatMessage],
        use_context: bool = False,
        context_filter: ContextFilter | None = None,
        use_kg_rag: bool = False,
        use_hybrid_rag: bool = False,
        # KG查询配置参数
        kg_query_kwargs: dict | None = None,
    ) -> CompletionGen:
        chat_engine_input = ChatEngineInput.from_messages(messages)
        last_message = (
            chat_engine_input.last_message.content
            if chat_engine_input.last_message
            else ''
        )
        system_prompt = (
            chat_engine_input.system_message.content
            if chat_engine_input.system_message
            else ''
        )
        chat_history = (
            chat_engine_input.chat_history if chat_engine_input.chat_history else []
        )
        chat_engine = self._chat_engine(
            system_prompt=system_prompt,
            use_context=use_context,
            context_filter=context_filter,
        )

        #self.clear_vector_and_node_data()
        if not last_message:
            last_message = "请提供有效的问题"

        # 初始化默认参数
        kg_kwargs = kg_query_kwargs or {}

        # 分支1：使用混合RAG（向量RAG + KG-RAG）
        if use_hybrid_rag:
            # 执行混合查询，获取融合后的回答和来源
            fusion_response_text, sources = self._query_hybrid_rag(
                query_text=last_message,
                chat_engine=chat_engine,
                chat_history=chat_history,
                **kg_kwargs
            )
            # 将完整文本转为流式TokenGen（兼容原有返回格式）
            fusion_token_gen = (token for token in fusion_response_text)
            return CompletionGen(response=fusion_token_gen, sources=sources)

        # 分支2：使用纯KG-RAG
        elif use_kg_rag:
            # 执行纯KG-RAG查询
            kg_response_text = self._query_kg_rag(last_message, **kg_kwargs)
            # 转为流式TokenGen（兼容原有返回格式）
            kg_token_gen = (token for token in kg_response_text)
            return CompletionGen(response=kg_token_gen, sources=None)

        # 分支3：原有逻辑（纯向量RAG / 无上下文聊天）
        else:
            streaming_response = chat_engine.stream_chat(
                message=last_message if last_message is not None else "",
                chat_history=chat_history,
            )
            sources = [Chunk.from_node(node) for node in streaming_response.source_nodes]
            completion_gen = CompletionGen(
                response=streaming_response.response_gen, sources=sources
            )
            return completion_gen
    
    def _query_kg_rag(self, query_text: str, **kwargs) -> str:
        """
        执行纯知识图谱RAG查询
        :param query_text: 用户问题
        :param kwargs: KG查询引擎配置参数（如similarity_top_k、response_mode等）
        :return: KG-RAG回答结果
        """
        try:
            # 复用已实现的neo4j_kg_rag_service.query_kg_rag方法
            kg_response = self.neo4j_kg_rag_service.query_kg_rag(query_text, **kwargs)
            return kg_response
        except RuntimeError as e:
            # 捕获KG索引未构建的异常，返回提示信息（不中断整体流程）
            logger.warning(f"KG-RAG查询失败（索引未构建）：{str(e)}")
            return f"知识图谱索引未构建，请先上传文档后再进行相关查询。"
        except Exception as e:
            logger.error(f"KG-RAG查询异常：{str(e)}", exc_info=True)
            return f"知识图谱查询出错：{str(e)}"

    # 新增：融合向量RAG与KG-RAG结果（核心优化，发挥两者优势）
    def _query_hybrid_rag(self, query_text: str, chat_engine, chat_history: list[ChatMessage], **kwargs) -> tuple[str, list[Chunk]]:
        """
        混合查询：向量RAG（提供上下文细节） + KG-RAG（提供关系推理）
        :return: 融合后的回答、向量RAG来源节点
        """
        # ========== 第一步：生成唯一缓存键 ==========
        # 缓存键包含：查询文本 + 关键kwargs参数（保证缓存唯一性）
        cache_params = {
            "query_text": query_text,
            # 提取kwargs中影响查询结果的关键参数（如过滤条件、top_k等）
            "kwargs": {k: v for k, v in kwargs.items() if k in ["top_k", "context_filter", "entity_filter"]}
        }
        # 将参数转为JSON字符串，再通过MD5生成唯一key（避免键过长）
        cache_key_str = json.dumps(cache_params, ensure_ascii=False, sort_keys=True)
        cache_key_hash = hashlib.md5(cache_key_str.encode("utf-8")).hexdigest()
        cache_key = f"{CACHE_KEY_PREFIX}{cache_key_hash}"

        # ========== 第二步：尝试从Redis读取缓存 ==========
        cached_result = self.redis_service.get(cache_key)
        if cached_result:
            logger.info(f"混合RAG缓存命中，缓存键：{cache_key}，问题：{query_text}")
            # 反序列化缓存结果
            fusion_response = cached_result.get("fusion_response", "")
            # 将缓存的字典列表转为Chunk对象
            vector_sources = [
                Chunk(**chunk_dict) for chunk_dict in cached_result.get("vector_sources", [])
            ]
            return fusion_response, vector_sources

        # ========== 第三步：缓存未命中，执行原混合RAG逻辑 ==========
        logger.info(f"混合RAG缓存未命中，执行实际查询，问题：{query_text}")
        
        # 1. 执行向量RAG查询（流式响应转为完整文本）
        vector_stream_response = chat_engine.stream_chat(message=query_text, chat_history=chat_history)
        vector_response = "".join([token for token in vector_stream_response.response_gen])
        vector_sources = [Chunk.from_node(node) for node in vector_stream_response.source_nodes]

        # 2. 执行KG-RAG查询
        kg_response = self._query_kg_rag(query_text,** kwargs)
        logger.info(f"混合RAG查询完成，问题：{query_text}，向量RAG回答长度：{len(vector_response)}，KG-RAG回答长度：{len(kg_response)}")
        
        # 3. 融合两者结果（通过LLM总结融合，保证回答一致性和完整性）
        fusion_prompt = f"""
        请你将以下两个回答融合为一个精准、简洁的最终回答，严格遵循以下要求：
        1.  向量检索回答（提供细节上下文）：{vector_response}
        2.  知识图谱回答（提供实体关系推理）：{kg_response}

        ########### 核心规则（必须严格遵守，缺一不可）###########
        1.  优先提取并保留知识图谱中的明确实体关系事实（如部门与负责人的对应关系），这是最高优先级
        2.  仅保留与用户问题直接相关的信息，完全忽略无关内容（如产品功能、发布日期、人物关系推测等非用户询问内容）
        3.  坚决删除所有冗余表述、同义改写、无依据推测（如“他们都是管理者”“可以推测与AI有关”等）
        4.  回答格式要求：分点列出（使用数字序号），每点仅陈述一个明确事实，不添加额外修饰词
        5.  无需补充额外背景信息，无需总结，无需过渡句，只输出用户问题对应的核心答案
        6.  去除重复内容，保证回答简洁明了，语言精炼，无废话

        用户当前问题是：{query_text}，请严格按上述规则生成回答。
        """

        # 调用LLM进行结果融合
        fusion_response = self.llm_component.llm.complete(fusion_prompt)
        fusion_response_str = str(fusion_response)

        # ========== 第四步：将结果写入Redis缓存 ==========
        # 转换Chunk对象为字典（便于序列化存储）
        vector_sources_dict = [chunk.model_dump() for chunk in vector_sources]
        cache_value = {
            "fusion_response": fusion_response_str,
            "vector_sources": vector_sources_dict,
            "query_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 记录缓存写入时间（便于排查）
            "query_text": query_text[:100]  # 存储简短查询文本（便于缓存管理）
        }
        
        # 写入缓存（设置过期时间）
        cache_set_success = self.redis_service.set(
            key=cache_key,
            value=cache_value,
            ex=HYBRID_RAG_CACHE_EXPIRE_SECONDS
        )
        if cache_set_success:
            logger.info(f"混合RAG缓存写入成功，缓存键：{cache_key}，过期时间：{HYBRID_RAG_CACHE_EXPIRE_SECONDS}秒")
        else:
            logger.warning(f"混合RAG缓存写入失败，缓存键：{cache_key}")

        return fusion_response_str, vector_sources

