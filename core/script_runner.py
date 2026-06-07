"""
script_runner.py
Executes all ScriptComponents in a scene safely.
Provides a controlled globals dict so scripts can access engine APIs
without importing anything dangerous.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import traceback

if TYPE_CHECKING:
    from core.scene import Scene


def _make_sandbox(app) -> dict:
    """Build the globals dict injected into every script execution."""
    from core.input_manager import Input
    from core.time_manager import Time
    from core.event_system import Events
    from core.scene_manager_runtime import SceneManager
    from PySide6.QtCore import Qt

    return {
        # engine APIs
        "Input": Input,
        "Time": Time,
        "Events": Events,
        "Qt": Qt,
        # scene access helper
        "get_scene": lambda: app.active_scene,
        "SceneManager": SceneManager,
        "Prefabs": app.prefabs,
        "Assets": app.assets,
        # math
        "math": __import__("math"),
        "numpy": __import__("numpy"),
        # safe builtins only
        "__builtins__": {
            "print": print,
            "len": len,
            "range": range,
            "int": int,
            "float": float,
            "str": str,
            "bool": bool,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
            "abs": abs,
            "min": min,
            "max": max,
            "round": round,
            "enumerate": enumerate,
            "zip": zip,
            "isinstance": isinstance,
            "hasattr": hasattr,
            "getattr": getattr,
            "setattr": setattr,
        },
    }


class ScriptRunner:
    """
    Manages the lifecycle of all scripts in a scene.
    Called by PlayMode.
    """

    def __init__(self, app):
        self.app = app
        self._sandbox = {}

    def start(self, scene: "Scene") -> None:
        self._sandbox = _make_sandbox(self.app)
        from core.script_component import ScriptComponent

        for entity in scene.entities:
            if not entity.enabled:
                continue
            for sc in entity.get_components(ScriptComponent):
                if not sc.enabled:
                    continue
                sc._sandbox = self._sandbox  # inject sandbox
                if not sc._loaded:
                    sc.load()
                self._safe_call(sc, "on_start", entity)

    def update(self, scene: "Scene", dt: float) -> None:
        from core.script_component import ScriptComponent

        for entity in scene.entities:
            if not entity.enabled:
                continue
            for sc in entity.get_components(ScriptComponent):
                if sc.enabled and sc._loaded:
                    self._safe_call(sc, "on_update", entity, dt)

    def stop(self, scene: "Scene") -> None:
        from core.script_component import ScriptComponent

        for entity in scene.entities:
            for sc in entity.get_components(ScriptComponent):
                if sc._loaded:
                    self._safe_call(sc, "on_stop", entity)

    def send_input(self, scene: "Scene", key: int, pressed: bool) -> None:
        from core.script_component import ScriptComponent

        for entity in scene.entities:
            if not entity.enabled:
                continue
            for sc in entity.get_components(ScriptComponent):
                if sc.enabled and sc._loaded:
                    self._safe_call(sc, "on_input", entity, key, pressed)

    @staticmethod
    def _safe_call(sc, method: str, *args) -> None:
        if sc._instance is None:
            return
        fn = getattr(sc._instance, method, None)
        if callable(fn):
            try:
                fn(*args)
            except Exception:
                print(
                    f"[ScriptRunner] '{method}' error in "
                    f"'{sc.script_path}':\n{traceback.format_exc()}"
                )
