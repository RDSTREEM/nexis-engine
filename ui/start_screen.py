"""
start_screen.py — Professional reworked start screen.
Clean, minimal, dark aesthetic with grid of recent projects.
"""

from __future__ import annotations
import json
from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QFont
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
from core.project_manager import RECENT_PROJECTS_FILE


class _RecentCard(QPushButton):
    def __init__(self, name: str, path: str, callback):
        super().__init__()
        self.setFixedHeight(72)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background: #1e1e1e;
                border: 1px solid #333;
                border-radius: 6px;
                text-align: left;
                padding: 10px 14px;
            }
            QPushButton:hover {
                background: #252525;
                border-color: #3c8dde;
            }
            QPushButton:pressed { background: #1a1a1a; }
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(
            "font-weight:600; font-size:12px; color:#e0e0e0; background:transparent;"
        )
        path_lbl = QLabel(path)
        path_lbl.setStyleSheet("font-size:9px; color:#555; background:transparent;")
        path_lbl.setWordWrap(True)
        lay.addWidget(name_lbl)
        lay.addWidget(path_lbl)
        self.clicked.connect(lambda: callback(path))


class CreateProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.setFixedSize(460, 260)
        self.setStyleSheet("QDialog{background:#1e1e1e;} QLabel{color:#ccc;}")
        self._folder = ""

        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        title = QLabel("Create New Project")
        title.setStyleSheet(
            "font-size:16px;font-weight:700;color:#fff;padding-bottom:4px;"
        )
        lay.addWidget(title)

        form = QFormLayout()
        form.setSpacing(8)

        self._name = QLineEdit("MyProject")
        self._name.setStyleSheet(
            "background:#2a2a2a;border:1px solid #444;border-radius:4px;"
            "padding:6px 8px;color:#fff;font-size:12px;"
        )
        form.addRow("Name:", self._name)

        self._type = QComboBox()
        self._type.addItems(["3D", "2D"])
        self._type.setStyleSheet(
            "background:#2a2a2a;border:1px solid #444;border-radius:4px;"
            "padding:4px 8px;color:#fff;font-size:12px;"
        )
        form.addRow("Type:", self._type)

        loc_row = QHBoxLayout()
        self._loc = QLineEdit(str(Path.home() / "NEXISProjects"))
        self._loc.setStyleSheet(
            "background:#2a2a2a;border:1px solid #444;border-radius:4px;"
            "padding:6px 8px;color:#fff;font-size:12px;"
        )
        browse = QPushButton("…")
        browse.setFixedWidth(32)
        browse.setStyleSheet(
            "background:#333;border:1px solid #444;border-radius:4px;"
            "color:#ccc;padding:6px;"
        )
        browse.clicked.connect(self._browse)
        loc_row.addWidget(self._loc)
        loc_row.addWidget(browse)
        form.addRow("Location:", loc_row)

        lay.addLayout(form)

        self._preview = QLabel()
        self._preview.setStyleSheet("color:#555;font-size:10px;")
        lay.addWidget(self._preview)
        self._name.textChanged.connect(self._upd)
        self._loc.textChanged.connect(self._upd)
        self._upd()

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setStyleSheet(
            "background:#3c8dde;border:none;border-radius:4px;"
            "padding:6px 20px;color:#fff;font-weight:600;"
        )
        btns.button(QDialogButtonBox.Cancel).setStyleSheet(
            "background:#333;border:1px solid #444;border-radius:4px;"
            "padding:6px 20px;color:#ccc;"
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

        self.setStyleSheet("background:#161616;")
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Left panel
        left = QWidget()
        left.setFixedWidth(280)
        left.setStyleSheet("background:#111;border-right:1px solid #222;")
        lv = QVBoxLayout(left)
        lv.setContentsMargins(32, 48, 32, 32)
        lv.setSpacing(8)

        logo = QLabel("NEXIS")
        logo.setStyleSheet(
            "font-size:42px;font-weight:900;color:#3c8dde;" "letter-spacing:3px;"
        )
        lv.addWidget(logo)

        sub = QLabel("Game Engine")
        sub.setStyleSheet(
            "font-size:11px;color:#444;letter-spacing:1px;margin-bottom:24px;"
        )
        lv.addWidget(sub)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#222;margin-bottom:16px;")
        lv.addWidget(sep)

        def _btn(label, primary=False):
            b = QPushButton(label)
            b.setFixedHeight(40)
            if primary:
                b.setStyleSheet("""
                    QPushButton{background:#3c8dde;border:none;border-radius:5px;
                    color:#fff;font-size:12px;font-weight:600;}
                    QPushButton:hover{background:#4a9de8;}
                    QPushButton:pressed{background:#2e7bc4;}""")
            else:
                b.setStyleSheet("""
                    QPushButton{background:#1e1e1e;border:1px solid #333;border-radius:5px;
                    color:#bbb;font-size:12px;}
                    QPushButton:hover{background:#252525;border-color:#555;}
                    QPushButton:pressed{background:#181818;}""")
            return b

        new_btn = _btn("New Project", primary=True)
        open_btn = _btn("Open Project…")
        new_btn.clicked.connect(self._create_cb)
        open_btn.clicked.connect(self._open_cb)
        lv.addWidget(new_btn)
        lv.addWidget(open_btn)
        lv.addStretch()

        ver = QLabel("v0.1-alpha")
        ver.setStyleSheet("color:#333;font-size:9px;")
        lv.addWidget(ver)
        outer.addWidget(left)

        # Right panel — recent projects
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(40, 40, 40, 40)
        rv.setSpacing(16)

        hdr = QLabel("Recent Projects")
        hdr.setStyleSheet("font-size:18px;font-weight:600;color:#ddd;")
        rv.addWidget(hdr)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setStyleSheet("background:transparent;border:none;")
        self._grid_w = QWidget()
        self._grid_w.setStyleSheet("background:transparent;")
        self._grid = QGridLayout(self._grid_w)
        self._grid.setSpacing(10)
        self._grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._scroll.setWidget(self._grid_w)
        rv.addWidget(self._scroll, 1)

        self._empty_lbl = QLabel(
            "No recent projects.\nCreate or open a project to get started."
        )
        self._empty_lbl.setStyleSheet("color:#444;font-size:12px;")
        self._empty_lbl.setAlignment(Qt.AlignCenter)
        rv.addWidget(self._empty_lbl)
        self._empty_lbl.hide()

        outer.addWidget(right, 1)
        self.reload_recent()

    def reload_recent(self) -> None:
        # Clear grid
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

        cols = 2
        for i, proj in enumerate(items[:12]):
            card = _RecentCard(
                proj.get("name", "?"),
                proj.get("path", ""),
                self._recent_cb,
            )
            self._grid.addWidget(card, i // cols, i % cols)
