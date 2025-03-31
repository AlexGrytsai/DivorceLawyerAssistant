import json
from abc import ABC, abstractmethod
from typing import Dict

from openai import (
    AsyncOpenAI,
)

from src.core.config import settings
from src.services.ai_service.decorators import reconnection_async

BASE_AI_CLIENT = AsyncOpenAI(api_key=settings.OPENAI_API_KEY, max_retries=5)


class AIBaseValidator(ABC):
    @abstractmethod
    async def analyze_text(
        self, prompt: str, assistant_prompt: str
    ) -> Dict[str, Dict[str, str]]:
        pass


class OpenAITextAnalyzer(AIBaseValidator):
    __slots__ = ("_openai_client", "_openai_model")

    def __init__(
        self,
        openai_client: AsyncOpenAI = BASE_AI_CLIENT,
        openai_model: str = settings.BASE_AI_MODEL,
    ) -> None:
        self._openai_client = openai_client
        self._openai_model = openai_model

    @reconnection_async(attempts=10)
    async def analyze_text(
        self,
        prompt: str,
        assistant_prompt: str,
    ) -> Dict[str, Dict[str, str]]:
        response = await self._openai_client.chat.completions.create(
            model=self._openai_model,
            messages=[
                {
                    "role": "system",
                    "content": assistant_prompt,
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=1,
        )
        if response.choices[0].message.content:
            return json.loads(response.choices[0].message.content)
        return {}
