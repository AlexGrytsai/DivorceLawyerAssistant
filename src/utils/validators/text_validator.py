import json
import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Tuple, Union

import pymupdf as fitz
from email_validator import validate_email, EmailNotValidError

from src.services.ai_service.ai_text_validator import (
    OpenAITextAnalyzer,
    AIBaseValidator,
)
from src.services.ai_service.prompts import GET_ADDRESS_PHONE_NUMBER_PROMPT

logger = logging.getLogger(__name__)


class TextBaseValidator(ABC):
    @staticmethod
    @abstractmethod
    async def validate_line_length(
        widget_instance: fitz.Widget,
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

    @staticmethod
    @abstractmethod
    async def address_validator(email: str) -> Tuple[bool, str]:
        pass

    @abstractmethod
    async def validate_widgets(
        self, widgets: Dict[str, Dict[str, str]]
    ) -> Dict[str, str]:
        pass


class TextWidgetValidatorUseAI(TextBaseValidator):
    def __init__(self, ai_assistant: OpenAITextAnalyzer) -> None:
        self._ai_assistant = ai_assistant
        self._errors_in_widgets = {}

    @staticmethod
    async def validate_line_length(
        widget_instance: fitz.Widget,
    ) -> Tuple[bool, str]:
        widget_value_char_width = fitz.Font("Helvetica").text_length(
            widget_instance.field_value, widget_instance.text_fontsize
        )
        if widget_value_char_width > widget_instance.rect.width:
            return False, "Line length is too long"
        return True, ""

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

    @staticmethod
    async def address_validator(address: str) -> Tuple[bool, str]:
        full_address_pattern = re.compile(
            r"^(?P<number>\d+)\s+"
            r"(?P<street>[A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\s"
            r"(?P<type>Road|Rd|Street|St|Avenue|Ave|Boulevard|Blvd|Lane|Ln|"
            r"Drive|Dr|Court|Ct|Place|Pl|Terrace|Ter)\s*"
            r"(?P<direction>N|S|E|W|NE|NW|SE|SW)?\s+"
            r"(?P<city>[A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\s*,\s*"
            r"(?P<state>[A-Z]{2})\s+"
            r"(?P<zip>\d{5}(?:-\d{4})?)$"
        )

        street_address_pattern = re.compile(
            r"^(?P<number>\d+)\s+"
            r"(?P<street>[A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\s"
            r"(?P<type>Road|Rd|Street|St|Avenue|Ave|Boulevard|Blvd|Lane|Ln|"
            r"Drive|Dr|Court|Ct|Place|Pl|Terrace|Ter)\s*"
            r"(?P<direction>N|S|E|W|NE|NW|SE|SW)?$"
        )

        city_state_zip_pattern = re.compile(
            r"^(?P<city>[A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\s*,\s*"
            r"(?P<state>[A-Z]{2})\s+"
            r"(?P<zip>\d{5}(?:-\d{4})?)$"
        )

        if full_address_pattern.match(address):
            return True, "Valid full address"

        if street_address_pattern.match(address):
            return True, "Valid street address"

        if city_state_zip_pattern.match(address):
            return True, "Valid city, state, and ZIP"

        if "," in address and not re.search(r"\b[A-Z]{2}\b", address):
            return False, "State abbreviation is missing or incorrect"

        if "," in address and not re.search(r"\b\d{5}(-\d{4})?\b$", address):
            return False, "ZIP code is missing or incorrect"

        if re.search(r"^\d+", address) and not re.search(
            r"\b(Road|Rd|Street|St|Avenue|Ave|Boulevard|Blvd|Lane|Ln|"
            r"Drive|Dr|Court|Ct|Place|Pl|Terrace|Ter)\b",
            address,
        ):
            return False, "Street type is missing or incorrect"

        return False, "Invalid address format"

    async def validate_widgets(
        self, widgets: Dict[str, Dict[str, Union[str, fitz.Widget]]]
    ) -> Dict[str, str]:
        widgets_for_ai = {}
        for widget_name, values_dict in widgets.items():
            if values_dict.get("value"):
                widget_value, widget_instance = (
                    values_dict["value"],
                    values_dict["widget_instance"],
                )
                if "email" in widget_name:
                    is_valid_email, error_message = await self.email_validator(
                        widget_value
                    )
                    if not is_valid_email:
                        logger.debug(f"{widget_name}: {error_message}")
                        await self._add_error_to_dict(
                            widget_name, error_message
                        )
                else:
                    is_valid_length, error_message = (
                        await self.validate_line_length(widget_instance)
                    )
                    if not is_valid_length:
                        logger.debug(f"{widget_name}: {error_message}")
                        await self._add_error_to_dict(
                            widget_name, error_message
                        )

                    is_caps_locked, caps_message = await self.is_caps_lock_on(
                        widget_value
                    )
                    if is_caps_locked:
                        logger.debug(f"{widget_name}: {error_message}")
                        await self._add_error_to_dict(
                            widget_name, caps_message
                        )

                    widgets_for_ai[widget_name] = widget_value

        address_dates_phones = await self._check_widget_data_with_ai(
            widgets=widgets_for_ai,
            ai_assistant=self._ai_assistant,
            assistant_prompt=GET_ADDRESS_PHONE_NUMBER_PROMPT,
        )
        if address_dates_phones.get("dates"):
            for widget_name, date in address_dates_phones["dates"].items():
                is_valid_date, error_message = await self.date_validator(date)
                if not is_valid_date:
                    logger.debug(f"{widget_name}: {error_message}")
                    await self._add_error_to_dict(widget_name, error_message)

        if address_dates_phones.get("addresses"):
            for widget_name, address in address_dates_phones[
                "addresses"
            ].items():
                is_valid_address, error_message = await self.address_validator(
                    address
                )
                if not is_valid_address:
                    logger.debug(f"{widget_name}: {error_message}")
                    await self._add_error_to_dict(widget_name, error_message)

        if address_dates_phones.get("phone_numbers"):
            for widget_name, phone_number in address_dates_phones[
                "phone_numbers"
            ].items():
                is_valid_phone, error_message = (
                    await self.phone_number_validator(phone_number)
                )
                if not is_valid_phone:
                    logger.debug(f"{widget_name}: {error_message}")
                    await self._add_error_to_dict(widget_name, error_message)

        return self._errors_in_widgets

    @staticmethod
    async def _check_widget_data_with_ai(
        widgets: Dict[str, str],
        ai_assistant: AIBaseValidator,
        assistant_prompt: str,
    ) -> Dict[str, Dict[str, str]]:
        if widgets:
            prompt = (
                f"Analyze the following JSON dictionary:\n"
                f"{json.dumps(widgets)}"
            )
            address_dates_phones = await ai_assistant.analyze_text(
                prompt=prompt,
                assistant_prompt=assistant_prompt,
            )
            return address_dates_phones

        return {}

    async def _add_error_to_dict(
        self,
        widget_name: str,
        error_message: str,
    ) -> None:
        if not self._errors_in_widgets.get(widget_name):
            self._errors_in_widgets[widget_name] = error_message
        else:
            self._errors_in_widgets[widget_name] += f"\n{error_message}"
