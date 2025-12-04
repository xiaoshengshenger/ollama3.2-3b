from typing import Literal, Optional  # 新增 Optional，支持可选字段

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Ollama API：本地默认地址（无需手动配置，启动 Ollama 后直接用）
    OLLAMA_API_HOST: str = "http://localhost:11434"

    # ChatGPT：设为可选（None 表示不用 OpenAI）
    OPENAI_API_KEY: Optional[str] = None  # 可选字段，默认 None

    # LLM 模型：默认 llama3.2:3b（可通过 .env 覆盖，若需要）
    OLLAMA_MODEL: Literal["llama3.2:3b", "llama3.2:7b", "llama3.2:13b"] = "llama3.2:3b"

    class Config:
        env_file = ".env"  
        env_file_encoding = "utf-8" 


settings = Settings()