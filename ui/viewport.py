import math

import moderngl
import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtOpenGLWidgets import QOpenGLWidget


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


VERTICES = np.array(
    [
        # front face
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
        # back face
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
        # left face
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
        # right face
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
        # top face
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
        # bottom face
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


class ViewportWidget(QOpenGLWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setFocusPolicy(Qt.StrongFocus)
        self.ctx = None
        self.prog = None
        self.vao = None

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(16)

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
            self.prog,
            [(vbo, "3f 3f", "in_vert", "in_color")],
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

        view = look_at([4, 3, 6], [0, 0, 0], [0, 1, 0])
        proj = perspective(45.0, w / h, 0.1, 100.0)

        self.prog["u_view"].write(view.T.tobytes())
        self.prog["u_proj"].write(proj.T.tobytes())
        self.vao.render(moderngl.TRIANGLES)

    def resizeGL(self, w, h):
        if self.ctx:
            self.ctx.viewport = (0, 0, w, h)
