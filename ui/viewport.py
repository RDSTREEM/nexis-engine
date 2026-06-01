import time
from typing import Optional

import moderngl
import numpy as np
from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QKeyEvent, QMouseEvent, QWheelEvent
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from core.camera import EditorCamera

# ---------------------------------------------------------------------------
# Temporary cube geometry — will move to renderer/mesh later
# ---------------------------------------------------------------------------

CUBE_VERTS = np.array(
    [
        # fmt: off
    # front
    -1, -1,  1,  1.0, 0.2, 0.2,
     1, -1,  1,  0.2, 1.0, 0.2,
     1,  1,  1,  0.2, 0.2, 1.0,
    -1, -1,  1,  1.0, 0.2, 0.2,
     1,  1,  1,  0.2, 0.2, 1.0,
    -1,  1,  1,  1.0, 1.0, 0.2,
    # back
    -1, -1, -1,  0.2, 1.0, 1.0,
     1,  1, -1,  1.0, 0.2, 1.0,
     1, -1, -1,  0.3, 0.7, 0.9,
    -1, -1, -1,  0.2, 1.0, 1.0,
    -1,  1, -1,  0.7, 0.3, 0.6,
     1,  1, -1,  1.0, 0.2, 1.0,
    # left
    -1, -1, -1,  0.4, 0.4, 1.0,
    -1, -1,  1,  0.4, 1.0, 0.4,
    -1,  1,  1,  1.0, 0.6, 0.2,
    -1, -1, -1,  0.4, 0.4, 1.0,
    -1,  1,  1,  1.0, 0.6, 0.2,
    -1,  1, -1,  0.8, 0.2, 0.6,
    # right
     1, -1, -1,  1.0, 0.5, 0.2,
     1,  1,  1,  0.2, 0.8, 0.4,
     1, -1,  1,  0.2, 0.2, 0.8,
     1, -1, -1,  1.0, 0.5, 0.2,
     1,  1, -1,  0.9, 0.8, 0.2,
     1,  1,  1,  0.2, 0.8, 0.4,
    # top
    -1,  1, -1,  0.7, 1.0, 0.3,
    -1,  1,  1,  0.6, 0.4, 1.0,
     1,  1,  1,  1.0, 0.7, 0.4,
    -1,  1, -1,  0.7, 1.0, 0.3,
     1,  1,  1,  1.0, 0.7, 0.4,
     1,  1, -1,  0.8, 0.2, 0.9,
    # bottom
    -1, -1, -1,  0.9, 0.4, 0.3,
     1, -1,  1,  0.4, 0.9, 0.6,
    -1, -1,  1,  0.3, 0.3, 0.9,
    -1, -1, -1,  0.9, 0.4, 0.3,
     1, -1, -1,  0.2, 0.6, 0.9,
     1, -1,  1,  0.4, 0.9, 0.6,
        # fmt: on
    ],
    dtype="f4",
)


# ---------------------------------------------------------------------------
# Viewport
# ---------------------------------------------------------------------------


class ViewportWidget(QOpenGLWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)

        self.camera = EditorCamera(self.app.console, mode="3d")

        # input state
        self.last_mouse: Optional[QPoint] = None
        self.right_btn_down: bool = False
        self.middle_btn_down: bool = False
        self.pressed_keys: set = set()

        # timing
        self.last_frame = time.time()

        # GL objects
        self.ctx = None
        self.prog = None
        self.vao = None

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(16)

    # ------------------------------------------------------------------
    # GL lifecycle
    # ------------------------------------------------------------------

    def initializeGL(self):
        self.ctx = moderngl.create_context()
        self.prog = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec3 in_vert;
                in vec3 in_color;
                uniform mat4 u_view;
                uniform mat4 u_proj;
                out vec3 v_color;
                void main() {
                    gl_Position = u_proj * u_view * vec4(in_vert, 1.0);
                    v_color = in_color;
                }
            """,
            fragment_shader="""
                #version 330
                in vec3 v_color;
                out vec4 f_color;
                void main() {
                    f_color = vec4(v_color, 1.0);
                }
            """,
        )
        vbo = self.ctx.buffer(CUBE_VERTS.tobytes())
        self.vao = self.ctx.vertex_array(
            self.prog, [(vbo, "3f 3f", "in_vert", "in_color")]
        )
        self.app.console.info("ViewportWidget: GL initialized.")

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
        self.prog["u_view"].write(view.T.tobytes())
        self.prog["u_proj"].write(proj.T.tobytes())
        self.vao.render(moderngl.TRIANGLES)

    def resizeGL(self, w, h):
        if self.ctx:
            self.ctx.viewport = (0, 0, w, h)

    # ------------------------------------------------------------------
    # Tick — fly mode needs per-frame update
    # ------------------------------------------------------------------

    def _on_tick(self):
        now = time.time()
        dt = min(0.05, now - self.last_frame)
        self.last_frame = now

        # only fly when right button is held AND keys are pressed
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

        # right drag without keys = orbit; with keys = fly (handled in tick)
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
