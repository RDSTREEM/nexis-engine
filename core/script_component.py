"""
script_component.py
Per-entity Python script component.
The script file must define a class named Script with any of:
    on_start(self, entity)
    on_update(self, entity, dt)
    on_stop(self, entity)
    on_input(self, entity, key, pressed)

Also supports the Amharic (.amh) language — transpiled to Python via
the AmharicTranspiler before execution (Phase 5).
"""

from __future__ import annotations

import importlib.util
import sys
import traceback
from pathlib import Path
from typing import Optional, Any

from core.component import Component


class ScriptComponent(Component):
    """Attaches a Python or Amharic script file to an entity."""

    def __init__(self, script_path: str = ""):
        super().__init__()
        self.script_path: str = script_path
        self._instance: Any = None
        self._error: str = ""
        self._loaded: bool = False

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load(self) -> bool:
        """Load and instantiate the script class. Returns True on success."""
        path = Path(self.script_path)
        if not path.exists():
            self._error = f"Script not found: {self.script_path}"
            return False

        try:
            source = path.read_text(encoding="utf-8")

            # transpile Amharic if needed
            if path.suffix.lower() == ".amh":
                from scripting.amharic_transpiler import transpile

                source = transpile(source)

            code = compile(source, str(path), "exec")
            ns = {}
            exec(code, ns)

            cls = ns.get("Script")
            if cls is None:
                self._error = "Script file must define a class named 'Script'."
                return False

            self._instance = cls()
            self._loaded = True
            self._error = ""
            return True

        except Exception:
            self._error = traceback.format_exc()
            self._loaded = False
            self._instance = None
            if self.entity:
                print(f"[Script] Error loading '{self.script_path}':\n{self._error}")
            return False

    def reload(self) -> bool:
        """Hot-reload the script (e.g. on file change)."""
        self._loaded = False
        self._instance = None
        return self.load()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_attach(self) -> None:
        if self.script_path:
            self.load()

    def on_start(self) -> None:
        self._call("on_start", self.entity)

    def on_update(self, delta_time: float) -> None:
        self._call("on_update", self.entity, delta_time)

    def on_stop(self) -> None:
        self._call("on_stop", self.entity)

    def on_input(self, key: int, pressed: bool) -> None:
        self._call("on_input", self.entity, key, pressed)

    # ------------------------------------------------------------------

    def _call(self, method: str, *args) -> None:
        if not self._loaded or self._instance is None:
            return
        fn = getattr(self._instance, method, None)
        if callable(fn):
            try:
                fn(*args)
            except Exception:
                err = traceback.format_exc()
                print(f"[Script] Runtime error in '{method}':\n{err}")

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["script_path"] = self.script_path
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "ScriptComponent":
        sc = cls(script_path=data.get("script_path", ""))
        sc.enabled = data.get("enabled", True)
        return sc
