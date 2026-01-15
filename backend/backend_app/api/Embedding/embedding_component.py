from llama_index.core.embeddings import BaseEmbedding
#from backend_app.constants import models_cache_path
from injector import singleton
from backend_app.api.settings.settings import settings
from backend_app.api.tools.common import get_local_embedding_model_path
@singleton
class EmbeddingComponent:
    embedding_model: BaseEmbedding

    def __init__(self) -> None:
        embedding_mode = settings().embedding.mode
        print(f"Initializing the embedding model in mode={embedding_mode}")
        match embedding_mode:
            case "huggingface":
                try:
                    from llama_index.embeddings.huggingface import (  # type: ignore
                        HuggingFaceEmbedding,
                    )
                except ImportError as e:
                    raise ImportError(
                        "Local dependencies not found, install with `poetry install --extras embeddings-huggingface`"
                    ) from e
                local_model_path = get_local_embedding_model_path()
                self.embedding_model = HuggingFaceEmbedding(
                    model_name=local_model_path  # 改为本地路径
                )
                '''
                self.embedding_model = HuggingFaceEmbedding(
                    model_name=settings().embedding.huggingface_model,
                    cache_folder=str(models_cache_path),
                    trust_remote_code=True,
                )
                '''