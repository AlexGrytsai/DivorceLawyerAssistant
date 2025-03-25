import tiktoken

from src.core import settings


def is_length_prompt_valid(prompt: str) -> bool:
    token_limit = settings.get_token_limit
    if token_limit <= 0:
        return False
    prompt_length = len(
        tiktoken.encoding_for_model(settings.BASE_AI_MODEL).encode(prompt)
    )
    return prompt_length <= token_limit


def get_length_prompt(prompt: str) -> int:
    return len(
        tiktoken.encoding_for_model(settings.BASE_AI_MODEL).encode(prompt)
    )
