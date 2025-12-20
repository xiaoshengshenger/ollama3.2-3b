from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from backend_app.config import settings
from backend_app.api.settings.settings import settings as settings_yaml
#
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
#from llama_index.llms.openai import OpenAI
from backend_app.api.api_router import api_router
from backend_app.di import global_injector 


def bind_injector_to_request(request: Request):
    request.state.injector = global_injector  # 绑定到request.state
    return request

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 在这里添加启动代码
    print("应用启动中...")
    if settings.OLLAMA_API_HOST:
        Settings.embed_model = HuggingFaceEmbedding(model_name=settings_yaml().embedding.huggingface_model,)
        Settings.llm = Ollama(base_url=settings.OLLAMA_API_HOST, model=settings_yaml().ollama.llm_model, request_timeout=settings_yaml().ollama.request_timeout)
        
        
    #elif settings.OPENAI_API_KEY:
        #Settings.llm = OpenAI(model="gpt-4o")

    yield
    # 在这里添加关闭代码
    print("应用关闭中...")

app = FastAPI(
    lifespan=lifespan,
    dependencies=[Depends(bind_injector_to_request)]  # 添加这行
)

app.include_router(router=api_router,prefix='/api/v1')

@app.get("/")
async def root():
    return {
        "message": "Llama3.2 服务启动成功！",
        "ollama_host": settings.OLLAMA_API_HOST,
        "model": settings_yaml().ollama.llm_model,
    }