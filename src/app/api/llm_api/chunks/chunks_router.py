from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.api.LLM.context_filter import ContextFilter
from app.api.llm_api.chunks.chunks_service import Chunk, ChunksService


chunks_router = APIRouter(prefix="/v1")


class ChunksBody(BaseModel):
    text: str = Field(examples=["Q3 2023 sales"])
    context_filter: ContextFilter | None = None
    limit: int = 10
    prev_next_chunks: int = Field(default=0, examples=[2])


class ChunksResponse(BaseModel):
    object: Literal["list"]
    model: Literal["private-gpt"]
    data: list[Chunk]


@chunks_router.post("/chunks", tags=["Context Chunks"])
def chunks_retrieval(request: Request, body: ChunksBody) -> ChunksResponse:
  
    service = request.state.injector.get(ChunksService)
    results = service.retrieve_relevant(
        body.text, body.context_filter, body.limit, body.prev_next_chunks
    )
    return ChunksResponse(
        object="list",
        model="private-gpt",
        data=results,
    )
