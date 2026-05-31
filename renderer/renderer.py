import time

import moderngl
import numpy as np


class Renderer:
    def __init__(self, app):
        self.app = app
        self.app.console.info("Renderer subsystem initialized.")
        self.ctx = None
        self.prog = None
        self.vbo = None
        self.vao = None
        self.default_fbo = None
        self.last_time = time.time()
        self.frame_count = 0

        self.vertices = np.array(
            [
                # front face
                -1.0,
                -1.0,
                1.0,
                1.0,
                0.2,
                0.2,
                1.0,
                -1.0,
                1.0,
                0.2,
                1.0,
                0.2,
                1.0,
                1.0,
                1.0,
                0.2,
                0.2,
                1.0,
                -1.0,
                -1.0,
                1.0,
                1.0,
                0.2,
                0.2,
                1.0,
                1.0,
                1.0,
                0.2,
                0.2,
                1.0,
                -1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                0.2,
                # back face
                -1.0,
                -1.0,
                -1.0,
                0.2,
                1.0,
                1.0,
                1.0,
                1.0,
                -1.0,
                1.0,
                0.2,
                1.0,
                1.0,
                -1.0,
                -1.0,
                0.3,
                0.7,
                0.9,
                -1.0,
                -1.0,
                -1.0,
                0.2,
                1.0,
                1.0,
                -1.0,
                1.0,
                -1.0,
                0.7,
                0.3,
                0.6,
                1.0,
                1.0,
                -1.0,
                1.0,
                0.2,
                1.0,
                # left face
                -1.0,
                -1.0,
                -1.0,
                0.4,
                0.4,
                1.0,
                -1.0,
                -1.0,
                1.0,
                0.4,
                1.0,
                0.4,
                -1.0,
                1.0,
                1.0,
                1.0,
                0.6,
                0.2,
                -1.0,
                -1.0,
                -1.0,
                0.4,
                0.4,
                1.0,
                -1.0,
                1.0,
                1.0,
                1.0,
                0.6,
                0.2,
                -1.0,
                1.0,
                -1.0,
                0.8,
                0.2,
                0.6,
                # right face
                1.0,
                -1.0,
                -1.0,
                1.0,
                0.5,
                0.2,
                1.0,
                1.0,
                1.0,
                0.2,
                0.8,
                0.4,
                1.0,
                -1.0,
                1.0,
                0.2,
                0.2,
                0.8,
                1.0,
                -1.0,
                -1.0,
                1.0,
                0.5,
                0.2,
                1.0,
                1.0,
                -1.0,
                0.9,
                0.8,
                0.2,
                1.0,
                1.0,
                1.0,
                0.2,
                0.8,
                0.4,
                # top face
                -1.0,
                1.0,
                -1.0,
                0.7,
                1.0,
                0.3,
                -1.0,
                1.0,
                1.0,
                0.6,
                0.4,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                0.7,
                0.4,
                -1.0,
                1.0,
                -1.0,
                0.7,
                1.0,
                0.3,
                1.0,
                1.0,
                1.0,
                1.0,
                0.7,
                0.4,
                1.0,
                1.0,
                -1.0,
                0.8,
                0.2,
                0.9,
                # bottom face
                -1.0,
                -1.0,
                -1.0,
                0.9,
                0.4,
                0.3,
                1.0,
                -1.0,
                1.0,
                0.4,
                0.9,
                0.6,
                -1.0,
                -1.0,
                1.0,
                0.3,
                0.3,
                0.9,
                -1.0,
                -1.0,
                -1.0,
                0.9,
                0.4,
                0.3,
                1.0,
                -1.0,
                -1.0,
                0.2,
                0.6,
                0.9,
                1.0,
                -1.0,
                1.0,
                0.4,
                0.9,
                0.6,
            ],
            dtype="f4",
        )

    def init_gl(self, ctx: moderngl.Context):
        """Called once after QOpenGLWidget creates the GL context."""
        self.ctx = ctx
        self.prog = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec3 in_position;
                in vec3 in_color;
                uniform mat4 u_view;
                uniform mat4 u_projection;
                out vec3 v_color;
                void main() {
                    gl_Position = u_projection * u_view * vec4(in_position, 1.0);
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
        self.vbo = self.ctx.buffer(self.vertices.tobytes())
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.vbo, "3f 3f", "in_position", "in_color")],
        )
        self.app.console.info("Renderer GL resources created.")

    def set_default_fbo(self, fbo_id: int):
        """Store Qt's actual framebuffer so moderngl renders into the right place."""
        if self.ctx is not None:
            self.default_fbo = self.ctx.detect_framebuffer(fbo_id)

    def is_ready(self) -> bool:
        return (
            self.ctx is not None
            and self.prog is not None
            and self.vao is not None
            and self.default_fbo is not None
        )

    def render_gl(
        self,
        view_matrix: np.ndarray,
        projection_matrix: np.ndarray,
        width: int,
        height: int,
    ) -> None:
        """Renders directly into QOpenGLWidget's framebuffer."""
        self.default_fbo.use()
        self.ctx.viewport = (0, 0, width, height)
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.clear(0.1, 0.12, 0.18, 1.0)

        self.prog["u_view"].write(view_matrix.astype("f4").T.tobytes())
        self.prog["u_projection"].write(projection_matrix.astype("f4").T.tobytes())
        self.vao.render()

        self.frame_count += 1
        now = time.time()
        if now - self.last_time >= 1.0:
            fps = self.frame_count / (now - self.last_time)
            self.app.console.info(f"FPS: {fps:.1f}")
            self.frame_count = 0
            self.last_time = now
