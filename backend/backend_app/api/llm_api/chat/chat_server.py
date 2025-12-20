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

import logging

logger = logging.getLogger(__name__)

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
        vector_store_component: VectorStoreComponent,
        embedding_component: EmbeddingComponent,
        node_store_component: NodeStoreComponent,
    ) -> None:
        self.settings = settings()
        self.llm_component = llm_component
        self.embedding_component = embedding_component
        self.vector_store_component = vector_store_component
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

    def _chat_engine(
        self,
        system_prompt: str | None = None,
        use_context: bool = False,
        context_filter: ContextFilter | None = None,
    ) -> BaseChatEngine:
        if use_context:
            logger.info(f"Using context for chat engine:{self.settings.rag.similarity_top_k}")
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

            comtext = ContextChatEngine.from_defaults(
                system_prompt=system_prompt,
                retriever=vector_index_retriever,
                llm=self.llm_component.llm,  # Takes no effect at the moment
                node_postprocessors=node_postprocessors,
            )

            # ===== 新增：手动验证retriever的检索结果 =====
            retrieved_nodes = vector_index_retriever.retrieve("你知道什么")
            logger.info(f"手动检索结果：节点数={len(retrieved_nodes)}")
            for node in retrieved_nodes:
                logger.info(f"节点相似度：{node.score}，内容：{node.text[:50]}")
            
            return comtext
            
        else:
            return SimpleChatEngine.from_defaults(
                system_prompt=system_prompt,
                llm=self.llm_component.llm,
            )

    def stream_chat(
        self,
        messages: list[ChatMessage],
        use_context: bool = False,
        context_filter: ContextFilter | None = None,
    ) -> CompletionGen:
        chat_engine_input = ChatEngineInput.from_messages(messages)
        last_message = (
            chat_engine_input.last_message.content
            if chat_engine_input.last_message
            else None
        )
        system_prompt = (
            chat_engine_input.system_message.content
            if chat_engine_input.system_message
            else None
        )
        chat_history = (
            chat_engine_input.chat_history if chat_engine_input.chat_history else None
        )
        chat_engine = self._chat_engine(
            system_prompt=system_prompt,
            use_context=use_context,
            context_filter=context_filter,
        )
        logger.info(f"用户问题:{last_message} ----历史记录： {chat_history}")
        streaming_response = chat_engine.stream_chat(
            message=last_message if last_message is not None else "",
            chat_history=chat_history,
        )
        logger.info(f"streaming_response:{streaming_response}")
        sources = [Chunk.from_node(node) for node in streaming_response.source_nodes]
        completion_gen = CompletionGen(
            response=streaming_response.response_gen, sources=sources
        )
        logger.info(f"sources:{sources}----------completion_gen：{completion_gen}")
        return completion_gen

