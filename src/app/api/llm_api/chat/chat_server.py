from app.config import Settings
from injector import inject, singleton
from app.api.Embedding.embedding_component import EmbeddingComponent



@singleton
class ChatService:
    settings: Settings

    @inject
    def __init__(
        self,
        settings: Settings,
        llm_component: LLMComponent,
        vector_store_component: VectorStoreComponent,
        embedding_component: EmbeddingComponent,
        node_store_component: NodeStoreComponent,
    ) -> None:
        self.settings = settings
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
        settings = self.settings
        if use_context:
            vector_index_retriever = self.vector_store_component.get_retriever(
                index=self.index,
                context_filter=context_filter,
                similarity_top_k=self.settings.rag.similarity_top_k,
            )
            node_postprocessors: list[BaseNodePostprocessor] = [
                MetadataReplacementPostProcessor(target_metadata_key="window"),
            ]
            if settings.rag.similarity_value:
                node_postprocessors.append(
                    SimilarityPostprocessor(
                        similarity_cutoff=settings.rag.similarity_value
                    )
                )

            if settings.rag.rerank.enabled:
                rerank_postprocessor = SentenceTransformerRerank(
                    model=settings.rag.rerank.model, top_n=settings.rag.rerank.top_n
                )
                node_postprocessors.append(rerank_postprocessor)

            return ContextChatEngine.from_defaults(
                system_prompt=system_prompt,
                retriever=vector_index_retriever,
                llm=self.llm_component.llm,  # Takes no effect at the moment
                node_postprocessors=node_postprocessors,
            )
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
        streaming_response = chat_engine.stream_chat(
            message=last_message if last_message is not None else "",
            chat_history=chat_history,
        )
        sources = [Chunk.from_node(node) for node in streaming_response.source_nodes]
        completion_gen = CompletionGen(
            response=streaming_response.response_gen, sources=sources
        )
        return completion_gen

