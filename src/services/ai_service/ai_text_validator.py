import json
from abc import ABC
from typing import Dict, Union

from openai import (
    AsyncOpenAI,
)

from src.services.ai_service.decorators_for_ai import reconnection_async


class AIBaseValidator(ABC):
    pass


class OpenAITextAnalyzer(AIBaseValidator):
    def __init__(self, openai_client: AsyncOpenAI, openai_model: str) -> None:
        self._openai_client = openai_client
        self._openai_model = openai_model

    @reconnection_async(attempts=10)
    async def analyze_text_with_ai(
        self,
        prompt: str,
        assistant_prompt: str,
    ) -> Dict[str, Union[str, Dict[str, str]]]:
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
            temperature=0.9,
        )

        return json.loads(response.choices[0].message.content)
