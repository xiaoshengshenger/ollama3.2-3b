from fastapi import APIRouter, Request
from backend_app.api.llm_api.llm_model import ChatBody
from starlette.responses import StreamingResponse
from llama_index.core.llms import ChatMessage, MessageRole
from backend_app.api.llm_api.chat.chat_server import ChatService
from backend_app.api.llm_api.llm_model import to_openai_sse_stream

import logging

logger = logging.getLogger(__name__)

chat_router = APIRouter()


@chat_router.post(
    "/completions",
    response_model=None,
    #responses={200: {"model": StreamingResponse}},
    responses={200: {"description": "成功返回流式对话响应", "content": {"text/event-stream": {}}}},
    tags=["Contextual Completions"],
    openapi_extra={
        "x-fern-streaming": {
            "stream-condition": "stream",
            "response": {"$ref": "#/components/schemas/OpenAICompletion"},
            "response-stream": {"$ref": "#/components/schemas/OpenAICompletion"},
        }
    },
)
def chat_completion(
    request: Request, body: ChatBody
) ->  StreamingResponse:
    service = request.state.injector.get(ChatService)
    all_messages = [
        ChatMessage(content=m.content, role=MessageRole(m.role)) for m in body.messages
    ][:-1]
    logger.info(f"asdasdasd:: {all_messages} ---- {body.messages}")
    completion_gen = service.stream_chat(
        messages=all_messages,
        use_context=body.use_context,
        use_hybrid_rag=True,
        context_filter=body.context_filter,
        kg_query_kwargs={
            "similarity_top_k": 2,
            "embedding_mode": "hybrid"
        }
    )
    """
    # 1. 原有纯向量RAG查询（无需改动，兼容原有调用）
    completion = chat_service.stream_chat(
        messages=user_messages,
        use_context=True,
        context_filter=context_filter
    )

    # 2. 纯知识图谱RAG查询（针对关系推理类问题）
    kg_completion = chat_service.stream_chat(
        messages=user_messages,
        use_kg_rag=True,
        kg_query_kwargs={
            "similarity_top_k": 5,
            "response_mode": "tree_summarize"
        }
    )

    # 3. 混合RAG查询（推荐，兼顾细节与关系推理，效果最优）
    hybrid_completion = chat_service.stream_chat(
        messages=user_messages,
        use_context=True,
        use_hybrid_rag=True,
        context_filter=context_filter,
        kg_query_kwargs={
            "similarity_top_k": 5,
            "embedding_mode": "hybrid"
        }
    )
    """
    logger.debug(f"asdasdasd:: {completion_gen.response} ---- {completion_gen.sources}")
    return StreamingResponse(
        to_openai_sse_stream(
            completion_gen.response,
            completion_gen.sources if body.include_sources else None,
        ),
        media_type="text/event-stream",
    )
