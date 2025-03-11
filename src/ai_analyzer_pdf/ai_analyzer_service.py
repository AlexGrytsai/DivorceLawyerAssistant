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
from openai.types.shared_params.response_format_json_object import (
    ResponseFormatJSONObject,
)


from src.core import settings
from src.utils.get_length_prompt import get_length_prompt

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
        instruction_for_document: str = "",
    ) -> None:
        start_analyzing_code = datetime.now()

        try:
            # prompt = (
            #     f"You are a divorce attorney assistant in the state of {us_state}. "
            #     f"Your task is to check the correctness of a legal form that was converted from a PDF file into a string. "
            #     f"The fields in the form are provided as a list, where each field is represented as "
            #     f"[{{field name}}: {{field value}}]. "
            #     f"If a field is not filled in, the 'field value' will be 'N/A'. "
            #     f"For Checkbox fields, if selected, it will appear as [{{field name}}: ON], if not selected — [{{field name}}: OFF].\n\n"
            #     f"### Instructions for Validation:\n"
            #     f"1. **Only check the values of fields, NOT their names.**\n"
            #     f"   - Do NOT modify field names.\n"
            #     f"2. **Only report real errors, do not change correct values.**\n"
            #     f"   - If a value is already valid, do NOT suggest a correction.\n"
            #     f"   - Do NOT suggest changes related to capitalization (e.g., 'BREVARD' is fine and does NOT need to be changed to 'Brevard').\n"
            #     f"3. **Ensure all field values comply with the provided form rules. Here are the rules: {instruction_for_document}**\n"
            #     f"   - Pay close attention to incorrect or missing values.\n"
            #     f"4. **Check for errors caused by incorrect PDF conversion.**\n"
            #     f"   - Errors may include missing table data, incorrect character recognition, or misplaced content.\n"
            #     f"5. **Verify the correctness of specific field formats (for the USA):**\n"
            #     f"   - **Addresses** should follow a standard format but DO NOT modify capitalization.\n"
            #     f"   - **Phone numbers** should be valid U.S. numbers but DO NOT change their format if already valid.\n"
            #     f"   - **Emails** should be in a correct format, but minor variations (e.g., uppercase vs lowercase) are acceptable.\n"
            #     f"   - **Dates** must be in MM/DD/YYYY format, but do NOT change them if they are already in this format.\n\n"
            #     f"### Output Format:\n"
            #     f"Return a dictionary containing only the fields where errors were detected. The dictionary structure should be:\n"
            #     f"```\n"
            #     f"{{\n"
            #     f"    'field_name': {{'describe mistake': '...', 'propose how to fix': '...'}},\n"
            #     f"    'another_field': {{'describe mistake': '...', 'propose how to fix': '...'}},\n"
            #     f"}}\n"
            #     f"```\n"
            #     f"- **DO NOT modify or validate field names. Only check their values.**\n"
            #     f"- **DO NOT include correctly filled fields in the output.**\n"
            #     f"- **DO NOT propose changes that do not actually fix an error.**\n\n"
            #     f"### Document for Review:\n"
            #     f"{document_text}"
            # )

            # prompt = (
            #     f"You are a divorce attorney assistant in the state "
            #     f"of {us_state}. Your task is to check the correctness "
            #     f"of the form, which was converted from a PDF file into "
            #     f"a string. The fields in the form are provided as a list, "
            #     f"where each field is represented as "
            #     f"[{{field_name}}: {{field_value}}]. "
            #     f"If a field is not filled in, the value will be 'N/A'. "
            #     f"For Checkbox fields, if selected, it will appear "
            #     f"as [{{field_name}}: ON], if not selected — "
            #     f"[{{field_name}}: OFF].\n\n"
            #     f"Pay attention to the values in the fields that are in the tables — "
            #     f"they may be the result of errors during the PDF conversion, "
            #     f"potentially leading to incorrect data display.\n\n"
            #     f"Your task is to return a report in the form of a dictionary,"
            #     f" containing only the fields where errors have occurred. "
            #     f"The structure of the dictionary should be as follows:\n\n"
            #     f"field_name: "
            #     f"{{describe mistake: str, propose how to fix: str}}\n\n"
            #     f"Important: The `field_name` in the returned dictionary must exactly "
            #     f"match the name of the field as it appears in the form (i.e., the text "
            #     f"provided in the format [{{field_name}}: {{field_value}}]).\n\n"
            #     f"Also, do not check the correctness of any names or surnames. "
            #     f"Your task is to focus on other fields, especially where errors might have occurred due to PDF conversion.\n\n"
            #     f"Additionally, please ensure that the following fields have the correct format (for USA):\n"
            #     f"- Address (should follow a valid address format)\n"
            #     f"- Phone number (should follow a valid phone number format)\n"
            #     f"- Email (should follow a valid email format)\n\n"
            #     f"Return the data without special characters or formatting. Only return the dictionary.\n\n"
            #     f"Here is the rules for how to need fill the document:\n"
            #     f"{instruction_for_document}\n\n"
            #     f"Here is the document for review:\n"
            #     f"{document_text}"
            # )

            prompt = (
                f"You are a divorce lawyer assistant in the state "
                f"of {us_state}. Your task is to check the correctness "
                f"of the document, which was converted from a PDF file into "
                f"a string. The fields in the form are provided as a list, "
                f"where each field is represented as "
                f"[{{field_name}}: {{field_value}}]. "
                f"If a field is not filled in, the value will be 'N/A'. "
                f"For Checkbox fields, if selected, it will appear "
                f"as [{{field_name}}: ON], if not selected — "
                f"[{{field_name}}: OFF].\n\n"
                # f"Pay attention to the values in the fields that are in the tables — "
                # f"they may be the result of errors during the PDF conversion, "
                # f"potentially leading to incorrect data display.\n\n"
                f"Your task is to return a report in the form of a dictionary,"
                f" containing only the fields where errors have occurred. "
                f"The structure of the dictionary should be as follows:\n\n"
                f"field_name: "
                f"{{describe mistake: str, propose how to fix: str}}\n\n"
                f"Important: The `field_name` in the returned dictionary must exactly "
                f"match the name of the field as it appears in the form (i.e., the text "
                f"provided in the format [{{field_name}}: {{field_value}}]).\n\n"
                f"Also, do not check the correctness of any names or surnames. "
                # f"Your task is to focus on other fields, especially where errors might have occurred due to PDF conversion.\n\n"
                f"Additionally, please ensure that the following fields have the correct format for USA:\n"
                f"- Address (should follow a valid address format)\n"
                f"- Phone number (should follow a valid phone number format)\n"
                f"- Email (should follow a valid email format)\n\n"
                # f"Return the data without special characters or formatting. "
                f"Add information that the document is also indicated and filled out in accordance with the rules that were provided."
                f"Only return the dictionary.\n\n"
                # f"Here are the rules how to fill out the document:\n"
                # f"{instruction_for_document}.\nCheck or document filled in accordance with these rules.\n\n"
                f"Here is the document for review:\n"
                f"{document_text}"
            )
            if self._is_validate_length_prompt(prompt):

                number_retry_connection = 10

                while True:
                    try:
                        response = await self._client.chat.completions.create(
                            model=settings.OPENAI_MODEL,
                            temperature=0.2,
                            top_p=1,
                            n=1,
                            messages=[
                                {
                                    "role": "system",
                                    "content": f"You are a divorce lawyer assistant in the state of {us_state}.",
                                },
                                {"role": "user", "content": prompt},
                            ],
                        )

                        review = response.choices[0].message.content
                        # review_json = json.loads(response.choices[0].message.content)

                        end_analyzing_code = datetime.now()
                        time_taken = end_analyzing_code - start_analyzing_code
                        logger.info(
                            f"Time taken to analyze code with OpenAI: {time_taken}"
                        )
                        return review

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
