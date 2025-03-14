import json
from abc import ABC, abstractmethod
from typing import Dict, Tuple, AnyStr, Union

from email_validator import validate_email, EmailNotValidError
from openai import AsyncOpenAI

from src.services.ai_service.ai_text_validator import (
    OpenAITextAnalyzer,
    AIBaseValidator,
)
from src.services.ai_service.prompts import VALIDATE_DATA_FORMAT_PROMPT


class TextBaseValidator(ABC):
    @staticmethod
    @abstractmethod
    def validate_line_length(line: str, max_length: int) -> bool:
        pass

    @staticmethod
    @abstractmethod
    def is_caps_lock_on(line: str) -> bool:
        pass

    @staticmethod
    @abstractmethod
    def email_validator(email: str) -> bool:
        pass

    @abstractmethod
    def address_validator(self, address: str) -> bool:
        pass

    @abstractmethod
    def phone_number_validator(self, phone_number: str) -> bool:
        pass

    @abstractmethod
    def validate_widgets(
        self, widgets: Dict[str, Dict[str, str]]
    ) -> Dict[str, Dict[str, str]]:
        pass


class TextWidgetValidatorUseAI(TextBaseValidator):
    MAX_LENGTH_IN_TABLE = 70
    MAX_LENGTH_IN_TEXT = 120

    def __init__(self, ai_assistant: OpenAITextAnalyzer) -> None:
        self._ai_assistant = ai_assistant

    @staticmethod
    def validate_line_length(line: str, max_length: int) -> bool:
        return len(line) <= max_length

    @staticmethod
    def is_caps_lock_on(line: str) -> bool:
        return line.isupper()

    @staticmethod
    def email_validator(email: str) -> Tuple[bool, str]:
        try:
            validate_email(email, check_deliverability=True)
            if not email.islower():
                return False, "Email should be in lowercase"
            return True, ""
        except EmailNotValidError as exc:
            return False, str(exc)

    def _get_widget_max_length(self, place_of_widget: str) -> int:
        if place_of_widget == "Table":
            return self.MAX_LENGTH_IN_TABLE
        elif place_of_widget == "Text":
            return self.MAX_LENGTH_IN_TEXT
        raise ValueError(f"Unknown widget type: {place_of_widget}")

    @staticmethod
    async def _check_widget_with_ai(
        widgets: Dict[str, str],
        ai_assistant: AIBaseValidator,
        assistant_prompt: str,
    ) -> Dict[str, Union[str, Dict[str, str]]]:
        prompt = (
            f"Analyze the following data and return a JSON object with "
            f"errors only:\n"
            f"{json.dumps(widgets)}\n"
            f"Check if addresses, dates, and phone numbers are correctly "
            f"formatted according to U.S. official document standards."
        )
        errors = await ai_assistant.analyze_text(
            prompt=prompt,
            assistant_prompt=assistant_prompt,
        )

        return errors

    async def validate_widgets(
        self, widgets: Dict[str, Dict[str, str]]
    ) -> Dict[str, Dict[str, str]]:
        errors_in_widgets = {}
        widgets_for_ai = {}
        for place_of_widget, value in widgets.items():
            for widget_name, widget_value in value.items():
                if "email" in widget_name:
                    is_valid_email, error_message = self.email_validator(
                        widget_value
                    )
                    if not is_valid_email:
                        errors_in_widgets[widget_name] = {
                            "Email": error_message
                        }
                elif not self.validate_line_length(
                    widget_value, self._get_widget_max_length(place_of_widget)
                ):
                    errors_in_widgets[widget_name] = {
                        "Max length": "Perhaps the line is too long"
                    }

                elif self.is_caps_lock_on(widget_value):
                    errors_in_widgets[widget_name] = {
                        "Caps lock": "Caps lock is on"
                    }
                else:
                    widgets_for_ai[widget_name] = widget_value
        await self._check_widget_with_ai(
            widgets=widgets_for_ai,
            ai_assistant=self._ai_assistant,
            assistant_prompt=VALIDATE_DATA_FORMAT_PROMPT,
        )
        return errors_in_widgets
