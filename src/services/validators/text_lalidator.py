from abc import ABC, abstractmethod
from typing import Dict


class TextBaseValidator(ABC):

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
        return errors_in_widgets
