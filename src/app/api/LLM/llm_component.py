from injector import singleton
from llama_index.core.llms import LLM
from app.api.settings.settings import settings, OllamaSettings
from collections.abc import Callable
from typing import Any

@singleton
class LLMComponent:
    llm: LLM

    def __init__(self) -> None:
        llm_mode = settings().llm.mode
        print(f"LLM model in mode={llm_mode}")
        match llm_mode:
            case "ollama":
                try:
                    from llama_index.llms.ollama import Ollama  # type: ignore
                except ImportError as e:
                    raise ImportError(
                        "Ollama dependencies not found, install with `poetry install --extras llms-ollama`"
                    ) from e

                ollama_settings = settings().ollama

                settings_kwargs = {
                    "tfs_z": ollama_settings.tfs_z,
                    "num_predict": ollama_settings.num_predict,
                    "top_k": ollama_settings.top_k,
                    "top_p": ollama_settings.top_p,
                    "repeat_last_n": ollama_settings.repeat_last_n,
                    "repeat_penalty": ollama_settings.repeat_penalty,
                }

                # calculate llm model. If not provided tag, it will be use latest
                llm_model = ollama_settings.llm_model
                if ":" not in llm_model:
                    # 条件1：模型名中没有冒号（未指定版本）
                    model_name = llm_model + ":latest"  # 补全为「模型名:latest」
                else:
                    # 条件2：模型名中已有冒号（已指定版本）
                    model_name = llm_model

                llm = Ollama(
                    model=model_name,
                    base_url=ollama_settings.api_base,
                    temperature=ollama_settings.temperature,
                    context_window=ollama_settings.context_window,
                    additional_kwargs=settings_kwargs,
                    request_timeout=ollama_settings.request_timeout,
                )
                

                if ollama_settings.autopull_models:
                    from app.api.utils.pull_ollama_model import check_connection, pull_model

                    if not check_connection(llm.client):
                        raise ValueError(
                            f"Failed to connect to Ollama, "
                            f"check if Ollama server is running on {ollama_settings.api_base}"
                        )
                    print(llm.client + "11111111111111111111111")
                    pull_model(llm.client, model_name)

                if (
                    ollama_settings.keep_alive
                    != OllamaSettings.model_fields["keep_alive"].default
                ):
                    # Modify Ollama methods to use the "keep_alive" field.
                    def add_keep_alive(func: Callable[..., Any]) -> Callable[..., Any]:
                        def wrapper(*args: Any, **kwargs: Any) -> Any:
                            kwargs["keep_alive"] = ollama_settings.keep_alive
                            return func(*args, **kwargs)

                        return wrapper

                    Ollama.chat = add_keep_alive(Ollama.chat)  # type: ignore
                    Ollama.stream_chat = add_keep_alive(Ollama.stream_chat)  # type: ignore
                    Ollama.complete = add_keep_alive(Ollama.complete)  # type: ignore
                    Ollama.stream_complete = add_keep_alive(Ollama.stream_complete)  # type: ignore

                self.llm = llm