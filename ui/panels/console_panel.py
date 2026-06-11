"""
console_panel.py — Reworked: coloured log levels, timestamps, copy button.
"""

from __future__ import annotations
import time

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QComboBox,
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ConsolePanel(QDockWidget):
    COLOURS = {
        "INFO": ("#c8c8c8", "#1a1a1a"),
        "WARNING": ("#f0c040", "#1a1500"),
        "ERROR": ("#ff6060", "#1a0800"),
        "SUCCESS": ("#55dd88", "#001a0a"),
        "DEBUG": ("#666666", "#111111"),
    }

    def __init__(self, app, parent=None):
        super().__init__("Console", parent)
        self.app = app
        self.setAllowedAreas(Qt.BottomDockWidgetArea)

        wrapper = QWidget()
        wrapper.setStyleSheet("background:#141414;")
        lay = QVBoxLayout(wrapper)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # toolbar
        bar = QWidget()
        bar.setFixedHeight(28)
        bar.setStyleSheet("background:#111;border-bottom:1px solid #1e1e1e;")
        br = QHBoxLayout(bar)
        br.setContentsMargins(8, 0, 8, 0)
        br.setSpacing(6)

        br.addWidget(QLabel("Level:"))
        self._filter = QComboBox()
        self._filter.addItems(["ALL", "INFO", "WARNING", "ERROR"])
        self._filter.setFixedWidth(80)
        self._filter.setStyleSheet(
            "QComboBox{background:#1a1a1a;border:1px solid #2a2a2a;"
            "border-radius:3px;padding:1px 6px;color:#aaa;font-size:10px;}"
        )
        self._filter.currentTextChanged.connect(self._apply_filter)
        br.addWidget(self._filter)
        br.addStretch()

        self._count_lbl = QLabel("0 messages")
        self._count_lbl.setStyleSheet("color:#444;font-size:10px;")
        br.addWidget(self._count_lbl)

        copy_btn = QPushButton("Copy")
        copy_btn.setFixedHeight(20)
        copy_btn.setStyleSheet(
            "QPushButton{background:#1e1e1e;border:1px solid #333;"
            "border-radius:3px;color:#888;padding:0 8px;font-size:10px;}"
            "QPushButton:hover{background:#252525;color:#aaa;}"
        )
        copy_btn.clicked.connect(
            lambda: __import__("PySide6.QtWidgets", fromlist=["QApplication"])
            .QApplication.clipboard()
            .setText(self._log.toPlainText())
        )
        br.addWidget(copy_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedHeight(20)
        clear_btn.setStyleSheet(copy_btn.styleSheet())
        clear_btn.clicked.connect(self.clear)
        br.addWidget(clear_btn)
        lay.addWidget(bar)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFont(QFont("Consolas", 9))
        self._log.setStyleSheet(
            "QTextEdit{background:#141414;border:none;color:#aaa;" "padding:4px 8px;}"
        )
        lay.addWidget(self._log)

        self.setWidget(wrapper)
        self._entries: list[tuple[str, str]] = []

    # ── Public ───────────────────────────────────────────────────────

    def log_widget(self) -> QTextEdit:
        return self._log

    def write(self, level: str, message: str) -> None:
        lvl = level.upper()
        fg, bg = self.COLOURS.get(lvl, ("#c8c8c8", "#1a1a1a"))
        ts = time.strftime("%H:%M:%S")
        lvl_pad = f"{lvl:<8}"
        html = (
            f'<span style="color:#333;">{ts}</span> '
            f'<span style="color:{fg};background:{bg};'
            f'padding:1px 4px;border-radius:2px;font-size:9px;">{lvl_pad}</span> '
            f'<span style="color:{fg};">{message}</span><br>'
        )
        self._entries.append((lvl, html))
        if self._filter.currentText() in ("ALL", lvl):
            self._log.moveCursor(QTextCursor.End)
            self._log.insertHtml(html)
            self._log.moveCursor(QTextCursor.End)
        self._count_lbl.setText(f"{len(self._entries)} messages")

    def clear(self) -> None:
        self._entries.clear()
        self._log.clear()
        self._count_lbl.setText("0 messages")

    def _apply_filter(self, level: str) -> None:
        self._log.clear()
        for entry_lvl, html in self._entries:
            if level == "ALL" or entry_lvl == level:
                self._log.moveCursor(QTextCursor.End)
                self._log.insertHtml(html)
        self._log.moveCursor(QTextCursor.End)
