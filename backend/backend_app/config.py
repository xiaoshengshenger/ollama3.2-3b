from typing import Literal, Optional  # 新增 Optional，支持可选字段
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 容器
    #OLLAMA_API_HOST: str = "http://ollama-server:11434"
    # 本地
    OLLAMA_API_HOST: str = "http://localhost:11434"

    # ChatGPT：设为可选（None 表示不用 OpenAI）
    OPENAI_API_KEY: Optional[str] = None  # 可选字段，默认 None

    # LLM 模型：默认 llama3.2:3b（可通过 .env 覆盖，若需要）
    OLLAMA_MODEL: Literal["llama3.2:3b", "llama3.2:7b", "llama3.2:13b"] = "llama3.2:3b"

    EMBEDDING_MODE: Literal["huggingface", "openai", "ollama"] = "huggingface"

    EMBEDDING_HUGGINGFACE_MODEL: str = "BAAI/bge-small-zh"

    QDRANT_HOST: str = Field(default="qdrant-server4", description="Qdrant 服务主机地址")
    QDRANT_PORT: int = Field(default=6333, description="Qdrant 服务端口号")  # 注意是 int 类型，Pydantic 会自动转换环境变量的字符串
    # 前端标题配置（可根据需求调整默认值）
    VITE_APP_TITLE: str = Field(default="PrivateGPT - 卡通 AI 知识库", description="前端应用标题")

    LLM_MODE: str = "ollama"

    class Config:
        env_file = ".env"  
        env_file_encoding = "utf-8" 
        case_sensitive = True


settings = Settings()