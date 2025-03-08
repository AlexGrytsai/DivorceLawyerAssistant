import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime

import tiktoken
from dotenv import load_dotenv
from fastapi import HTTPException, status
from openai import (
    AsyncOpenAI,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    RateLimitError,
)

from src.core import settings

load_dotenv()

logger = logging.getLogger(__name__)


class AIAnalyzerBase(ABC):
    @abstractmethod
    async def analyze_pdf_with_ai(
        self, document_text: str, us_state: str
    ) -> None:
        pass


class OpenAIAnalyzerService(AIAnalyzerBase):

    def __init__(self, ai_client: AsyncOpenAI) -> None:
        self._client = ai_client

    @staticmethod
    def _is_validate_length_prompt(prompt: str) -> bool:
        length_tokens_prompt = len(
            tiktoken.encoding_for_model(settings.OPENAI_MODEL).encode(prompt)
        )

        if length_tokens_prompt > settings.get_token_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Prompt is too long: {length_tokens_prompt} tokens. "
                f"Max tokens: {settings.get_token_limit}",
            )

        return True

    async def analyze_pdf_with_ai(
        self,
        document_text: str,
        us_state: str,
    ) -> None:
        start_analyzing_code = datetime.now()

        try:

            prompt = (
                f"You are a divorce attorney assistant in the state "
                f"of {us_state}. Your task is to check the correctness "
                f"of the form, which was converted from a PDF file into "
                f"a string. The fields in the form are provided as a list, "
                f"where each field is represented as "
                f"[{{field_name}}: {{field_value}}]. "
                f"If a field is not filled in, the value will be 'N/A'. "
                f"For Checkbox fields, if selected, it will appear "
                f"as [{{field_name}}: ON], if not selected — "
                f"[{{field_name}}: OFF].\n\n"
                f"Pay special attention to very long values in the fields — "
                f"they may be the result of errors during the PDF conversion, "
                f"potentially leading to incorrect data display.\n\n"
                f"Your task is to return a report in the form of a dictionary,"
                f" containing only the fields where errors have occurred. "
                f"The structure of the dictionary should be as follows:\n\n"
                f"field_name: "
                f"{{describe mistake: str, propose how to fix: str}}\n\n"
                f"Return the data without special characters or formatting.\n\n"
                f"Here is the document for review:\n"
                f"{document_text}"
            )

            if self._is_validate_length_prompt(prompt):

                number_retry_connection = 10

                while True:
                    try:
                        response = await self._client.chat.completions.create(
                            model=settings.OPENAI_MODEL,
                            messages=[
                                {
                                    "role": "system",
                                    "content": "You are a code review assistant.",
                                },
                                {"role": "user", "content": prompt},
                            ],
                        )

                        review = response.choices[0].message.content
                        review_json = json.loads(review)

                        end_analyzing_code = datetime.now()
                        time_taken = end_analyzing_code - start_analyzing_code
                        logger.info(
                            f"Time taken to analyze code with OpenAI: {time_taken}"
                        )
                        return review_json

                    except APITimeoutError:
                        if number_retry_connection == 0:
                            logger.critical(
                                "Request timeout for OpenAI. Service unavailable."
                            )
                            raise HTTPException(
                                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                                detail="Request timeout. Please try again later.",
                            )
                        else:
                            number_retry_connection -= 1
                            logger.info(
                                f"Timeout error for OpenAI. "
                                f"Retrying ({number_retry_connection}. "
                                f"Left {number_retry_connection})"
                            )
                    except (
                        AuthenticationError,
                        InternalServerError,
                        RateLimitError,
                    ) as exc:
                        logger.critical(exc)
                        raise HTTPException(
                            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Service unavailable. Please try again later.",
                        )

        except HTTPException as exc:
            raise exc
