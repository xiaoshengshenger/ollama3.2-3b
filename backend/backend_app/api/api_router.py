from fastapi import APIRouter

from backend_app.api.llm_api.chat.chat_completions import chat_router
from backend_app.api.llm_api.ingest.ingest_router import ingest_router
from backend_app.api.llm_api.meta.meta_router import meta_router

api_router = APIRouter()

api_router.include_router(chat_router, prefix="/chat",tags=["chat"])
api_router.include_router(ingest_router, prefix="/ingest", tags=["ingest"])
api_router.include_router(meta_router, prefix="/meta", tags=["meta"])
#api_router.include_router(health.router, prefix="/health", tags=["health"])
#api_router.include_router(meta.router, prefix="/meta", tags=["meta"])
#api_router.include_router(models.router, prefix="/models", tags=["health"])