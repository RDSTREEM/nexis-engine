from __future__ import annotations
from pathlib import Path

from core.console import EngineConsole
from core.project_manager import ProjectManager
from assets.asset_manager import AssetManager
from core.raycast import EntitySelector
from core.play_mode import PlayMode
from core.prefab_system import PrefabSystem
from core.scene_manager_runtime import SceneManager
from core.undo_redo import UndoStack
from scripting.script_manager import ScriptManager
from ui.main_window import MainWindow

from assets.importers.mesh_importer import import_mesh
from assets.importers.texture_importer import import_texture
from assets.importers.audio_importer import import_audio


class NEXISApplication:
    def __init__(self):
        self.console = EngineConsole()
        self.project = ProjectManager(self)
        self.assets = AssetManager(self)
        self.selector = EntitySelector(self)
        self.play_mode = PlayMode(self)
        self.prefabs = PrefabSystem(self)
        self.script_manager = ScriptManager(self)
        self.undo = UndoStack

        # bind runtime scene manager to this app
        SceneManager._bind(self)

        self.assets.register_importer("mesh", import_mesh)
        self.assets.register_importer("texture", import_texture)
        self.assets.register_importer("audio", import_audio)

        self.main_window = MainWindow(self)

        # undo stack notifies main window title
        UndoStack.set_on_change(self._on_undo_change)

    # ------------------------------------------------------------------

    @property
    def active_scene(self):
        return self.project.active_scene

    @active_scene.setter
    def active_scene(self, scene):
        self.project.active_scene = scene

    @property
    def project_type(self) -> str:
        return self.project.project_type

    # ------------------------------------------------------------------

    def run(self) -> None:
        self.main_window.show()
        self.console.info("NEXIS engine started.")

    def create_project(self, folder: Path, name: str, ptype: str) -> None:
        if self.project.create_project(folder, name, ptype):
            UndoStack.clear()
            self._post_project_load()

    def open_project(self, path: str) -> None:
        if path and self.project.open_project(path):
            UndoStack.clear()
            self._post_project_load()

    def save_project(self) -> None:
        self.project.save_scene()
        self.project.save_project()
        self.console.info("Project saved.")

    def close_project(self) -> None:
        if self.play_mode.is_playing:
            self.play_mode.stop()
        self.project.close_project()
        self.selector.clear()
        UndoStack.clear()
        self.main_window.show_start_screen()

    def _post_project_load(self) -> None:
        SceneManager._active_scenes = []
        SceneManager._scene_paths = []
        if self.project.project_root:
            self.assets.scan_project(self.project.project_root)
        self.main_window.on_project_loaded()

    def _on_undo_change(self) -> None:
        mw = getattr(self, "main_window", None)
        if mw is None:
            return
        can_u = UndoStack.can_undo()
        can_r = UndoStack.can_redo()
        if hasattr(mw, "_undo_act"):
            mw._undo_act.setEnabled(can_u)
            mw._undo_act.setText(
                f"Undo {UndoStack.undo_description()}" if can_u else "Undo"
            )
        if hasattr(mw, "_redo_act"):
            mw._redo_act.setEnabled(can_r)
            mw._redo_act.setText(
                f"Redo {UndoStack.redo_description()}" if can_r else "Redo"
            )
