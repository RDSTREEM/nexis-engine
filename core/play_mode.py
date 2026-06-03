"""
play_mode.py
Manages the play/pause/stop lifecycle.

On Play:
  1. Snapshot the scene (deep copy via JSON round-trip)
  2. Start Time, Input, Events
  3. Start ScriptRunner, HotReloader, PhysicsWorld
  4. Switch viewport to play rendering

On Stop:
  1. Stop scripts, hot-reloader, physics
  2. Clear Events
  3. Restore scene from snapshot
  4. Refresh hierarchy + inspector
"""

from __future__ import annotations
import json
from typing import Optional, TYPE_CHECKING

from core.time_manager import Time
from core.event_system import Events
from core.input_manager import Input
from core.script_runner import ScriptRunner
from core.hot_reload import HotReloader
from core.physics_2d import PhysicsWorld2D
from core.scene import Scene

if TYPE_CHECKING:
    pass


class PlayMode:

    def __init__(self, app):
        self.app = app
        self.is_playing = False
        self.is_paused = False

        self._snapshot: Optional[str] = None  # JSON string
        self._runner: ScriptRunner = ScriptRunner(app)
        self._hot_reload: HotReloader = HotReloader(app)
        self._physics: PhysicsWorld2D = PhysicsWorld2D()

    # ------------------------------------------------------------------
    # Play
    # ------------------------------------------------------------------

    def play(self) -> None:
        if self.is_playing:
            return
        scene = self.app.active_scene
        if scene is None:
            self.app.console.warning("No scene loaded — cannot enter play mode.")
            return

        self.app.console.info("▶ Entering play mode…")

        # snapshot
        self._snapshot = json.dumps(scene.to_dict())

        # start systems
        Time.start()
        self._runner.start(scene)
        self._hot_reload.start(scene)
        scene.start()

        self.is_playing = True
        self.is_paused = False

        # update toolbar
        self.app.main_window.toolbar.set_playing(True, False)
        self.app.console.info("▶ Play mode active.")

    # ------------------------------------------------------------------
    # Pause / resume
    # ------------------------------------------------------------------

    def pause(self) -> None:
        if not self.is_playing:
            return
        self.is_paused = not self.is_paused
        Time.time_scale = 0.0 if self.is_paused else 1.0
        label = "⏸ Paused." if self.is_paused else "▶ Resumed."
        self.app.console.info(label)
        self.app.main_window.toolbar.set_playing(True, self.is_paused)

    # ------------------------------------------------------------------
    # Stop
    # ------------------------------------------------------------------

    def stop(self) -> None:
        if not self.is_playing:
            return
        self.app.console.info("⏹ Stopping play mode…")
        scene = self.app.active_scene

        # stop systems
        self._runner.stop(scene)
        self._hot_reload.stop()
        scene.stop()
        Time.stop()
        Events.clear()

        self.is_playing = False
        self.is_paused = False

        # restore scene
        if self._snapshot:
            restored = Scene.from_dict(json.loads(self._snapshot))
            self.app.project.active_scene = restored
            self._snapshot = None

        # refresh UI
        self.app.main_window.hierarchy.refresh()
        self.app.main_window.inspector.clear()
        self.app.main_window.toolbar.set_playing(False, False)
        self.app.console.info("⏹ Play mode stopped. Scene restored.")

    # ------------------------------------------------------------------
    # Per-frame update  (called by viewport tick)
    # ------------------------------------------------------------------

    def update(self) -> None:
        if not self.is_playing or self.is_paused:
            return
        scene = self.app.active_scene
        if scene is None:
            return

        dt = Time.tick()

        # physics
        self._physics.step(scene, dt)

        # scripts
        self._runner.update(scene, dt)

        # scene update (non-script on_update components)
        scene.update(dt)

    def send_input(self, key: int, pressed: bool) -> None:
        if not self.is_playing or self.is_paused:
            return
        scene = self.app.active_scene
        if scene:
            self._runner.send_input(scene, key, pressed)
