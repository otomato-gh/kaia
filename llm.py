import os
from autogen_ext.models.ollama import OllamaChatCompletionClient

from pydantic import BaseModel


class StructuredOutput(BaseModel):
    tool_command: str
    tool_result: str


def get_llm():
    """Get the chat model instance configured via environment variables."""
    model_provider = os.getenv('LLM_PROVIDER', 'ollama')
    model_name = os.getenv('MODEL_NAME', 'mistral')
    
    if model_provider.lower() == 'ollama':
        return OllamaChatCompletionClient(model=model_name, keep_alive="60m", response_format=StructuredOutput)
    else:
        raise ValueError(f"Unsupported model provider: {model_provider}") 