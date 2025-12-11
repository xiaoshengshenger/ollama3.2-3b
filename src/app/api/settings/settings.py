from pydantic import BaseModel
from typing import Literal
from app.api.settings.settings_load import load_active_settings


class EmbeddingSettings(BaseModel):
    mode:  Literal[
        "huggingface",
    ]
    huggingface_model: Literal[
        "BAAI/bge-small-zh",
    ]
    ingest_mode: Literal[
        "simple",
    ]
    embed_dim: int

class LlmSettings(BaseModel):
    mode: Literal[
        "ollama",
    ]
    ollama_model: Literal[
        "llama3.2:3b",
        "llama3.2:7b",
        "llama3.2:13b",
        "llama3.2:70b",
    ]

class OllamaSettings(BaseModel):
    llm_model: Literal[
        "llama3.2:3b",
        "llama3.2:7b",
        "llama3.2:13b",
        "llama3.2:70b",
    ]
    embedding_model: Literal[
        "nomic-embed-text",
    ]
    api_base: str
    embedding_api_base: str
    tfs_z: float    
    top_k: int
    top_p: float
    num_predict: int
    repeat_last_n: int
    repeat_penalty: float
    request_timeout: int
    autopull_models: bool
    temperature: float
    context_window: int
    keep_alive: Literal["0s", "5m", "30m", "1h", "none", "load"] = "5m"   

class VectorStoreSettings(BaseModel):
    database: Literal[
        "qdrant",
    ]

class QdrantSettings(BaseModel):    
    path: str   

class NodeStoreSettings(BaseModel):
    database: Literal[
        "simple",
    ]

class DataSettings(BaseModel):
    local_data_folder: str

class rerankSettings(BaseModel):
    enabled:  bool
    model: str
    top_n: int

class RAGSettings(BaseModel):
    similarity_top_k: int
    similarity_value: float | None = None
    rerank: rerankSettings

class Settings(BaseModel):
    embedding: EmbeddingSettings
    llm: LlmSettings
    ollama: OllamaSettings
    vectorstore: VectorStoreSettings
    qdrant: QdrantSettings | None = None
    nodestore: NodeStoreSettings
    data: DataSettings
    rag: RAGSettings


unsafe_settings = load_active_settings()

unsafe_typed_settings = Settings(**unsafe_settings)

def settings() -> Settings:

    from app.di import global_injector

    return global_injector.get(Settings)