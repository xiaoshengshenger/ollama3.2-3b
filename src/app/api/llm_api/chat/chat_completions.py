from fastapi import APIRouter, Request
from app.api.llm_api.llm_model import ChatBody
from starlette.responses import StreamingResponse
from llama_index.core.llms import ChatMessage, MessageRole
from app.api.llm_api.chat.chat_server import ChatService
from app.api.llm_api.llm_model import to_openai_sse_stream

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
    ]
    completion_gen = service.stream_chat(
        messages=all_messages,
        use_context=body.use_context,
        context_filter=body.context_filter,
    )
    logger.debug(f"asdasdasd:: {completion_gen.response} ---- {completion_gen.sources}")
    return StreamingResponse(
        to_openai_sse_stream(
            completion_gen.response,
            completion_gen.sources if body.include_sources else None,
        ),
        media_type="text/event-stream",
    )
