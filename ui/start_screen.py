import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ProjectTypeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose Project Type")
        self.setMinimumWidth(320)
        self.type_result = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select a project type:"))

        self.button_2d = QPushButton("2D")
        self.button_3d = QPushButton("3D")
        self.button_2d.clicked.connect(self._choose_2d)
        self.button_3d.clicked.connect(self._choose_3d)

        layout.addWidget(self.button_2d)
        layout.addWidget(self.button_3d)

        buttons = QDialogButtonBox(QDialogButtonBox.Cancel)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _choose_2d(self):
        self.type_result = "2D"
        self.accept()

    def _choose_3d(self):
        self.type_result = "3D"
        self.accept()

    def selected_type(self):
        return self.type_result


class StartScreen(QWidget):
    def __init__(self, console, create_callback, open_callback, recent_callback):
        super().__init__()
        self.console = console
        self.create_callback = create_callback
        self.open_callback = open_callback
        self.recent_callback = recent_callback

        self.setMinimumSize(800, 500)
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)

        title = QLabel("Welcome to NEXIS")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: bold;")
        main_layout.addWidget(title)

        subtitle = QLabel("Create or open a project to begin.")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #666666;")
        main_layout.addWidget(subtitle)

        button_create = QPushButton("Create Project")
        button_open = QPushButton("Open Project")
        button_create.setFixedHeight(48)
        button_open.setFixedHeight(48)
        button_create.clicked.connect(self._on_create_project)
        button_open.clicked.connect(self._on_open_project)

        main_layout.addWidget(button_create)
        main_layout.addWidget(button_open)

        self.recent_list = QListWidget()
        self.recent_list.setSelectionMode(QListWidget.SingleSelection)
        self.recent_list.itemClicked.connect(self._on_recent_project_selected)
        main_layout.addWidget(QLabel("Recent Projects"))
        main_layout.addWidget(self.recent_list)

        self._load_recent_projects()

    def _load_recent_projects(self):
        recent_path = Path(__file__).resolve().parent.parent / "recent_projects.json"
        if recent_path.exists():
            try:
                with recent_path.open("r", encoding="utf-8") as handle:
                    items = json.load(handle)
            except Exception as exc:
                self.console.warning(f"Failed to load recent projects: {exc}")
                items = []
        else:
            items = []

        if not items:
            self.recent_list.addItem("No recent projects available")
            return

        for project in items:
            row = QListWidgetItem(project.get("name", "Untitled Project"))
            row.setData(Qt.UserRole, project.get("path", ""))
            self.recent_list.addItem(row)

    def _on_create_project(self):
        self.console.info("Start screen: create project clicked.")
        self.create_callback()

    def _on_open_project(self):
        self.console.info("Start screen: open project clicked.")
        self.open_callback()

    def _on_recent_project_selected(self, item):
        path = item.data(Qt.UserRole)
        if not path:
            self.console.warning("Recent project has no path.")
            return
        self.console.info(f"Start screen: opening recent project {path}")
        self.recent_callback(path)
