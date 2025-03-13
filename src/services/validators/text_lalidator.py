from abc import ABC, abstractmethod
from typing import Dict, Tuple

from email_validator import validate_email, EmailNotValidError


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
    def validate_widgets(
        self, widgets: Dict[str, Dict[str, str]]
    ) -> Dict[str, Dict[str, str]]:
        pass


class TextWidgetValidator(TextBaseValidator):
    MAX_LENGTH_IN_TABLE = 70
    MAX_LENGTH_IN_TEXT = 120

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

    def validate_widgets(
        self, widgets: Dict[str, Dict[str, str]]
    ) -> Dict[str, Dict[str, str]]:
        errors_in_widgets = {}
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

                if self.is_caps_lock_on(widget_value):
                    errors_in_widgets[widget_name] = {
                        "Caps lock": "Caps lock is on"
                    }
        return errors_in_widgets
