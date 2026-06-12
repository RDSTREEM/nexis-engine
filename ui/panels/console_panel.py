"""
console_panel.py — Reworked.
Consistent header bar. Fixed near-invisible timestamp color.
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

from ui.theme import (
    BG_SURFACE,
    BG_INPUT,
    BG_HEADER,
    BORDER,
    BORDER_LIGHT,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    PANEL_TOOLBAR_H,
)


class ConsolePanel(QDockWidget):
    COLOURS = {
        "INFO": ("#c8c8c8", "#1a1a1a"),
        "WARNING": ("#e0a030", "#1e1500"),
        "ERROR": ("#e05555", "#1e0a0a"),
        "SUCCESS": ("#4caf72", "#0a1e12"),
        "DEBUG": ("#666666", "#111111"),
    }

    def __init__(self, app, parent=None):
        super().__init__("Console", parent)
        self.app = app
        self.setAllowedAreas(Qt.BottomDockWidgetArea)

        wrapper = QWidget()
        wrapper.setStyleSheet(f"background: {BG_SURFACE};")
        lay = QVBoxLayout(wrapper)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # ── Toolbar ───────────────────────────────────────────────────
        bar = QWidget()
        bar.setFixedHeight(PANEL_TOOLBAR_H)
        bar.setStyleSheet(
            f"background: {BG_HEADER}; border-bottom: 1px solid {BORDER};"
        )
        br = QHBoxLayout(bar)
        br.setContentsMargins(10, 0, 8, 0)
        br.setSpacing(6)

        lbl = QLabel("Level:")
        lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        br.addWidget(lbl)

        self._filter = QComboBox()
        self._filter.addItems(["ALL", "INFO", "WARNING", "ERROR"])
        self._filter.setFixedWidth(80)
        self._filter.setFixedHeight(22)
        self._filter.setStyleSheet(
            f"QComboBox{{background:{BG_INPUT};border:1px solid {BORDER_LIGHT};"
            f"border-radius:3px;padding:1px 6px;color:{TEXT_SECONDARY};font-size:11px;}}"
        )
        self._filter.currentTextChanged.connect(self._apply_filter)
        br.addWidget(self._filter)
        br.addStretch()

        self._count_lbl = QLabel("0 messages")
        self._count_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        br.addWidget(self._count_lbl)

        btn_style = (
            f"QPushButton{{background:transparent;border:1px solid transparent;"
            f"border-radius:3px;color:{TEXT_MUTED};padding:0 8px;font-size:11px;height:22px;}}"
            f"QPushButton:hover{{background:#2a2a2a;border-color:{BORDER_LIGHT};color:{TEXT_SECONDARY};}}"
        )
        copy_btn = QPushButton("Copy")
        copy_btn.setStyleSheet(btn_style)
        copy_btn.clicked.connect(
            lambda: __import__("PySide6.QtWidgets", fromlist=["QApplication"])
            .QApplication.clipboard()
            .setText(self._log.toPlainText())
        )
        br.addWidget(copy_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet(btn_style)
        clear_btn.clicked.connect(self.clear)
        br.addWidget(clear_btn)

        lay.addWidget(bar)

        # ── Log area ──────────────────────────────────────────────────
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFont(QFont("Consolas", 9))
        self._log.setStyleSheet(
            f"QTextEdit{{background:{BG_SURFACE};border:none;color:{TEXT_PRIMARY};padding:4px 8px;}}"
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
        # Timestamp uses #666 (was #333 — near-invisible)
        html = (
            f'<span style="color:#666;">{ts}</span> '
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
