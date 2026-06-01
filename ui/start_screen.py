from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from core.project_manager import RECENT_PROJECTS_FILE

# ============================================================
# Create Project Dialog
# ============================================================


class CreateProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Project")
        self.setMinimumWidth(420)
        self._folder = ""

        layout = QVBoxLayout(self)

        form = QFormLayout()

        # project name
        self._name_edit = QLineEdit("MyProject")
        form.addRow("Project Name:", self._name_edit)

        # project type
        self._type_combo = QComboBox()
        self._type_combo.addItems(["3D", "2D"])
        form.addRow("Project Type:", self._type_combo)

        # folder
        folder_row = QHBoxLayout()
        self._folder_edit = QLineEdit(str(Path.home() / "NEXISProjects"))
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse)
        folder_row.addWidget(self._folder_edit)
        folder_row.addWidget(browse_btn)
        form.addRow("Location:", folder_row)

        layout.addLayout(form)

        # preview path label
        self._preview_lbl = QLabel()
        self._preview_lbl.setStyleSheet("color: #888888; font-size: 10px;")
        layout.addWidget(self._preview_lbl)

        self._name_edit.textChanged.connect(self._update_preview)
        self._folder_edit.textChanged.connect(self._update_preview)
        self._update_preview()

        # buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _browse(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Choose Project Location", str(Path.home())
        )
        if folder:
            self._folder_edit.setText(folder)

    def _update_preview(self):
        name = self._name_edit.text().strip() or "MyProject"
        folder = self._folder_edit.text().strip()
        self._preview_lbl.setText(f"→ {folder}/{name}/")

    def result_data(self) -> tuple[str, str, str]:
        """Returns (parent_folder/project_name, name, type)."""
        name = self._name_edit.text().strip() or "MyProject"
        folder = str(Path(self._folder_edit.text().strip()) / name)
        ptype = self._type_combo.currentText()
        return folder, name, ptype


# ============================================================
# Start Screen
# ============================================================


class StartScreen(QWidget):
    def __init__(self, console, create_cb, open_cb, recent_cb):
        super().__init__()
        self.console = console
        self._create_cb = create_cb
        self._open_cb = open_cb
        self._recent_cb = recent_cb

        self.setMinimumSize(800, 500)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(16)

        # title
        title = QLabel("NEXIS")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 48px; font-weight: bold; color: #3c8dde;")
        layout.addWidget(title)

        subtitle = QLabel("Lightweight 2D + 3D Game Engine")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 13px; color: #666666;")
        layout.addWidget(subtitle)

        # buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        create_btn = QPushButton("New Project")
        open_btn = QPushButton("Open Project")
        create_btn.setFixedHeight(44)
        open_btn.setFixedHeight(44)
        create_btn.clicked.connect(self._create_cb)
        open_btn.clicked.connect(self._open_cb)
        btn_row.addWidget(create_btn)
        btn_row.addWidget(open_btn)
        layout.addLayout(btn_row)

        # recent projects
        layout.addWidget(QLabel("Recent Projects"))
        self.recent_list = QListWidget()
        self.recent_list.itemDoubleClicked.connect(self._on_recent_double_clicked)
        layout.addWidget(self.recent_list)

        self.reload_recent()

    def reload_recent(self) -> None:
        self.recent_list.clear()
        items = []
        if RECENT_PROJECTS_FILE.exists():
            try:
                items = json.loads(RECENT_PROJECTS_FILE.read_text(encoding="utf-8"))
            except Exception as exc:
                self.console.warning(f"Could not load recent projects: {exc}")

        if not items:
            self.recent_list.addItem("No recent projects")
            return

        for project in items:
            row = QListWidgetItem(
                f"{project.get('name','?')}   —   {project.get('path','')}"
            )
            row.setData(Qt.UserRole, project.get("path", ""))
            self.recent_list.addItem(row)

    def _on_recent_double_clicked(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.UserRole)
        if path:
            self._recent_cb(path)
