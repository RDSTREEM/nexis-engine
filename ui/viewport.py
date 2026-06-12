from __future__ import annotations
import time
from typing import Optional

import moderngl
import numpy as np
from PySide6.QtCore import QPoint, Qt, QEvent, QTimer
from PySide6.QtGui import QKeyEvent, QMouseEvent, QWheelEvent
from PySide6.QtWidgets import QApplication
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
        self.setFocus()

        self.camera = EditorCamera(self.app.console, mode="3d")
        self.debug_draw = DebugDraw()

        self.gizmo = Gizmo()
        self.gizmo.HANDLE_SIZE = 2.0
        self.gizmo.HIT_RADIUS_PX = 16

        self.last_mouse: Optional[QPoint] = None
        self.right_btn_down: bool = False
        self.middle_btn_down: bool = False
        self.left_btn_down: bool = False
        self.pressed_keys: set = set()

        self._free_drag: bool = False
        self._free_drag_start_mouse: Optional[QPoint] = None
        self._free_drag_start_pos: Optional[np.ndarray] = None

        self.last_frame = time.perf_counter()
        self.ctx: Optional[moderngl.Context] = None

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(16)

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
            if scene:
                cam = scene._find_main_camera()
                if cam:
                    cc = cam.clear_color
                    self.ctx.clear(cc[0], cc[1], cc[2], cc[3])
                    view = cam.get_view_matrix()
                    proj = cam.get_projection_matrix(w, h)
                    scene.render_editor(self.ctx, view, proj)
                else:
                    self.ctx.clear(0.05, 0.05, 0.05, 1.0)
                    self._draw_no_camera_msg()
            else:
                self.ctx.clear(0.05, 0.05, 0.05, 1.0)
        else:
            self.ctx.clear(0.1, 0.12, 0.18, 1.0)
            view, proj = self.camera.get_matrices(w, h)
            if scene:
                scene.render_editor(self.ctx, view, proj)

            inv_view = np.linalg.inv(view)
            cam_pos = inv_view[:3, 3]

            self.debug_draw.begin(view, proj)
            if self.camera.mode == "3d":
                self.debug_draw.grid(size=20, spacing=1.0, camera_pos=cam_pos)
                self.debug_draw.axis_gizmo((0, 0, 0), size=1.5)
            else:
                self.debug_draw.grid_2d(size=20, spacing=1.0, camera_pos=cam_pos)
            sel = self.app.selector.get_selection_aabb()
            if sel is not None:
                center, half = sel
                self.debug_draw.selection_box(center, half + 0.05)
            self.debug_draw.end()

            self.gizmo.set_entity(self.app.selector.selected_entity)
            self.gizmo.set_2d(self.camera.mode == "2d")
            self.debug_draw.begin(view, proj)
            self.gizmo.draw(self.debug_draw, view, proj, w, h)
            self.debug_draw.end()

    def _draw_no_camera_msg(self):
        pass

    def resizeGL(self, w, h):
        if self.ctx:
            self.ctx.viewport = (0, 0, w, h)

    def showEvent(self, event):
        super().showEvent(event)

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

        mw = getattr(self.app, "main_window", None)
        if mw and hasattr(mw, "toolbar"):
            from core.time_manager import Time

            if play_mode and play_mode.is_playing:
                mw.toolbar.set_fps(Time.fps)
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        self.setFocus()
        pos = event.position().toPoint()
        self.last_mouse = pos
        btn = event.button()
        Input.on_mouse_press(btn.value)

        play_mode = getattr(self.app, "play_mode", None)
        playing = play_mode is not None and play_mode.is_playing

        if btn == Qt.LeftButton:
            self.left_btn_down = True
            if not playing:
                w2, h2 = max(1, self.width()), max(1, self.height())
                v2, p2 = self.camera.get_matrices(w2, h2)
                hit = self.gizmo.on_mouse_press(pos.x(), pos.y(), v2, p2, w2, h2)
                if not hit:
                    picked = self._try_pick(pos.x(), pos.y())
                    if picked is not None:
                        self._free_drag = True
                        self._free_drag_start_mouse = pos
                        self._free_drag_start_pos = picked.transform.position.copy()
        elif btn == Qt.RightButton:
            self.right_btn_down = True
            self.setCursor(Qt.ClosedHandCursor)
        elif btn == Qt.MiddleButton:
            self.middle_btn_down = True
            self.setCursor(Qt.SizeAllCursor)

    def mouseReleaseEvent(self, event: QMouseEvent):
        Input.on_mouse_release(event.button().value)

        if self.gizmo.is_dragging():
            e = self.app.selector.selected_entity
            if e is not None:
                from core.undo_redo import SetPropertyCommand, UndoStack

                t = e.transform
                if (
                    self.gizmo.mode == TRANSLATE
                    and self.gizmo._drag_start_pos is not None
                ):
                    UndoStack._undo.append(
                        SetPropertyCommand(
                            t,
                            "position",
                            self.gizmo._drag_start_pos,
                            t.position.copy(),
                            f"Move '{e.name}'",
                        )
                    )
                    UndoStack._redo.clear()
                    UndoStack._notify()
                elif (
                    self.gizmo.mode == SCALE
                    and self.gizmo._drag_start_scale is not None
                ):
                    UndoStack._undo.append(
                        SetPropertyCommand(
                            t,
                            "scale",
                            self.gizmo._drag_start_scale,
                            t.scale.copy(),
                            f"Scale '{e.name}'",
                        )
                    )
                    UndoStack._redo.clear()
                    UndoStack._notify()
        self.gizmo.on_mouse_release()

        if self._free_drag:
            e = self.app.selector.selected_entity
            if e is not None and self._free_drag_start_pos is not None:
                from core.undo_redo import SetPropertyCommand, UndoStack

                UndoStack._undo.append(
                    SetPropertyCommand(
                        e.transform,
                        "position",
                        self._free_drag_start_pos,
                        e.transform.position.copy(),
                        f"Move '{e.name}'",
                    )
                )
                UndoStack._redo.clear()
                UndoStack._notify()
            self._free_drag = False
            self._free_drag_start_mouse = None
            self._free_drag_start_pos = None

        if event.button() == Qt.LeftButton:
            self.left_btn_down = False
        elif event.button() == Qt.RightButton:
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

        mw = getattr(self.app, "main_window", None)

        if self.gizmo.is_dragging():
            w2, h2 = max(1, self.width()), max(1, self.height())
            v2, p2 = self.camera.get_matrices(w2, h2)
            self.gizmo.on_mouse_move(pos.x(), pos.y(), v2, p2, w2, h2)
            if mw and hasattr(mw, "inspector") and self.app.selector.selected_entity:
                mw.inspector.show_entity(self.app.selector.selected_entity)

        elif self._free_drag and self.left_btn_down:
            e = self.app.selector.selected_entity
            if e is not None:
                w2, h2 = max(1, self.width()), max(1, self.height())
                v2, p2 = self.camera.get_matrices(w2, h2)
                if self.camera.mode == "2d":
                    from core.raycast import world_pos_from_screen_2d

                    cur = world_pos_from_screen_2d(pos.x(), pos.y(), w2, h2, v2, p2)
                    prev = world_pos_from_screen_2d(
                        pos.x() - dx, pos.y() - dy, w2, h2, v2, p2
                    )
                    d = cur - prev
                    e.transform.position[0] += d[0]
                    e.transform.position[1] += d[1]
                else:
                    from core.raycast import ray_from_screen_3d

                    def _xz(mx, my):
                        ray = ray_from_screen_3d(mx, my, w2, h2, v2, p2)
                        ey = e.transform.position[1]
                        ddy = ray.direction[1]
                        if abs(ddy) < 1e-8:
                            return None
                        tt = (ey - ray.origin[1]) / ddy
                        return ray.at(tt)

                    c = _xz(pos.x(), pos.y())
                    p = _xz(pos.x() - dx, pos.y() - dy)
                    if c is not None and p is not None:
                        e.transform.position[0] += c[0] - p[0]
                        e.transform.position[2] += c[2] - p[2]
                e.transform._dirty = True
                if mw and hasattr(mw, "inspector"):
                    mw.inspector.show_entity(e)

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

    def keyPressEvent(self, event: QKeyEvent):
        self._handle_key_press(event)
        key = event.key()
        play_mode = getattr(self.app, "play_mode", None)
        if play_mode and play_mode.is_playing:
            play_mode.send_input(key, True)
            super().keyPressEvent(event)
            return

        if not self.right_btn_down:
            if key == Qt.Key_W:
                self.gizmo.set_mode(TRANSLATE)
            elif key == Qt.Key_E:
                self.gizmo.set_mode(ROTATE)
            elif key == Qt.Key_R:
                self.gizmo.set_mode(SCALE)

        if key == Qt.Key_F:
            self.camera.focus_reset()
        elif key == Qt.Key_Delete:
            self.app.main_window.hierarchy.on_delete_entity()
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        self._handle_key_release(event)
        super().keyReleaseEvent(event)

    def _handle_key_press(self, event: QKeyEvent):
        key = event.key()
        self.pressed_keys.add(key)
        Input.on_key_press(key)

    def _handle_key_release(self, event: QKeyEvent):
        key = event.key()
        self.pressed_keys.discard(key)
        Input.on_key_release(key)
        play_mode = getattr(self.app, "play_mode", None)
        if play_mode and play_mode.is_playing:
            play_mode.send_input(key, False)

    def _try_pick(self, mx, my):
        scene = self.app.active_scene
        if scene is None:
            return None
        w, h = max(1, self.width()), max(1, self.height())
        view, proj = self.camera.get_matrices(w, h)
        return self.app.selector.pick(
            mx, my, w, h, view, proj, scene, mode=self.camera.mode
        )
