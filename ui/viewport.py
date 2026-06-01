import math
from typing import Optional

import moderngl
import numpy as np
from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QKeyEvent, QMouseEvent, QWheelEvent
from PySide6.QtOpenGLWidgets import QOpenGLWidget

# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------


def look_at(eye, target, up):
    eye = np.array(eye, dtype="f4")
    target = np.array(target, dtype="f4")
    up = np.array(up, dtype="f4")
    f = target - eye
    f = f / np.linalg.norm(f)
    r = np.cross(f, up)
    r = r / np.linalg.norm(r)
    u = np.cross(r, f)
    m = np.eye(4, dtype="f4")
    m[0, :3] = r
    m[1, :3] = u
    m[2, :3] = -f
    m[:3, 3] = [-np.dot(r, eye), -np.dot(u, eye), np.dot(f, eye)]
    return m


def perspective(fov_deg, aspect, near, far):
    f = 1.0 / math.tan(math.radians(fov_deg) / 2)
    m = np.zeros((4, 4), dtype="f4")
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = (2 * far * near) / (near - far)
    m[3, 2] = -1.0
    return m


# ---------------------------------------------------------------------------
# Vertex data — colourful cube
# ---------------------------------------------------------------------------

VERTICES = np.array(
    [
        # front
        -1,
        -1,
        1,
        1.0,
        0.2,
        0.2,
        1,
        -1,
        1,
        0.2,
        1.0,
        0.2,
        1,
        1,
        1,
        0.2,
        0.2,
        1.0,
        -1,
        -1,
        1,
        1.0,
        0.2,
        0.2,
        1,
        1,
        1,
        0.2,
        0.2,
        1.0,
        -1,
        1,
        1,
        1.0,
        1.0,
        0.2,
        # back
        -1,
        -1,
        -1,
        0.2,
        1.0,
        1.0,
        1,
        1,
        -1,
        1.0,
        0.2,
        1.0,
        1,
        -1,
        -1,
        0.3,
        0.7,
        0.9,
        -1,
        -1,
        -1,
        0.2,
        1.0,
        1.0,
        -1,
        1,
        -1,
        0.7,
        0.3,
        0.6,
        1,
        1,
        -1,
        1.0,
        0.2,
        1.0,
        # left
        -1,
        -1,
        -1,
        0.4,
        0.4,
        1.0,
        -1,
        -1,
        1,
        0.4,
        1.0,
        0.4,
        -1,
        1,
        1,
        1.0,
        0.6,
        0.2,
        -1,
        -1,
        -1,
        0.4,
        0.4,
        1.0,
        -1,
        1,
        1,
        1.0,
        0.6,
        0.2,
        -1,
        1,
        -1,
        0.8,
        0.2,
        0.6,
        # right
        1,
        -1,
        -1,
        1.0,
        0.5,
        0.2,
        1,
        1,
        1,
        0.2,
        0.8,
        0.4,
        1,
        -1,
        1,
        0.2,
        0.2,
        0.8,
        1,
        -1,
        -1,
        1.0,
        0.5,
        0.2,
        1,
        1,
        -1,
        0.9,
        0.8,
        0.2,
        1,
        1,
        1,
        0.2,
        0.8,
        0.4,
        # top
        -1,
        1,
        -1,
        0.7,
        1.0,
        0.3,
        -1,
        1,
        1,
        0.6,
        0.4,
        1.0,
        1,
        1,
        1,
        1.0,
        0.7,
        0.4,
        -1,
        1,
        -1,
        0.7,
        1.0,
        0.3,
        1,
        1,
        1,
        1.0,
        0.7,
        0.4,
        1,
        1,
        -1,
        0.8,
        0.2,
        0.9,
        # bottom
        -1,
        -1,
        -1,
        0.9,
        0.4,
        0.3,
        1,
        -1,
        1,
        0.4,
        0.9,
        0.6,
        -1,
        -1,
        1,
        0.3,
        0.3,
        0.9,
        -1,
        -1,
        -1,
        0.9,
        0.4,
        0.3,
        1,
        -1,
        -1,
        0.2,
        0.6,
        0.9,
        1,
        -1,
        1,
        0.4,
        0.9,
        0.6,
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

        # --- camera state ---
        self.cam_target = np.array([0.0, 0.0, 0.0], dtype="f4")
        self.cam_distance = 8.0
        self.cam_yaw = math.radians(45.0)  # horizontal angle
        self.cam_pitch = math.radians(25.0)  # vertical angle
        self.cam_up = np.array([0.0, 1.0, 0.0], dtype="f4")

        # --- input state ---
        self.last_mouse: Optional[QPoint] = None
        self.right_btn_down: bool = False
        self.middle_btn_down: bool = False

        # --- sensitivity ---
        self.ORBIT_SENS = 0.005
        self.PAN_SENS = 0.003
        self.ZOOM_SENS = 0.12

        # --- GL ---
        self.ctx = None
        self.prog = None
        self.vao = None

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(16)

    # ------------------------------------------------------------------
    # Camera helpers
    # ------------------------------------------------------------------

    def _cam_position(self) -> np.ndarray:
        cp = math.cos(self.cam_pitch)
        return self.cam_target + self.cam_distance * np.array(
            [
                cp * math.sin(self.cam_yaw),
                math.sin(self.cam_pitch),
                cp * math.cos(self.cam_yaw),
            ],
            dtype="f4",
        )

    def _view_matrix(self) -> np.ndarray:
        return look_at(self._cam_position(), self.cam_target, self.cam_up)

    def _proj_matrix(self, w: int, h: int) -> np.ndarray:
        return perspective(45.0, w / h, 0.1, 1000.0)

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
        vbo = self.ctx.buffer(VERTICES.tobytes())
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
        self.prog["u_view"].write(self._view_matrix().T.tobytes())
        self.prog["u_proj"].write(self._proj_matrix(w, h).T.tobytes())
        self.vao.render(moderngl.TRIANGLES)

    def resizeGL(self, w, h):
        if self.ctx:
            self.ctx.viewport = (0, 0, w, h)

    # ------------------------------------------------------------------
    # Mouse input
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

        if self.right_btn_down:
            self._orbit(dx, dy)
        elif self.middle_btn_down:
            self._pan(dx, dy)

    def wheelEvent(self, event: QWheelEvent):
        self._zoom(event.angleDelta().y() / 120.0)

    # ------------------------------------------------------------------
    # Camera operations
    # ------------------------------------------------------------------

    def _orbit(self, dx: float, dy: float):
        self.cam_yaw += dx * self.ORBIT_SENS
        self.cam_pitch -= dy * self.ORBIT_SENS
        # clamp pitch so camera never flips
        self.cam_pitch = max(
            math.radians(-89.0), min(math.radians(89.0), self.cam_pitch)
        )

    def _pan(self, dx: float, dy: float):
        # move target along camera's local right and up axes
        eye = self._cam_position()
        forward = self.cam_target - eye
        forward = forward / np.linalg.norm(forward)
        right = np.cross(forward, self.cam_up)
        right = right / np.linalg.norm(right)
        up = np.cross(right, forward)

        scale = self.cam_distance * self.PAN_SENS
        self.cam_target -= right * dx * scale
        self.cam_target += up * dy * scale

    def _zoom(self, delta: float):
        self.cam_distance *= 1.0 - delta * self.ZOOM_SENS
        self.cam_distance = max(0.5, min(500.0, self.cam_distance))

    # ------------------------------------------------------------------
    # Keyboard (WASD moves the target, like Blender's G key-ish)
    # ------------------------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent):
        step = self.cam_distance * 0.05
        eye = self._cam_position()
        forward = self.cam_target - eye
        forward[1] = 0  # keep movement horizontal
        norm = np.linalg.norm(forward)
        if norm > 1e-6:
            forward = forward / norm
        right = np.cross(forward, self.cam_up)
        right = right / np.linalg.norm(right)

        key = event.key()
        if key == Qt.Key_W:
            self.cam_target += forward * step
        elif key == Qt.Key_S:
            self.cam_target -= forward * step
        elif key == Qt.Key_A:
            self.cam_target -= right * step
        elif key == Qt.Key_D:
            self.cam_target += right * step
        elif key == Qt.Key_Q:
            self.cam_target[1] += step
        elif key == Qt.Key_E:
            self.cam_target[1] -= step
        else:
            super().keyPressEvent(event)
        self.update()
