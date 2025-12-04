from contextlib import asynccontextmanager
from fastapi import FastAPI
from .config import settings

#
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
#from llama_index.llms.openai import OpenAI

#
from .api.api_router import test

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 在这里添加启动代码
    print("应用启动中...")
    if settings.OLLAMA_API_HOST:
        Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-base-en-v1.5")
        Settings.llm = Ollama(base_url=settings.OLLAMA_API_HOST, model=settings.OLLAMA_MODEL, request_timeout=10000.0)
        
    #elif settings.OPENAI_API_KEY:
        #Settings.llm = OpenAI(model="gpt-4o")

    yield
    # 在这里添加关闭代码
    print("应用关闭中...")

app = FastAPI(lifespan=lifespan)

app.include_router(test, prefix='/api/v1')

@app.get("/")
async def root():
    return {
        "message": "Llama3.2 服务启动成功！",
        "ollama_host": settings.OLLAMA_API_HOST,
        "model": settings.OLLAMA_MODEL
    }