"""
scene_manager_runtime.py
Runtime scene loading/unloading — usable from scripts.

from core.scene_manager_runtime import SceneManager
SceneManager.load("scenes/Level2.nexis_scene")
SceneManager.load_additive("scenes/HUD.nexis_scene")
SceneManager.unload("scenes/HUD.nexis_scene")
SceneManager.reload()
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from core.scene import Scene


class _SceneManagerRuntime:
    def __init__(self):
        self._app          = None   # set by NEXISApplication
        self._active_scenes: List["Scene"] = []
        self._scene_paths:   List[str]     = []

    def _bind(self, app) -> None:
        self._app = app

    # ------------------------------------------------------------------
    # Load (replace all current scenes)
    # ------------------------------------------------------------------

    def load(self, path: str, transition_fn=None) -> Optional["Scene"]:
        """
        Load a scene file and replace the current scene.
        Stops play mode if running.
        transition_fn: optional callable(old_scene, new_scene) for fades etc.
        """
        if self._app is None:
            return None

        play = getattr(self._app, "play_mode", None)
        if play and play.is_playing:
            play.stop()

        scene = self._load_file(path)
        if scene is None:
            return None

        if transition_fn:
            transition_fn(self._app.active_scene, scene)

        self._app.project.active_scene = scene
        self._active_scenes            = [scene]
        self._scene_paths              = [str(path)]

        self._app.main_window.hierarchy.refresh()
        self._app.main_window.inspector.clear()
        self._app.console.info(f"Loaded scene: {Path(path).name}")
        return scene

    # ------------------------------------------------------------------
    # Additive load (keep existing scenes, add new one)
    # ------------------------------------------------------------------

    def load_additive(self, path: str) -> Optional["Scene"]:
        scene = self._load_file(path)
        if scene is None:
            return None
        self._active_scenes.append(scene)
        self._scene_paths.append(str(path))
        # merge entities into primary scene for rendering
        primary = self._app.active_scene
        if primary and scene is not primary:
            for entity in scene.entities:
                primary.add_entity(entity)
        self._app.main_window.hierarchy.refresh()
        self._app.console.info(f"Additively loaded: {Path(path).name}")
        return scene

    # ------------------------------------------------------------------
    # Unload a specific scene (by path)
    # ------------------------------------------------------------------

    def unload(self, path: str) -> None:
        key = str(path)
        if key not in self._scene_paths:
            return
        idx   = self._scene_paths.index(key)
        scene = self._active_scenes[idx]
        # remove its entities from primary scene
        primary = self._app.active_scene
        if primary and scene is not primary:
            for entity in scene.entities:
                primary.remove_entity(entity)
        self._active_scenes.pop(idx)
        self._scene_paths.pop(idx)
        self._app.console.info(f"Unloaded: {Path(path).name}")
        self._app.main_window.hierarchy.refresh()

    # ------------------------------------------------------------------
    # Reload current scene from disk
    # ------------------------------------------------------------------

    def reload(self) -> Optional["Scene"]:
        if not self._scene_paths:
            return None
        return self.load(self._scene_paths[0])

    # ------------------------------------------------------------------
    # Current scene info
    # ------------------------------------------------------------------

    @property
    def active_scene(self) -> Optional["Scene"]:
        return self._app.active_scene if self._app else None

    @property
    def loaded_scene_paths(self) -> List[str]:
        return list(self._scene_paths)

    def is_loaded(self, path: str) -> bool:
        return str(path) in self._scene_paths

    # ------------------------------------------------------------------

    def _load_file(self, path: str) -> Optional["Scene"]:
        from core.scene import Scene
        p = Path(path)
        if not p.is_absolute() and self._app.project.project_root:
            p = self._app.project.project_root / path
        if not p.exists():
            self._app.console.warning(f"Scene file not found: {p}")
            return None
        try:
            data  = json.loads(p.read_text(encoding="utf-8"))
            scene = Scene.from_dict(data)
            return scene
        except Exception as e:
            self._app.console.warning(f"Failed to load scene '{p.name}': {e}")
            return None


# Singleton — scripts import this
SceneManager = _SceneManagerRuntime()