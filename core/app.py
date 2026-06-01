from pathlib import Path

from PySide6.QtWidgets import QFileDialog

from core.console import EngineConsole
from core.project_manager import ProjectManager
from scripting.script_manager import ScriptManager
from ui.main_window import MainWindow


class NEXISApplication:
    def __init__(self):
        self.console = EngineConsole()
        self.project = ProjectManager(self)
        self.script_manager = ScriptManager(self)
        self.main_window = MainWindow(self)

    # convenience so viewport can do self.app.active_scene
    @property
    def active_scene(self):
        return self.project.active_scene

    @property
    def project_type(self) -> str:
        return self.project.project_type  # "2D" or "3D"

    def run(self) -> None:
        self.main_window.show()
        self.console.info("NEXIS engine started.")

    # ------------------------------------------------------------------
    # Called by MainWindow
    # ------------------------------------------------------------------

    def request_create_project(self) -> None:
        """Opens the create-project dialog chain (handled in MainWindow)."""
        self.main_window.on_request_create_project()

    def create_project(self, folder: Path, name: str, project_type: str) -> None:
        ok = self.project.create_project(folder, name, project_type)
        if ok:
            self.main_window.on_project_loaded()

    def open_project(self, path: str) -> None:
        if not path:
            self.console.warning("Open project cancelled.")
            return
        ok = self.project.open_project(path)
        if ok:
            self.main_window.on_project_loaded()

    def save_project(self) -> None:
        self.project.save_scene()
        self.project.save_project()
        self.console.info("Project saved.")

    def close_project(self) -> None:
        self.project.close_project()
        self.main_window.show_start_screen()
