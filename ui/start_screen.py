from __future__ import annotations
import json
from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor, QPainter, QLinearGradient
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.theme import (
    ACCENT,
    ACCENT_DIM,
    ACCENT_HOVER,
    BG_HEADER,
    BG_SURFACE,
    BG_RAISED,
    BG_INPUT,
    BORDER,
    BORDER_LIGHT,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    GREEN,
    GREEN_BG,
    GREEN_BORDER,
    accent_btn_style,
    green_btn_style,
)
from core.project_manager import RECENT_PROJECTS_FILE


class _RecentCard(QPushButton):
    def __init__(self, name: str, path: str, callback):
        super().__init__()
        self.setMinimumHeight(130)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {BG_RAISED};
                border: 1px solid {BORDER};
                border-radius: 6px;
                text-align: left;
                padding: 12px 16px;
            }}
            QPushButton:hover {{
                background: #2e2e2e;
                border-color: {ACCENT};
            }}
            QPushButton:pressed {{ background: {BG_SURFACE}; }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(
            f"font-weight: 600; font-size: 13px; color: {TEXT_PRIMARY}; background: transparent; margin-left: 10px;"
        )
        path_lbl = QLabel(path)
        path_lbl.setStyleSheet(
            f"font-size: 11px; color: {TEXT_MUTED}; background: transparent; margin-left: 10px;"
        )
        path_lbl.setWordWrap(True)
        lay.addWidget(name_lbl)
        lay.addWidget(path_lbl)
        self.clicked.connect(lambda: callback(path))


class CreateProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.setFixedSize(460, 260)
        self.setStyleSheet(f"""
            QDialog {{ background: {BG_SURFACE}; }}
            QLabel  {{ color: {TEXT_SECONDARY}; font-size: 12px; }}
        """)
        self._folder = ""

        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        lay.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Create New Project")
        title.setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: {TEXT_PRIMARY}; padding-bottom: 4px; background: {BG_SURFACE};"
        )
        lay.addWidget(title)

        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        input_style = (
            f"background: {BG_INPUT}; border: 1px solid {BORDER_LIGHT}; border-radius: 4px;"
            f"padding: 5px 8px; color: {TEXT_PRIMARY}; font-size: 12px;"
        )

        self._name = QLineEdit("MyProject")
        self._name.setStyleSheet(input_style)
        form.addRow("Name:", self._name)

        self._type = QComboBox()
        self._type.addItems(["3D", "2D"])
        self._type.setStyleSheet(input_style)
        form.addRow("Type:", self._type)

        loc_row = QHBoxLayout()
        self._loc = QLineEdit(str(Path.home() / "NEXISProjects"))
        self._loc.setStyleSheet(input_style)
        browse = QPushButton("…")
        browse.setFixedWidth(32)
        browse.setStyleSheet(
            f"background: {BG_RAISED}; border: 1px solid {BORDER_LIGHT}; border-radius: 4px;"
            f"color: {TEXT_SECONDARY}; padding: 5px;"
        )
        browse.clicked.connect(self._browse)
        loc_row.addWidget(self._loc)
        loc_row.addWidget(browse)
        form.addRow("Location:", loc_row)

        lay.addLayout(form)

        self._preview = QLabel()
        self._preview.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 10px; background: {BG_SURFACE}"
        )
        lay.addWidget(self._preview)
        self._name.textChanged.connect(self._upd)
        self._loc.textChanged.connect(self._upd)
        self._upd()

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setStyleSheet(accent_btn_style())
        btns.button(QDialogButtonBox.Cancel).setStyleSheet(
            f"background: {BG_RAISED}; border: 1px solid {BORDER_LIGHT}; border-radius: 4px;"
            f"padding: 5px 16px; color: {TEXT_SECONDARY};"
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Choose Location", str(Path.home()))
        if d:
            self._loc.setText(d)

    def _upd(self):
        name = self._name.text().strip() or "MyProject"
        self._preview.setText(f"→ {self._loc.text().strip()}/{name}/")

    def result_data(self):
        name = self._name.text().strip() or "MyProject"
        folder = str(Path(self._loc.text().strip()) / name)
        return folder, name, self._type.currentText()


class StartScreen(QWidget):
    def __init__(self, console, create_cb, open_cb, recent_cb):
        super().__init__()
        self.console = console
        self._create_cb = create_cb
        self._open_cb = open_cb
        self._recent_cb = recent_cb

        # Outer shell matches editor BG_BASE so there's no jarring color jump
        self.setStyleSheet(f"background: #1c1c1c;")
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Left sidebar ──────────────────────────────────────────────────
        left = QWidget()
        left.setFixedWidth(300)
        left.setStyleSheet(f"background: #161616; border-right: 1px solid {BORDER};")
        lv = QVBoxLayout(left)
        lv.setContentsMargins(32, 44, 28, 32)
        lv.setSpacing(0)

        logo = QLabel("NEXIS")
        logo.setStyleSheet(
            f"font-size: 40px; font-weight: 900; color: {ACCENT}; letter-spacing: 4px;"
        )
        lv.addWidget(logo)

        sub = QLabel("Game Engine Studio")
        sub.setStyleSheet(
            f"font-size: 11px; color: {TEXT_MUTED}; letter-spacing: 1px; margin-bottom: 24px;"
        )
        lv.addWidget(sub)
        lv.addSpacing(8)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {BORDER}; margin-bottom: 20px;")
        lv.addWidget(sep)
        lv.addSpacing(16)

        def _btn(label, primary=False):
            b = QPushButton(label)
            b.setFixedHeight(38)
            b.setCursor(Qt.PointingHandCursor)
            if primary:
                b.setStyleSheet(accent_btn_style())
            else:
                b.setStyleSheet(
                    f"QPushButton{{background:{BG_RAISED};border:1px solid {BORDER_LIGHT};"
                    f"border-radius:4px;color:{TEXT_PRIMARY};font-size:12px;padding:4px 12px;}}"
                    f"QPushButton:hover{{background:#2e2e2e;border-color:#484848;}}"
                    f"QPushButton:pressed{{background:{BG_SURFACE};}}"
                )
            return b

        new_btn = _btn("New Project", primary=True)
        open_btn = _btn("Open Project…")
        new_btn.clicked.connect(self._create_cb)
        open_btn.clicked.connect(self._open_cb)
        lv.addWidget(new_btn)
        lv.addSpacing(8)
        lv.addWidget(open_btn)
        lv.addStretch()

        ver = QLabel("v0.1-alpha")
        ver.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px;")
        lv.addWidget(ver)
        outer.addWidget(left)

        right = QWidget()
        right.setStyleSheet(f"background: #1c1c1c;")
        rv = QVBoxLayout(right)
        rv.setContentsMargins(40, 40, 40, 40)
        rv.setSpacing(6)

        hdr = QLabel("Recent Projects")
        hdr.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {TEXT_PRIMARY};")
        rv.addWidget(hdr)

        desc = QLabel("Open an existing project or start a new one.")
        desc.setStyleSheet(
            f"font-size: 12px; color: {TEXT_MUTED}; margin-bottom: 16px;"
        )
        rv.addWidget(desc)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setStyleSheet("background: transparent; border: none;")
        self._grid_w = QWidget()
        self._grid_w.setStyleSheet("background: transparent;")
        self._grid = QGridLayout(self._grid_w)
        self._grid.setSpacing(10)
        self._grid.setAlignment(Qt.AlignTop)
        self._grid.setColumnStretch(0, 1)
        self._scroll.setWidget(self._grid_w)
        rv.addWidget(self._scroll, 1)

        self._empty_lbl = QLabel(
            "No recent projects.\nCreate or open a project to get started."
        )
        self._empty_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
        self._empty_lbl.setAlignment(Qt.AlignCenter)
        rv.addWidget(self._empty_lbl)
        self._empty_lbl.hide()

        outer.addWidget(right, 1)
        self.reload_recent()

    def reload_recent(self) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        items = []
        if RECENT_PROJECTS_FILE.exists():
            try:
                items = json.loads(RECENT_PROJECTS_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass

        if not items:
            self._empty_lbl.show()
            return
        self._empty_lbl.hide()

        for i, proj in enumerate(items[:12]):
            card = _RecentCard(
                proj.get("name", "Untitled Project"),
                proj.get("path", ""),
                self._recent_cb,
            )
            self._grid.addWidget(card, i, 0)
