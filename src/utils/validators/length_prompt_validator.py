import tiktoken

from src.core import settings


def is_length_prompt_valid(prompt: str) -> bool:
    if (
        len(tiktoken.encoding_for_model(settings.BASE_AI_MODEL).encode(prompt))
        > settings.MODEL_TOKEN_LIMITS
    ):
        return False

    return True


def get_length_prompt(prompt: str) -> int:
    return len(
        tiktoken.encoding_for_model(settings.BASE_AI_MODEL).encode(prompt)
    )
