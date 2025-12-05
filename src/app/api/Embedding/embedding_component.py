from llama_index.core.embeddings import BaseEmbedding
from app.config import Settings
from app.constants import models_cache_path
from injector import inject, singleton
@singleton
class EmbeddingComponent:
    embedding_model: BaseEmbedding

    @inject
    def __init__(self, settings: Settings) -> None:
        embedding_mode = settings.EMBEDDING_MODE
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

                self.embedding_model = HuggingFaceEmbedding(
                    model_name=settings.HUGGINGFACE_EMBEDDING_MODEL,
                    cache_folder=str(models_cache_path),
                    trust_remote_code=True,
                )