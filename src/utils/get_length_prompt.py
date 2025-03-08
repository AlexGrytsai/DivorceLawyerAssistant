import tiktoken

from src.core import settings


def get_length_prompt(prompt: str) -> int:
    return len(
        tiktoken.encoding_for_model(settings.OPENAI_MODEL).encode(prompt)
    )
