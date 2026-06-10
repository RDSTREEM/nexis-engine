"""
game_runner.py
Headless NEXIS game runner — runs a project WITHOUT the editor UI.
Supports two modes:
  1. python game_runner.py path/to/Project.nexis
  2. python game_runner.py path/to/Project.nexis --windowed  (separate window)

The --windowed flag is also what the editor uses for "Play in New Window".
"""

from __future__ import annotations
import sys
import json
import time
import math
import argparse
from pathlib import Path

import numpy as np
import moderngl
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtOpenGLWidgets import QOpenGLWidget

# ── Minimal console (no UI widget) ────────────────────────────────────────


class _Console:
    def info(self, m):
        print(f"[INFO]    {m}")

    def warning(self, m):
        print(f"[WARNING] {m}")

    def error(self, m):
        print(f"[ERROR]   {m}")


# ── Game GL widget ─────────────────────────────────────────────────────────


class GameWidget(QOpenGLWidget):
    """
    Minimal OpenGL widget that runs the scene in play mode.
    Mirrors exactly what the editor viewport does during play,
    but with no editor overhead.
    """

    def __init__(self, project_path: str, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self._project_path = Path(project_path)
        self._ctx = None
        self._scene = None
        self._ready = False

        # Minimal app-like object so scene / scripts work unchanged
        from core.console import EngineConsole
        from core.time_manager import Time
        from core.event_system import Events
        from core.input_manager import Input
        from core.physics_2d import PhysicsWorld2D

        self._console = EngineConsole()
        self._Time = Time
        self._Events = Events
        self._Input = Input
        self._physics = PhysicsWorld2D()
        self._last_t = time.perf_counter()

        # Timer drives the game loop
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    # ── GL ──────────────────────────────────────────────────────────────

    def initializeGL(self):
        self._ctx = moderngl.create_context()
        self._load_project()

    def _load_project(self):
        try:
            pdata = json.loads(self._project_path.read_text(encoding="utf-8"))
            startup = pdata.get("startup_scene", "")
            scene_path = self._project_path.parent / startup
            from core.scene import Scene

            self._scene = Scene.from_dict(
                json.loads(scene_path.read_text(encoding="utf-8"))
            )
            self._ptype = pdata.get("type", "3D")
            # Start
            self._Time.start()
            self._scene.start()
            self._ready = True
            self._console.info(f"Game started: {pdata.get('name','')}")
        except Exception as e:
            self._console.error(f"Failed to load project: {e}")
            import traceback

            traceback.print_exc()

    def paintGL(self):
        if not self._ready or self._scene is None:
            return
        w, h = max(1, self.width()), max(1, self.height())
        fbo = self._ctx.detect_framebuffer(self.defaultFramebufferObject())
        fbo.use()
        self._ctx.viewport = (0, 0, w, h)
        self._ctx.enable(moderngl.DEPTH_TEST)

        cam = self._scene._find_main_camera()
        if cam:
            cc = cam.clear_color
            self._ctx.clear(cc[0], cc[1], cc[2], cc[3])
            view = cam.get_view_matrix()
            proj = cam.get_projection_matrix(w, h)
            self._scene.render_editor(self._ctx, view, proj)
        else:
            self._ctx.clear(0.05, 0.05, 0.05, 1.0)

    def resizeGL(self, w, h):
        if self._ctx:
            self._ctx.viewport = (0, 0, w, h)

    # ── Game loop ────────────────────────────────────────────────────────

    def _tick(self):
        if not self._ready:
            return
        self._Input.begin_frame()
        dt = self._Time.tick()
        self._physics.step(self._scene, dt)
        self._scene.update(dt)
        self.update()

    # ── Input forwarding ─────────────────────────────────────────────────

    def keyPressEvent(self, ev):
        self._Input.on_key_press(ev.key())
        # Send to all script components
        if self._scene:
            from core.script_component import ScriptComponent

            for e in self._scene.all_entities():
                sc = e.get_component(ScriptComponent)
                if sc and sc._loaded:
                    sc.on_input(ev.key(), True)
        super().keyPressEvent(ev)

    def keyReleaseEvent(self, ev):
        self._Input.on_key_release(ev.key())
        if self._scene:
            from core.script_component import ScriptComponent

            for e in self._scene.all_entities():
                sc = e.get_component(ScriptComponent)
                if sc and sc._loaded:
                    sc.on_input(ev.key(), False)
        super().keyReleaseEvent(ev)

    def mousePressEvent(self, ev):
        self._Input.on_mouse_press(ev.button().value)

    def mouseReleaseEvent(self, ev):
        self._Input.on_mouse_release(ev.button().value)

    def mouseMoveEvent(self, ev):
        pos = ev.position().toPoint()
        self._Input.on_mouse_move(pos.x(), pos.y())

    def wheelEvent(self, ev):
        self._Input.on_scroll(ev.angleDelta().y() / 120.0)

    def closeEvent(self, ev):
        if self._scene:
            self._scene.stop()
        self._Events.clear()
        self._Time.stop()
        super().closeEvent(ev)


# ── Play window (used by editor "Play in Window") ─────────────────────────


class PlayWindow(QMainWindow):
    """Separate window launched from the editor for play-in-window mode."""

    def __init__(self, project_path: str):
        super().__init__()
        self.setWindowTitle("NEXIS — Game")
        self.resize(960, 540)
        widget = GameWidget(project_path, parent=self)
        self.setCentralWidget(widget)

    @staticmethod
    def launch(project_path: str) -> "PlayWindow":
        """Called from the editor. Returns the window (caller must keep ref)."""
        win = PlayWindow(project_path)
        win.show()
        return win


# ── CLI entry point ────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="NEXIS Game Runner")
    parser.add_argument("project", help="Path to .nexis project file")
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--title", default="")
    parser.add_argument(
        "--windowed",
        action="store_true",
        help="Run in a titled window (same as Play in Window)",
    )
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName("NEXIS Game")

    win = QMainWindow()
    title = args.title or Path(args.project).stem
    win.setWindowTitle(title)
    win.resize(args.width, args.height)

    widget = GameWidget(args.project)
    win.setCentralWidget(widget)
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
