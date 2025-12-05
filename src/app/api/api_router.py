from fastapi import APIRouter

from app.api.llm_api import chat, files, health, meta, models

api_router = APIRouter()

api_router.include_router(chat.router, prefix="/chat",tags=["chat"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(meta.router, prefix="/meta", tags=["meta"])
api_router.include_router(models.router, prefix="/models", tags=["health"])