from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from backend_app.config import settings
from backend_app.api.settings.settings import settings as settings_yaml
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
# from llama_index.llms.openai import OpenAI
from backend_app.api.api_router import api_router
from backend_app.di import global_injector
from backend_app.api.tools.common import get_local_embedding_model_path, is_model_dir_valid
import os
import sys
import logging

# 配置日志
logger = logging.getLogger(__name__)

def bind_injector_to_request(request: Request):
    request.state.injector = global_injector  # 绑定到request.state
    return request

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 在这里添加启动代码
    print("应用启动中...")
    if settings.OLLAMA_API_HOST:
        # ======================
        # 修改1：加载本地嵌入模型
        # ======================
        local_model_path = get_local_embedding_model_path()
        logger.info(f"全局嵌入模型路径: {local_model_path}")
        
        # 强制本地加载，禁用外网请求
        if not is_model_dir_valid(local_model_path):
            error_msg = f"""
            全局嵌入模型本地目录无效！
            请手动下载BAAI/bge-small-zh模型到：{local_model_path}
            下载地址：https://hf-mirror.com/BAAI/bge-small-zh
            必需文件：config.json、tokenizer.json、pytorch_model.bin
            """
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # 初始化全局嵌入模型
        Settings.embed_model = HuggingFaceEmbedding(
            model_name=local_model_path  # 改为本地路径
        )
        
        Settings.llm = Ollama(
            base_url=settings.OLLAMA_API_HOST,
            model=settings_yaml().ollama.llm_model,
            request_timeout=settings_yaml().ollama.request_timeout
        )
        
    # elif settings.OPENAI_API_KEY:
    #     Settings.llm = OpenAI(model="gpt-4o")

    yield
    # 在这里添加关闭代码
    print("应用关闭中...")

app = FastAPI(
    lifespan=lifespan,
    dependencies=[Depends(bind_injector_to_request)]  # 添加这行
)

app.include_router(router=api_router, prefix='/api/v1')

@app.get("/")
async def root():
    return {
        "message": "Llama3.2 服务启动成功！",
        "ollama_host": settings.OLLAMA_API_HOST,
        "model": settings_yaml().ollama.llm_model,
    }