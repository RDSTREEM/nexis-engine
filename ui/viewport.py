from __future__ import annotations
import time
from typing import Optional

import moderngl
import numpy as np
from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QKeyEvent, QMouseEvent, QWheelEvent
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from core.camera import EditorCamera
from core.debug_draw import DebugDraw
from core.input_manager import Input
from core.gizmos import Gizmo, TRANSLATE, ROTATE, SCALE


class ViewportWidget(QOpenGLWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)

        self.camera = EditorCamera(self.app.console, mode="3d")
        self.debug_draw = DebugDraw()

        self.gizmo = Gizmo()
        self.last_mouse: Optional[QPoint] = None
        self.right_btn_down: bool = False
        self.middle_btn_down: bool = False
        self.pressed_keys: set = set()

        self.last_frame = time.perf_counter()
        self.ctx: Optional[moderngl.Context] = None

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(16)

    # ------------------------------------------------------------------
    # GL
    # ------------------------------------------------------------------

    def initializeGL(self):
        self.ctx = moderngl.create_context()
        self.debug_draw.init_gl(self.ctx)
        self.app.console.info("ViewportWidget: GL context ready.")

    def paintGL(self):
        if self.ctx is None:
            return
        w, h = max(1, self.width()), max(1, self.height())
        fbo = self.ctx.detect_framebuffer(self.defaultFramebufferObject())
        fbo.use()
        self.ctx.viewport = (0, 0, w, h)
        self.ctx.enable(moderngl.DEPTH_TEST)

        scene = self.app.active_scene
        play_mode = getattr(self.app, "play_mode", None)
        playing = play_mode is not None and play_mode.is_playing

        if playing:
            rendered = scene.render_play(self.ctx, w, h) if scene else False
            if not rendered:
                self.ctx.clear(0.05, 0.05, 0.05, 1.0)
        else:
            self.ctx.clear(0.1, 0.12, 0.18, 1.0)
            view, proj = self.camera.get_matrices(w, h)
            if scene:
                scene.render_editor(self.ctx, view, proj)

            self.debug_draw.begin(view, proj)
            if self.camera.mode == "3d":
                self.debug_draw.grid(size=20, spacing=1.0)
                self.debug_draw.axis_gizmo((0, 0, 0), size=1.5)
            else:
                self.debug_draw.grid_2d(size=20, spacing=1.0)

            sel = self.app.selector.get_selection_aabb()
            if sel is not None:
                center, half = sel
                self.debug_draw.selection_box(center, half + 0.05)
            self.debug_draw.end()

            # gizmo overlay
            self.gizmo.set_entity(self.app.selector.selected_entity)
            self.gizmo.set_2d(self.camera.mode == "2d")
            self.debug_draw.begin(view, proj)
            self.gizmo.draw(self.debug_draw, view, proj, w, h)
            self.debug_draw.end()

    def resizeGL(self, w, h):
        if self.ctx:
            self.ctx.viewport = (0, 0, w, h)

    # ------------------------------------------------------------------
    # Tick
    # ------------------------------------------------------------------

    def _on_tick(self):
        now = time.perf_counter()
        dt = min(0.05, now - self.last_frame)
        self.last_frame = now

        Input.begin_frame()

        play_mode = getattr(self.app, "play_mode", None)
        if play_mode and play_mode.is_playing:
            play_mode.update()
        elif self.right_btn_down and self.pressed_keys:
            self.camera.fly(self.pressed_keys, dt)

        # update FPS in toolbar
        mw = getattr(self.app, "main_window", None)
        if mw and hasattr(mw, "toolbar"):
            from core.time_manager import Time

            if play_mode and play_mode.is_playing:
                mw.toolbar.set_fps(Time.fps)

        self.update()

    # ------------------------------------------------------------------
    # Mouse
    # ------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent):
        self.setFocus()
        pos = event.position().toPoint()
        self.last_mouse = pos
        btn = event.button()

        # use .value to convert Qt enum → int safely on PySide6
        Input.on_mouse_press(btn.value)

        play_mode = getattr(self.app, "play_mode", None)
        playing = play_mode is not None and play_mode.is_playing

        if btn == Qt.LeftButton:
            if not playing:
                w2, h2 = max(1, self.width()), max(1, self.height())
                v2, p2 = self.camera.get_matrices(w2, h2)
                if not self.gizmo.on_mouse_press(pos.x(), pos.y(), v2, p2, w2, h2):
                    self._try_pick(pos.x(), pos.y())
        elif btn == Qt.RightButton:
            self.right_btn_down = True
            self.setCursor(Qt.ClosedHandCursor)
        elif btn == Qt.MiddleButton:
            self.middle_btn_down = True
            self.setCursor(Qt.SizeAllCursor)

    def mouseReleaseEvent(self, event: QMouseEvent):
        Input.on_mouse_release(event.button().value)
        if self.gizmo.is_dragging():
            # record transform change for undo
            e = self.app.selector.selected_entity
            if e is not None:
                from core.undo_redo import SetPropertyCommand, UndoStack
                from core.gizmos import TRANSLATE, ROTATE, SCALE
                import numpy as np

                t = e.transform
                mode = self.gizmo.mode
                if mode == TRANSLATE:
                    cmd = SetPropertyCommand(
                        t,
                        "position",
                        self.gizmo._drag_start_pos,
                        t.position.copy(),
                        f"Move '{e.name}'",
                    )
                elif mode == SCALE:
                    cmd = SetPropertyCommand(
                        t,
                        "scale",
                        self.gizmo._drag_start_scale,
                        t.scale.copy(),
                        f"Scale '{e.name}'",
                    )
                else:
                    cmd = None
                if cmd:
                    # don't re-execute, just push to stack
                    UndoStack._undo.append(cmd)
                    UndoStack._redo.clear()
                    UndoStack._notify()
        self.gizmo.on_mouse_release()
        if event.button() == Qt.RightButton:
            self.right_btn_down = False
        elif event.button() == Qt.MiddleButton:
            self.middle_btn_down = False
        self.setCursor(Qt.ArrowCursor)

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position().toPoint()
        Input.on_mouse_move(pos.x(), pos.y())

        if self.last_mouse is None:
            self.last_mouse = pos
            return
        dx = pos.x() - self.last_mouse.x()
        dy = pos.y() - self.last_mouse.y()
        self.last_mouse = pos

        play_mode = getattr(self.app, "play_mode", None)
        if play_mode and play_mode.is_playing:
            return

        if self.gizmo.is_dragging():
            w2, h2 = max(1, self.width()), max(1, self.height())
            v2, p2 = self.camera.get_matrices(w2, h2)
            self.gizmo.on_mouse_move(pos.x(), pos.y(), v2, p2, w2, h2)
        elif self.right_btn_down and not self.pressed_keys:
            self.camera.orbit(dx, dy)
        elif self.middle_btn_down:
            self.camera.pan(dx, dy)

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y() / 120.0
        Input.on_scroll(delta)
        play_mode = getattr(self.app, "play_mode", None)
        if not (play_mode and play_mode.is_playing):
            self.camera.zoom(delta)

    # ------------------------------------------------------------------
    # Keyboard
    # ------------------------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        self.pressed_keys.add(key)
        Input.on_key_press(key)

        play_mode = getattr(self.app, "play_mode", None)
        if play_mode and play_mode.is_playing:
            play_mode.send_input(key, True)
            super().keyPressEvent(event)
            return

        if key == Qt.Key_W and not (play_mode and play_mode.is_playing):
            self.gizmo.set_mode(TRANSLATE)
        elif key == Qt.Key_E and not (play_mode and play_mode.is_playing):
            self.gizmo.set_mode(ROTATE)
        elif key == Qt.Key_R and not (play_mode and play_mode.is_playing):
            self.gizmo.set_mode(SCALE)
        elif key == Qt.Key_F:
            self.camera.focus_reset()
        elif key == Qt.Key_Delete:
            self.app.main_window.hierarchy.on_delete_entity()
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        key = event.key()
        self.pressed_keys.discard(key)
        Input.on_key_release(key)
        play_mode = getattr(self.app, "play_mode", None)
        if play_mode and play_mode.is_playing:
            play_mode.send_input(key, False)
        super().keyReleaseEvent(event)

    # ------------------------------------------------------------------
    # Picking
    # ------------------------------------------------------------------

    def _try_pick(self, mx: int, my: int) -> None:
        scene = self.app.active_scene
        if scene is None:
            return
        w, h = max(1, self.width()), max(1, self.height())
        view, proj = self.camera.get_matrices(w, h)
        self.app.selector.pick(mx, my, w, h, view, proj, scene, mode=self.camera.mode)
