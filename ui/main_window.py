from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QDockWidget,
    QFormLayout,
    QFrame,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
)

from ui.start_screen import ProjectTypeDialog, StartScreen
from ui.viewport import ViewportWidget


class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setWindowTitle("NEXIS")
        self.resize(1280, 860)
        self._create_menu()
        self._create_docks()
        self._create_central_area()
        self._create_console_output()
        self.app.console.set_ui_widget(self.console_text_edit)
        self.show_start_screen()

    def _create_menu(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        self.close_project_action = QAction("Close Project", self)
        self.close_project_action.setEnabled(False)
        self.close_project_action.triggered.connect(self._on_request_close_project)
        file_menu.addAction(self.close_project_action)

    def _create_docks(self) -> None:
        self.scene_hierarchy = QTreeWidget()
        self.scene_hierarchy.setHeaderLabel("Scene Hierarchy")
        self.scene_hierarchy.addTopLevelItem(QTreeWidgetItem(["Scene Root"]))
        self.scene_dock = QDockWidget("Scene Hierarchy", self)
        self.scene_dock.setWidget(self.scene_hierarchy)
        self.scene_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.scene_dock)

        inspector_widget = QWidget()
        inspector_widget.setMinimumWidth(260)
        inspector_layout = QFormLayout(inspector_widget)
        inspector_layout.addRow(
            QLabel("Inspector"), QLabel("Select an object to view properties.")
        )
        inspector_frame = QFrame()
        inspector_frame.setLayout(inspector_layout)

        self.inspector_dock = QDockWidget("Inspector", self)
        self.inspector_dock.setWidget(inspector_frame)
        self.inspector_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea
        )
        self.addDockWidget(Qt.RightDockWidgetArea, self.inspector_dock)

    def _create_central_area(self) -> None:
        self.stacked_central = QStackedWidget()
        self.start_screen = StartScreen(
            self.app.console,
            self._on_request_create_project,
            self._on_request_open_project,
            self._on_request_open_recent_project,
        )
        self.viewport_widget = ViewportWidget(self.app)
        self.stacked_central.addWidget(self.start_screen)
        self.stacked_central.addWidget(self.viewport_widget)
        self.setCentralWidget(self.stacked_central)

    def _create_console_output(self) -> None:
        self.console_text_edit = QTextEdit()
        self.console_text_edit.setReadOnly(True)
        self.console_text_edit.setMinimumHeight(180)

        self.console_dock = QDockWidget("Console", self)
        self.console_dock.setWidget(self.console_text_edit)
        self.console_dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.console_dock)

    def _set_editor_mode(self, enabled: bool) -> None:
        self.scene_dock.setVisible(enabled)
        self.inspector_dock.setVisible(enabled)
        self.console_dock.setVisible(enabled)
        self.close_project_action.setEnabled(enabled)

    def show_start_screen(self) -> None:
        self._set_editor_mode(False)
        self.stacked_central.setCurrentWidget(self.start_screen)
        self.setWindowTitle("NEXIS - Start")

    def show_viewport(self) -> None:
        self._set_editor_mode(True)
        self.stacked_central.setCurrentWidget(self.viewport_widget)
        self.setWindowTitle("NEXIS - Editor")

    def _on_request_create_project(self) -> None:
        dialog = ProjectTypeDialog(self)
        if dialog.exec() == QDialog.Accepted:
            scene_type = dialog.selected_type()
            if scene_type:
                self.app.create_project(scene_type)
            else:
                self.app.console.warning("No project type selected.")

    def _on_request_open_project(self) -> None:
        root = Path(__file__).resolve().parent.parent
        project_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open NEXIS Project",
            str(root),
            "Project Files (*.project);;All Files (*)",
        )
        if project_path:
            self.app.open_project(project_path)

    def _on_request_open_recent_project(self, path: str) -> None:
        self.app.open_project(path)

    def _on_request_close_project(self) -> None:
        self.app.close_project()

    def on_project_loaded(self, scene_type: str) -> None:
        self.app.console.info(f"Project ready. Active scene type: {scene_type}.")
        self._refresh_scene_hierarchy(scene_type)
        self.show_viewport()

    def _refresh_scene_hierarchy(self, scene_type: str) -> None:
        self.scene_hierarchy.clear()
        root_item = QTreeWidgetItem(["Scene Root"])
        scene_item = QTreeWidgetItem([f"{scene_type} Scene"])
        root_item.addChild(scene_item)
        root_item.setExpanded(True)
        self.scene_hierarchy.addTopLevelItem(root_item)
