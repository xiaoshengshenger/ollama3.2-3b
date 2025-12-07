from pydantic import BaseModel, Field
from app.api.LLM.context_filter import ContextFilter
from typing import Literal
from llama_index.core.llms import ChatResponse, CompletionResponse
from app.api.llm_api.chunks.chunks_service import Chunk
from collections.abc import Iterator
import time
import uuid

class OpenAIDelta(BaseModel):
    """A piece of completion that needs to be concatenated to get the full message."""

    content: str | None

class OpenAIMessage(BaseModel):
    role: Literal["assistant", "system", "user"] = Field(default="user")
    content: str | None

class OpenAIChoice(BaseModel):

    finish_reason: str | None = Field(examples=["stop"])
    delta: OpenAIDelta | None = None
    message: OpenAIMessage | None = None
    sources: list[Chunk] | None = None
    index: int = 0

#前端传过来的参数结构
class ChatBody(BaseModel):
    messages: list[OpenAIMessage]
    use_context: bool = False
    context_filter: ContextFilter | None = None
    include_sources: bool = True
    stream: bool = False

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a rapper. Always answer with a rap.",
                        },
                        {
                            "role": "user",
                            "content": "How do you fry an egg?",
                        },
                    ],
                    "stream": False,
                    "use_context": True,
                    "include_sources": True,
                    "context_filter": {
                        "docs_ids": ["c202d5e6-7b69-4869-81cc-dd574ee8ee11"]
                    },
                }
            ]
        }
    }

class OpenAICompletion(BaseModel):
    """Clone of OpenAI Completion model.

    For more information see: https://platform.openai.com/docs/api-reference/chat/object
    """

    id: str
    object: Literal["completion", "completion.chunk"] = Field(default="completion")
    created: int = Field(..., examples=[1623340000])
    model: Literal["private-gpt"]
    choices: list[OpenAIChoice]

    @classmethod
    def from_text(
        cls,
        text: str | None,
        finish_reason: str | None = None,
        sources: list[Chunk] | None = None,
    ) -> "OpenAICompletion":
        return OpenAICompletion(
            id=str(uuid.uuid4()),
            object="completion",
            created=int(time.time()),
            model="private-gpt",
            choices=[
                OpenAIChoice(
                    message=OpenAIMessage(role="assistant", content=text),
                    finish_reason=finish_reason,
                    sources=sources,
                )
            ],
        )

    @classmethod
    def json_from_delta(
        cls,
        *,
        text: str | None,
        finish_reason: str | None = None,
        sources: list[Chunk] | None = None,
    ) -> str:
        chunk = OpenAICompletion(
            id=str(uuid.uuid4()),
            object="completion.chunk",
            created=int(time.time()),
            model="private-gpt",
            choices=[
                OpenAIChoice(
                    delta=OpenAIDelta(content=text),
                    finish_reason=finish_reason,
                    sources=sources,
                )
            ],
        )

        return chunk.model_dump_json()

def to_openai_sse_stream(
    response_generator: Iterator[str | CompletionResponse | ChatResponse],
    sources: list[Chunk] | None = None,
) -> Iterator[str]:
    for response in response_generator:
        if isinstance(response, CompletionResponse | ChatResponse):
            yield f"data: {OpenAICompletion.json_from_delta(text=response.delta)}\n\n"
        else:
            yield f"data: {OpenAICompletion.json_from_delta(text=response, sources=sources)}\n\n"
    yield f"data: {OpenAICompletion.json_from_delta(text='', finish_reason='stop')}\n\n"
    yield "data: [DONE]\n\n"