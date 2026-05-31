import moderngl
from PySide6.QtCore import Qt, QTimer
from PySide6.QtOpenGLWidgets import QOpenGLWidget


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
                in vec2 in_vert;
                in vec3 in_color;
                out vec3 v_color;
                void main() {
                    gl_Position = vec4(in_vert, 0.0, 1.0);
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

        # A single triangle in NDC — should fill roughly half the screen
        import numpy as np

        vertices = np.array(
            [
                # x,    y,    r,    g,    b
                0.0,
                0.8,
                1.0,
                0.0,
                0.0,
                -0.8,
                -0.8,
                0.0,
                1.0,
                0.0,
                0.8,
                -0.8,
                0.0,
                0.0,
                1.0,
            ],
            dtype="f4",
        )

        vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(vbo, "2f 3f", "in_vert", "in_color")],
        )
        self.app.console.info("ViewportWidget: GL initialized, triangle ready.")

    def paintGL(self):
        if self.ctx is None:
            return
        fbo = self.ctx.detect_framebuffer(self.defaultFramebufferObject())
        fbo.use()
        self.ctx.viewport = (0, 0, self.width(), self.height())
        self.ctx.clear(0.1, 0.12, 0.18, 1.0)
        self.vao.render(moderngl.TRIANGLES)

    def resizeGL(self, w, h):
        if self.ctx:
            self.ctx.viewport = (0, 0, w, h)
