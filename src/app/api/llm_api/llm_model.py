from pydantic import BaseModel


#前端传过来的参数结构
class ChatBody(BaseModel):
    messages: list[OpenAIMessage]
    use_context: bool = False
    context_filter: ContextFilter | None = None
    include_sources: bool = True
    stream: bool = False

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a rapper. Always answer with a rap.",
                        },
                        {
                            "role": "user",
                            "content": "How do you fry an egg?",
                        },
                    ],
                    "stream": False,
                    "use_context": True,
                    "include_sources": True,
                    "context_filter": {
                        "docs_ids": ["c202d5e6-7b69-4869-81cc-dd574ee8ee11"]
                    },
                }
            ]
        }
    }