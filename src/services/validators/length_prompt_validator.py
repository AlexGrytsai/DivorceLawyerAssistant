import tiktoken

from src.core import settings


def get_length_prompt(prompt: str) -> bool:
    if (
        len(tiktoken.encoding_for_model(settings.BASE_AI_MODEL).encode(prompt))
        > settings.MODEL_TOKEN_LIMITS
    ):
        return False

    return True
