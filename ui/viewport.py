import time
from typing import Optional

import moderngl
from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QKeyEvent, QMouseEvent, QWheelEvent
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from core.camera import EditorCamera


class ViewportWidget(QOpenGLWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)

        self.camera = EditorCamera(self.app.console, mode="3d")

        self.last_mouse: Optional[QPoint] = None
        self.right_btn_down: bool = False
        self.middle_btn_down: bool = False
        self.pressed_keys: set = set()

        self.last_frame = time.time()
        self.ctx: Optional[moderngl.Context] = None

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(16)

    # ------------------------------------------------------------------
    # GL lifecycle
    # ------------------------------------------------------------------

    def initializeGL(self):
        self.ctx = moderngl.create_context()
        self.app.console.info("ViewportWidget: GL context ready.")

    def paintGL(self):
        if self.ctx is None:
            return
        w, h = max(1, self.width()), max(1, self.height())

        fbo = self.ctx.detect_framebuffer(self.defaultFramebufferObject())
        fbo.use()
        self.ctx.viewport = (0, 0, w, h)
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.clear(0.1, 0.12, 0.18, 1.0)

        view, proj = self.camera.get_matrices(w, h)

        # render the active scene if one is loaded
        scene = getattr(self.app, "active_scene", None)
        if scene is not None:
            scene.render_editor(self.ctx, view, proj)

    def resizeGL(self, w, h):
        if self.ctx:
            self.ctx.viewport = (0, 0, w, h)

    # ------------------------------------------------------------------
    # Tick
    # ------------------------------------------------------------------

    def _on_tick(self):
        now = time.time()
        dt = min(0.05, now - self.last_frame)
        self.last_frame = now
        if self.right_btn_down and self.pressed_keys:
            self.camera.fly(self.pressed_keys, dt)
        self.update()

    # ------------------------------------------------------------------
    # Mouse
    # ------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent):
        self.last_mouse = event.position().toPoint()
        if event.button() == Qt.RightButton:
            self.right_btn_down = True
            self.setCursor(Qt.ClosedHandCursor)
        elif event.button() == Qt.MiddleButton:
            self.middle_btn_down = True
            self.setCursor(Qt.SizeAllCursor)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.RightButton:
            self.right_btn_down = False
        elif event.button() == Qt.MiddleButton:
            self.middle_btn_down = False
        self.setCursor(Qt.ArrowCursor)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.last_mouse is None:
            self.last_mouse = event.position().toPoint()
            return
        cur = event.position().toPoint()
        dx = cur.x() - self.last_mouse.x()
        dy = cur.y() - self.last_mouse.y()
        self.last_mouse = cur
        if self.right_btn_down and not self.pressed_keys:
            self.camera.orbit(dx, dy)
        elif self.middle_btn_down:
            self.camera.pan(dx, dy)

    def wheelEvent(self, event: QWheelEvent):
        self.camera.zoom(event.angleDelta().y() / 120.0)

    # ------------------------------------------------------------------
    # Keyboard
    # ------------------------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent):
        self.pressed_keys.add(event.key())
        if event.key() == Qt.Key_F:
            self.camera.focus_reset()
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        self.pressed_keys.discard(event.key())
        super().keyReleaseEvent(event)
