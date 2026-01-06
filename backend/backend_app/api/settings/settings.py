from pydantic import BaseModel, Field
from typing import Literal
from backend_app.api.settings.settings_load import load_active_settings

class Neo4jSettings(BaseModel):
    """Neo4j 连接配置"""
    username: str = Field(default="neo4j", description="Neo4j用户名",env="NEO4J_USER")
    password: str = Field(default="12345678", description="Neo4j密码",env="NEO4J_PASSWORD")
    url: str = Field(default="neo4j://127.0.0.1:7687", description="Neo4j连接地址",env="NEO4J_URL")
    database: str = Field(default="neo4j", description="Neo4j数据库名",env="NEO4J_DB")
    clear_existing_data: bool = Field(default=True, description="是否清空Neo4j历史数据",env="NEO4J_CLEAR_EXISTING_DATA")
    max_triplets_per_chunk: int = Field(default=3, description="每个文档块提取的最大三元组数量",env="NEO4J_MAX_TRIPLETS")
    include_embeddings: bool = Field(default=True, description="是否启用嵌入混合检索",env="NEO4J_INCLUDE_EMBEDDINGS")

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
    api_base: str = Field(
        # 容器
        #default="http://ollama-server:11434",  
        # 本地
        default="http://localhost:11434",# 本地开发默认值
        env="OLLAMA_HOST",  # 绑定Docker的环境变量OLLAMA_HOST
        description="Ollama server base URL"
    )
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
    local_kg_data_folder: str

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
    neo4j: Neo4jSettings
    vectorstore: VectorStoreSettings
    qdrant: QdrantSettings | None = None
    nodestore: NodeStoreSettings
    data: DataSettings
    rag: RAGSettings


unsafe_settings = load_active_settings()

unsafe_typed_settings = Settings(**unsafe_settings)

def settings() -> Settings:

    from backend_app.di import global_injector

    return global_injector.get(Settings)