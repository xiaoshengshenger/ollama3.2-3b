from injector import inject, singleton
from llama_index.core.llms import LLM
from app.config import Settings

@singleton
class LLMComponent:
    llm: LLM

    @inject
    def __init__(self, settings: Settings) -> None:
        llm_mode = settings.LLM_MODE
        print(f"Initializing the LLM model in mode={llm_mode}")
        match llm_mode:
            case "ollama":
                try:
                    from llama_index.llms.ollama import Ollama  # type: ignore
                except ImportError as e:
                    raise ImportError(
                        "Ollama dependencies not found, install with `poetry install --extras llms-ollama`"
                    ) from e

                ollama_settings = settings.ollama

                settings_kwargs = {
                    "tfs_z": 0.9,
                    "num_predict": 512,
                    "top_k": 40,
                    "top_p": 0.9,
                    "repeat_last_n": 64,
                    "repeat_penalty": 1.1,
                }

                # calculate llm model. If not provided tag, it will be use latest
                llm_model = settings.OLLAMA_MODEL
                if ":" not in llm_model:
                    # 条件1：模型名中没有冒号（未指定版本）
                    model_name = llm_model + ":latest"  # 补全为「模型名:latest」
                else:
                    # 条件2：模型名中已有冒号（已指定版本）
                    model_name = llm_model

                llm = Ollama(
                    model=model_name,
                    base_url=ollama_settings.api_base,
                    temperature=settings.llm.temperature,
                    context_window=settings.llm.context_window,
                    additional_kwargs=settings_kwargs,
                    request_timeout=ollama_settings.request_timeout,
                )
                

                if ollama_settings.autopull_models:
                    from private_gpt.utils.ollama import check_connection, pull_model

                    if not check_connection(llm.client):
                        raise ValueError(
                            f"Failed to connect to Ollama, "
                            f"check if Ollama server is running on {ollama_settings.api_base}"
                        )
                    logger.info("Initializing9999 the LLM in mode=%s， client=%s", model_name, llm.client)
                    pull_model(llm.client, model_name)

                if (
                    ollama_settings.keep_alive
                    != ollama_settings.model_fields["keep_alive"].default
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