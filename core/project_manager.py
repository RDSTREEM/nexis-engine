from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from core.scene import Scene

if TYPE_CHECKING:
    pass

RECENT_PROJECTS_FILE = Path.home() / ".nexis" / "recent_projects.json"
MAX_RECENT = 10


class ProjectManager:
    """
    Owns the active project and scene.
    Handles create / open / save / close and the recent-projects list.

    Project file (.nexis) — JSON:
    {
        "name": "MyGame",
        "type": "3D",           # "2D" or "3D"
        "version": "0.1",
        "scenes": ["scenes/Main.nexis_scene"],
        "startup_scene": "scenes/Main.nexis_scene"
    }

    Scene file (.nexis_scene) — JSON produced by Scene.to_dict()
    """

    def __init__(self, app):
        self.app = app

        self.project_path: Optional[Path] = None  # path to .nexis file
        self.project_name: str = ""
        self.project_type: str = "3D"  # "2D" or "3D"
        self.project_root: Optional[Path] = None  # folder containing .nexis

        self.active_scene: Optional[Scene] = None
        self.is_open: bool = False
        self._project_settings: dict = {}  # Cached project settings

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_project(self, folder: Path, name: str, project_type: str) -> bool:
        """Create a new project folder structure and default scene."""
        try:
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "scenes").mkdir(exist_ok=True)
            (folder / "assets").mkdir(exist_ok=True)
            (folder / "scripts").mkdir(exist_ok=True)

            # default scene
            scene = Scene(f"{name} Scene", project_type)
            scene_rel = "scenes/Main.nexis_scene"
            scene_path = folder / scene_rel
            scene_path.write_text(
                json.dumps(scene.to_dict(), indent=2), encoding="utf-8"
            )

            # project file
            project_data = {
                "name": name,
                "type": project_type,
                "version": "0.1",
                "scenes": [scene_rel],
                "startup_scene": scene_rel,
            }
            proj_file = folder / f"{name}.nexis"
            proj_file.write_text(json.dumps(project_data, indent=2), encoding="utf-8")

            self._set_project(proj_file, project_data, scene)
            self._add_to_recent(proj_file, name)
            self.app.console.info(f"Project '{name}' created at {folder}")
            return True

        except Exception as exc:
            self.app.console.warning(f"Failed to create project: {exc}")
            return False

    # ------------------------------------------------------------------
    # Open
    # ------------------------------------------------------------------

    def open_project(self, path: str | Path) -> bool:
        path = Path(path)
        if not path.exists():
            self.app.console.warning(f"Project file not found: {path}")
            return False
        try:
            project_data = json.loads(path.read_text(encoding="utf-8"))
            startup = project_data.get("startup_scene", "")
            scene_path = path.parent / startup if startup else None

            if scene_path and scene_path.exists():
                scene_data = json.loads(scene_path.read_text(encoding="utf-8"))
                scene = Scene.from_dict(scene_data)
            else:
                scene = Scene(
                    project_data.get("name", "Scene"), project_data.get("type", "3D")
                )

            self._set_project(path, project_data, scene)
            self._add_to_recent(path, project_data.get("name", path.stem))
            self.app.console.info(f"Opened project: {path}")
            return True

        except Exception as exc:
            self.app.console.warning(f"Failed to open project: {exc}")
            return False

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save_scene(self) -> bool:
        if not self.is_open or self.active_scene is None:
            return False
        try:
            project_data = json.loads(self.project_path.read_text(encoding="utf-8"))
            startup = project_data.get("startup_scene", "scenes/Main.nexis_scene")
            scene_path = self.project_root / startup
            scene_path.parent.mkdir(parents=True, exist_ok=True)
            scene_path.write_text(
                json.dumps(self.active_scene.to_dict(), indent=2), encoding="utf-8"
            )
            self.app.console.info(f"Scene saved: {scene_path}")
            return True
        except Exception as exc:
            self.app.console.warning(f"Failed to save scene: {exc}")
            return False

    def save_project(self) -> bool:
        """Save project metadata (no scene data — call save_scene separately)."""
        if not self.is_open:
            return False
        try:
            project_data = {
                "name": self.project_name,
                "type": self.project_type,
                "version": "0.1",
                "scenes": ["scenes/Main.nexis_scene"],
                "startup_scene": "scenes/Main.nexis_scene",
            }
            self.project_path.write_text(
                json.dumps(project_data, indent=2), encoding="utf-8"
            )
            return True
        except Exception as exc:
            self.app.console.warning(f"Failed to save project: {exc}")
            return False

    # ------------------------------------------------------------------
    # Close
    # ------------------------------------------------------------------

    def close_project(self) -> None:
        self.save_scene()
        self.project_path = None
        self.project_name = ""
        self.project_type = "3D"
        self.project_root = None
        self.active_scene = None
        self.is_open = False
        self._project_settings = {}
        self.app.console.info("Project closed.")

    # ------------------------------------------------------------------
    # Recent projects
    # ------------------------------------------------------------------

    def load_recent_projects(self) -> list:
        if not RECENT_PROJECTS_FILE.exists():
            return []
        try:
            return json.loads(RECENT_PROJECTS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _add_to_recent(self, path: Path, name: str) -> None:
        recent = self.load_recent_projects()
        entry = {"name": name, "path": str(path)}
        recent = [r for r in recent if r.get("path") != str(path)]
        recent.insert(0, entry)
        recent = recent[:MAX_RECENT]
        RECENT_PROJECTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        RECENT_PROJECTS_FILE.write_text(json.dumps(recent, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _set_project(self, path: Path, data: dict, scene: Scene) -> None:
        self.project_path = path
        self.project_root = path.parent
        self.project_name = data.get("name", path.stem)
        self.project_type = data.get("type", "3D")
        self.active_scene = scene
        self.is_open = True
        self._load_project_settings()

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def _load_project_settings(self) -> None:
        """Load project_settings.json from project root."""
        import copy

        # Default settings
        self._project_settings = {
            "physics": {
                "gravity_x": 0.0,
                "gravity_y": -9.81,
                "fixed_timestep": 0.02,
                "max_substeps": 5,
            },
            "render": {
                "target_fps": 60,
                "vsync": True,
                "msaa_samples": 4,
                "background_color": [0.1, 0.12, 0.18, 1.0],
            },
            "tags": [
                "Untagged",
                "Player",
                "Enemy",
                "Ground",
                "Trigger",
                "UI",
                "Camera",
            ],
            "layers": ["Default", "UI", "Physics", "Ignore Raycast"],
            "input": {
                "Horizontal": {"positive": "D", "negative": "A"},
                "Vertical": {"positive": "W", "negative": "S"},
                "Jump": {"positive": "Space", "negative": ""},
                "Fire": {"positive": "Mouse0", "negative": ""},
            },
        }

        # Load and merge saved settings
        if self.project_root:
            settings_path = self.project_root / "project_settings.json"
            if settings_path.exists():
                try:
                    saved = json.loads(settings_path.read_text(encoding="utf-8"))
                    for k, v in saved.items():
                        if isinstance(v, dict) and k in self._project_settings:
                            self._project_settings[k].update(v)
                        else:
                            self._project_settings[k] = v
                except Exception:
                    pass

    def get_tags(self) -> list:
        """Get list of predefined tags for this project."""
        return self._project_settings.get("tags", ["Untagged"])

    def get_layers(self) -> list:
        """Get list of predefined layers for this project."""
        return self._project_settings.get("layers", ["Default"])
