import time
from typing import Optional

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QImage, QKeyEvent, QMouseEvent, QPainter, QWheelEvent
from PySide6.QtWidgets import QWidget

from core.camera import EditorCamera


class ViewportWidget(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)

        self.renderer = self.app.renderer
        self.camera = EditorCamera(self.app.console)
        self.pressed_keys: set[int] = set()
        self.last_mouse_pos: Optional[QPoint] = None
        self.right_button_pressed = False
        self.middle_button_pressed = False
        self.frame_timer = QTimer(self)
        self.frame_timer.timeout.connect(self.on_frame)
        self.frame_timer.start(16)
        self.last_frame_time = time.time()

    def paintEvent(self, event):
        width = max(1, self.width())
        height = max(1, self.height())
        self.camera.update_matrices(width / height)
        image = self.renderer.render(
            self.camera.view_matrix,
            self.camera.projection_matrix,
            width,
            height,
        )
        painter = QPainter(self)
        painter.drawImage(self.rect(), image)
        painter.end()

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
        scroll_delta = event.angleDelta().y() / 120.0
        self.camera.zoom(scroll_delta)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        self.pressed_keys.add(event.key())
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        self.pressed_keys.discard(event.key())
        super().keyReleaseEvent(event)
