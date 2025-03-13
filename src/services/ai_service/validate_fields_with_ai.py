import json
from abc import ABC
from typing import Dict

from openai import (
    AsyncOpenAI,
)

from src.core import settings
from src.services.ai_service.decorators_for_ai import reconnection_async


class AIBaseValidator(ABC):
    pass


class OpenaiFieldValidator(AIBaseValidator):
    def __init__(self, openai_client: AsyncOpenAI) -> None:
        self._openai_client = openai_client

    @reconnection_async(attempts=10)
    async def analyze_field_value_with_ai(
        self,
        prompt: str,
        assistant_description: str,
    ) -> Dict[str, str]:
        response = await self._openai_client.chat.completions.create(
            model=settings.BASE_AI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": assistant_description,
                },
                {"role": "user", "content": prompt},
            ],
        )

        return json.loads(response.choices[0].message.content)
