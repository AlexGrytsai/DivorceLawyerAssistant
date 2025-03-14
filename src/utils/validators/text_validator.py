import json
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Tuple

from email_validator import validate_email, EmailNotValidError

from src.services.ai_service.ai_text_validator import (
    OpenAITextAnalyzer,
    AIBaseValidator,
)
from src.services.ai_service.prompts import GET_ADDRESS_PHONE_NUMBER_PROMPT


class TextBaseValidator(ABC):
    @staticmethod
    @abstractmethod
    async def validate_line_length(
        line: str, max_length: int
    ) -> Tuple[bool, str]:
        pass

    @staticmethod
    @abstractmethod
    async def is_caps_lock_on(line: str) -> Tuple[bool, str]:
        pass

    @staticmethod
    @abstractmethod
    async def email_validator(email: str) -> Tuple[bool, str]:
        pass

    @staticmethod
    @abstractmethod
    async def date_validator(email: str) -> Tuple[bool, str]:
        pass

    @staticmethod
    @abstractmethod
    async def phone_number_validator(email: str) -> Tuple[bool, str]:
        pass

    @abstractmethod
    async def validate_widgets(
        self, widgets: Dict[str, Dict[str, str]]
    ) -> Dict[str, str]:
        pass


class TextWidgetValidatorUseAI(TextBaseValidator):
    MAX_LENGTH_IN_TABLE = 70
    MAX_LENGTH_IN_TEXT = 120

    def __init__(self, ai_assistant: OpenAITextAnalyzer) -> None:
        self._ai_assistant = ai_assistant

    @staticmethod
    async def validate_line_length(
        line: str, max_length: int
    ) -> Tuple[bool, str]:
        if len(line) <= max_length:
            return True, ""
        return False, "Line length is too long"

    @staticmethod
    async def is_caps_lock_on(line: str) -> Tuple[bool, str]:
        if line.isupper():
            return True, "Caps lock is on"
        return False, ""

    @staticmethod
    async def email_validator(email: str) -> Tuple[bool, str]:
        try:
            validate_email(email, check_deliverability=True)
            if not email.islower():
                return (
                    False,
                    "All letters in the email address must be lowercase.",
                )
            return True, ""
        except EmailNotValidError as exc:
            return False, str(exc)

    @staticmethod
    async def date_validator(date_str: str) -> Tuple[bool, str]:
        print(date_str)
        try:
            datetime.strptime(date_str, "%m/%d/%Y")
            return True, ""
        except ValueError:
            pass

        try:
            datetime.strptime(date_str, "%B %d, %Y")
            return True, ""
        except ValueError:
            pass

        return False, "The date is indicated in the wrong format"

    @staticmethod
    async def phone_number_validator(phone_number: str) -> Tuple[bool, str]:
        pattern = r"^\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$"

        if re.match(pattern, phone_number):
            return True, ""
        return False, "Phone number is not valid"

    async def validate_widgets(
        self, widgets: Dict[str, Dict[str, str]]
    ) -> Dict[str, str]:
        errors_in_widgets = {}
        widgets_for_ai = {}
        for place_of_widget, value in widgets.items():
            for widget_name, widget_value in value.items():
                if "email" in widget_name:
                    is_valid_email, error_message = await self.email_validator(
                        widget_value
                    )
                    if not is_valid_email:
                        errors_in_widgets[widget_name] = error_message
                else:
                    is_valid_length, error_message = (
                        await self.validate_line_length(
                            widget_value,
                            self._widget_max_length(place_of_widget),
                        )
                    )
                    if not is_valid_length:
                        errors_in_widgets[widget_name] = error_message

                    is_caps_locked, caps_message = await self.is_caps_lock_on(
                        widget_value
                    )
                    if is_caps_locked:
                        errors_in_widgets[widget_name] = caps_message
                    elif is_valid_length and not is_caps_locked:
                        widgets_for_ai[widget_name] = widget_value

        address_dates_phones = await self._check_widget_data_with_ai(
            widgets=widgets_for_ai,
            ai_assistant=self._ai_assistant,
            assistant_prompt=GET_ADDRESS_PHONE_NUMBER_PROMPT,
        )
        if address_dates_phones.get("dates"):
            for date in address_dates_phones["dates"].values():
                is_valid_date, error_message = await self.date_validator(date)
                if not is_valid_date:
                    errors_in_widgets[date] = error_message

        if address_dates_phones.get("addresses"):
            pass

        if address_dates_phones.get("phone_numbers"):
            for phone_number in address_dates_phones["phone_numbers"].values():
                is_valid_phone, error_message = (
                    await self.phone_number_validator(phone_number)
                )
                if not is_valid_phone:
                    errors_in_widgets[phone_number] = error_message

        return errors_in_widgets

    @staticmethod
    async def _check_widget_data_with_ai(
        widgets: Dict[str, str],
        ai_assistant: AIBaseValidator,
        assistant_prompt: str,
    ) -> Dict[str, Dict[str, str]]:
        prompt = (
            f"Analyze the following JSON dictionary:\n"
            f"{json.dumps(widgets)}"
        )
        address_dates_phones = await ai_assistant.analyze_text(
            prompt=prompt,
            assistant_prompt=assistant_prompt,
        )

        return address_dates_phones

    def _widget_max_length(self, place_of_widget: str) -> int:
        if place_of_widget == "Table":
            return self.MAX_LENGTH_IN_TABLE
        elif place_of_widget == "Text":
            return self.MAX_LENGTH_IN_TEXT
        raise ValueError(f"Unknown widget type: {place_of_widget}")
