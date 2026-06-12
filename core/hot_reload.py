from __future__ import annotations
import os
import threading
import time
from pathlib import Path
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from core.scene import Scene


class HotReloader:
    """
    Start watching when play mode begins.
    Stop watching when play mode ends.
    """

    POLL_INTERVAL = 1.0  # seconds between checks

    def __init__(self, app):
        self.app = app
        self._mtimes: Dict[str, float] = {}
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self, scene: "Scene") -> None:
        self._running = True
        self._snapshot(scene)
        self._thread = threading.Thread(target=self._watch, args=(scene,), daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        self._mtimes.clear()

    def _snapshot(self, scene: "Scene") -> None:
        from core.script_component import ScriptComponent

        for entity in scene.entities:
            for sc in entity.get_components(ScriptComponent):
                p = sc.script_path
                if p and Path(p).exists():
                    self._mtimes[p] = os.stat(p).st_mtime

    def _watch(self, scene: "Scene") -> None:
        from core.script_component import ScriptComponent

        while self._running:
            time.sleep(self.POLL_INTERVAL)
            for entity in scene.entities:
                for sc in entity.get_components(ScriptComponent):
                    p = sc.script_path
                    if not p or not Path(p).exists():
                        continue
                    mtime = os.stat(p).st_mtime
                    if mtime != self._mtimes.get(p, 0):
                        self._mtimes[p] = mtime
                        ok = sc.reload()
                        status = "reloaded" if ok else "reload FAILED"
                        self.app.console.info(f"[HotReload] {Path(p).name} {status}")
