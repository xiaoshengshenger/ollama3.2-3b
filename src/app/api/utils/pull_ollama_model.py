import logging
from collections import deque
from collections.abc import Iterator, Mapping
from typing import Any

from httpx import ConnectError
from tqdm import tqdm  # type: ignore

from app.api.utils.retry import retry

try:
    from ollama import Client, ResponseError  # type: ignore
except ImportError as e:
    raise ImportError(
        "Ollama dependencies not found, install with `poetry install --extras llms-ollama or embeddings-ollama`"
    ) from e

logger = logging.getLogger(__name__)

_MAX_RETRIES = 5
_JITTER = (3.0, 10.0)


@retry(
    is_async=False,
    exceptions=(ConnectError, ResponseError),
    tries=_MAX_RETRIES,
    jitter=_JITTER,
    logger=logger,
)
def check_connection(client: Client) -> bool:
    try:
        client.list()
        return True
    except (ConnectError, ResponseError) as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to connect to Ollama: {type(e).__name__}: {e!s}")
        return False


def process_streaming(generator: Iterator[Mapping[str, Any]]) -> None:
    progress_bars = {}
    queue = deque()  # type: ignore

    def create_progress_bar(dgt: str, total: int) -> Any:
        return tqdm(
            total=total, desc=f"Pulling model {dgt[7:17]}...", unit="B", unit_scale=True
        )

    current_digest = None

    for chunk in generator:
        digest = chunk.get("digest")
        completed_size = chunk.get("completed", 0)
        total_size = chunk.get("total")

        if digest and total_size is not None:
            if digest not in progress_bars and (completed_size or 0) > 0:
                progress_bars[digest] = create_progress_bar(digest, total=total_size)
                if current_digest is None:
                    current_digest = digest
                else:
                    queue.append(digest)

            if digest in progress_bars:
                progress_bar = progress_bars[digest]
                progress = completed_size - progress_bar.n
                if completed_size > 0 and total_size >= progress != progress_bar.n:
                    if digest == current_digest:
                        progress_bar.update(progress)
                        if progress_bar.n >= total_size:
                            progress_bar.close()
                            current_digest = queue.popleft() if queue else None
                    else:
                        # Store progress for later update
                        progress_bars[digest].total = total_size
                        progress_bars[digest].n = completed_size

    # Close any remaining progress bars at the end
    for progress_bar in progress_bars.values():
        progress_bar.close()


def pull_model(client: Client, model_name: str, raise_error: bool = True) -> None:
    try:
        models_response = client.list()
        print(f"Ollama list 接口返回：{models_response}")

        logger.info(f"Pulling model {model_name}. Please wait...")
        installed_models = [model["model"] for model in models_response.get("models", [])]
        if model_name not in installed_models:
            process_streaming(client.pull(model_name, stream=True))     
    except Exception as e:
        logger.error(f"Failed to pull model {model_name}: {e!s}")
        if raise_error:
            raise e
