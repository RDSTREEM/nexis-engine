from typing import Optional

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QTextEdit
from rich.console import Console as RichConsole


class EngineConsole:
    """Engine-wide console that mirrors logs to both rich and the Qt UI."""

    def __init__(self):
        self.rich_console = RichConsole()
        self.ui_widget: Optional[QTextEdit] = None

    def set_ui_widget(self, widget: QTextEdit) -> None:
        self.ui_widget = widget
        self.info("Console connected to UI widget.")

    def _append_to_ui(self, text: str) -> None:
        if self.ui_widget is None:
            return
        self.ui_widget.append(text)
        cursor = self.ui_widget.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.ui_widget.setTextCursor(cursor)

    def info(self, message: str) -> None:
        formatted = f"[INFO] {message}"
        self.rich_console.log(formatted)
        self._append_to_ui(formatted)

    def warning(self, message: str) -> None:
        formatted = f"[WARNING] {message}"
        self.rich_console.log(formatted)
        self._append_to_ui(formatted)

    def error(self, message: str) -> None:
        formatted = f"[ERROR] {message}"
        self.rich_console.log(formatted)
        self._append_to_ui(formatted)
