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

        self.camera = EditorCamera(self.app.console)
        self.pressed_keys: set[int] = set()
        self.last_mouse_pos: Optional[QPoint] = None
        self.right_button_pressed = False
        self.middle_button_pressed = False
        self.mgl_ctx = None

        self.frame_timer = QTimer(self)
        self.frame_timer.timeout.connect(self.on_frame)
        self.frame_timer.start(16)
        self.last_frame_time = time.time()

    def initializeGL(self):
        self.mgl_ctx = moderngl.create_context()
        self.app.renderer.init_gl(self.mgl_ctx)
        self.app.console.info("OpenGL context initialized in viewport.")

    def resizeGL(self, width: int, height: int):
        if self.mgl_ctx:
            self.mgl_ctx.viewport = (0, 0, width, height)

    def paintGL(self):
        width = max(1, self.width())
        height = max(1, self.height())
        self.camera.update_matrices(width / height)
        if self.mgl_ctx and self.app.renderer.is_ready():
            self.app.renderer.render_gl(
                self.camera.view_matrix,
                self.camera.projection_matrix,
                width,
                height,
            )

    def on_frame(self):
        now = time.time()
        delta_time = min(0.033, now - self.last_frame_time)
        self.last_frame_time = now
        self.camera.update(self.pressed_keys, delta_time)
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.last_mouse_pos = event.position().toPoint()
        if event.button() == Qt.RightButton:
            self.right_button_pressed = True
            self.setCursor(Qt.ClosedHandCursor)
        elif event.button() == Qt.MiddleButton:
            self.middle_button_pressed = True
            self.setCursor(Qt.SizeAllCursor)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.RightButton:
            self.right_button_pressed = False
        elif event.button() == Qt.MiddleButton:
            self.middle_button_pressed = False
        self.setCursor(Qt.ArrowCursor)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.last_mouse_pos is None:
            self.last_mouse_pos = event.position().toPoint()
            return
        current_pos = event.position().toPoint()
        delta = current_pos - self.last_mouse_pos
        self.last_mouse_pos = current_pos
        if self.right_button_pressed:
            self.camera.orbit(delta.x(), delta.y())
        elif self.middle_button_pressed:
            self.camera.pan(delta.x(), delta.y())

    def wheelEvent(self, event: QWheelEvent) -> None:
        self.camera.zoom(event.angleDelta().y() / 120.0)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        self.pressed_keys.add(event.key())
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        self.pressed_keys.discard(event.key())
        super().keyReleaseEvent(event)
