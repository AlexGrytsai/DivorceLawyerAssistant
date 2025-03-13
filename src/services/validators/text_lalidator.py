from abc import ABC, abstractmethod
from typing import Dict


class TextBaseValidator(ABC):
    @staticmethod
    @abstractmethod
    def validate_line_length(line: str, max_length: int) -> bool:
        pass

    @staticmethod
    @abstractmethod
    def is_caps_lock_on(line: str) -> bool:
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

    def get_widget_max_length(self, place_of_widget: str) -> int:
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
                if not self.validate_line_length(
                    widget_value, self.get_widget_max_length(place_of_widget)
                ):
                    errors_in_widgets[widget_name] = {
                        "Max length": "Perhaps the line is too long"
                    }

                if self.is_caps_lock_on(widget_value):
                    errors_in_widgets[widget_name] = {
                        "Caps lock": "Caps lock is on"
                    }
        return errors_in_widgets
