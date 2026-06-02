from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QTextCursor
from PySide6.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QLabel,
)


class ConsolePanel(QDockWidget):
    """
    Coloured console output with level filter and clear button.
    Levels: INFO (white), WARNING (yellow), ERROR (red).
    """

    COLOURS = {
        "INFO": "#dddddd",
        "WARNING": "#f0c040",
        "ERROR": "#ff5555",
        "SUCCESS": "#55ff88",
        "DEBUG": "#888888",
    }

    def __init__(self, app, parent=None):
        super().__init__("Console", parent)
        self.app = app
        self.setAllowedAreas(Qt.BottomDockWidgetArea)

        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # toolbar
        bar = QWidget()
        bar.setFixedHeight(26)
        bar.setStyleSheet("background:#1a1a1a;")
        bar_row = QHBoxLayout(bar)
        bar_row.setContentsMargins(4, 0, 4, 0)
        bar_row.setSpacing(6)

        bar_row.addWidget(QLabel("Filter:"))
        self._filter = QComboBox()
        self._filter.addItems(["ALL", "INFO", "WARNING", "ERROR"])
        self._filter.setFixedWidth(90)
        self._filter.currentTextChanged.connect(self._apply_filter)
        bar_row.addWidget(self._filter)
        bar_row.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedHeight(20)
        clear_btn.clicked.connect(self.clear)
        bar_row.addWidget(clear_btn)
        layout.addWidget(bar)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFont(QFont("Consolas", 9))
        self._log.setStyleSheet("background:#1a1a1a; border:none;")
        layout.addWidget(self._log)

        self.setWidget(wrapper)
        self._entries: list[tuple[str, str]] = []  # (level, html_line)

    # ------------------------------------------------------------------

    def write(self, level: str, message: str) -> None:
        colour = self.COLOURS.get(level.upper(), "#dddddd")
        html = (
            f'<span style="color:{colour};">' f"[{level.upper()}] {message}</span><br>"
        )
        self._entries.append((level.upper(), html))
        if self._filter.currentText() in ("ALL", level.upper()):
            self._log.moveCursor(QTextCursor.End)
            self._log.insertHtml(html)
            self._log.moveCursor(QTextCursor.End)

    def clear(self) -> None:
        self._entries.clear()
        self._log.clear()

    def _apply_filter(self, level: str) -> None:
        self._log.clear()
        for entry_level, html in self._entries:
            if level == "ALL" or entry_level == level:
                self._log.moveCursor(QTextCursor.End)
                self._log.insertHtml(html)
        self._log.moveCursor(QTextCursor.End)
