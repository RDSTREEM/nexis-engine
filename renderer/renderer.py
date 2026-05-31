import time

import moderngl
import numpy as np
from PySide6.QtGui import QImage


class Renderer:
    def __init__(self, app):
        self.app = app
        self.app.console.info("Renderer subsystem initialized.")
        self.ctx = moderngl.create_standalone_context()
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
        self.vbo = self.ctx.buffer(self.vertices.tobytes())
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.vbo, "3f 3f", "in_position", "in_color")],
        )
        self.fbo = None
        self.last_time = time.time()
        self.frame_count = 0

    def _make_framebuffer(self, width: int, height: int):
        color_attachment = self.ctx.texture((width, height), 3, dtype="u1")
        depth_attachment = self.ctx.depth_renderbuffer((width, height))
        fbo = self.ctx.framebuffer(
            color_attachments=[color_attachment], depth_attachment=depth_attachment
        )
        return fbo

    def render(
        self,
        view_matrix: np.ndarray,
        projection_matrix: np.ndarray,
        width: int,
        height: int,
    ) -> QImage:
        if width <= 0 or height <= 0:
            return QImage()

        if self.fbo is None or self.fbo.size != (width, height):
            self.fbo = self._make_framebuffer(width, height)

        self.fbo.use()
        self.ctx.viewport = (0, 0, width, height)
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.clear(1.0, 0.0, 0.0, 1.0)

        self.prog["u_view"].write(view_matrix.astype("f4").T.tobytes())
        self.prog["u_projection"].write(projection_matrix.astype("f4").T.tobytes())
        import sys

        print("view matrix:", view_matrix, file=sys.stderr)
        print("proj matrix:", projection_matrix, file=sys.stderr)
        print("fbo size:", self.fbo.size, file=sys.stderr)
        print("viewport:", self.ctx.viewport, file=sys.stderr)
        self.vao.render()
        self.frame_count += 1
        now = time.time()
        if now - self.last_time >= 1.0:
            fps = self.frame_count / (now - self.last_time)
            self.app.console.info(f"Render loop FPS: {fps:.1f}")
            self.frame_count = 0
            self.last_time = now

        data = self.fbo.read(components=3, alignment=1)
        print("data length:", len(data), file=sys.stderr)
        # Check if all pixels are the background color (roughly 0.1, 0.12, 0.18)
        import numpy as np

        arr = np.frombuffer(data, dtype=np.uint8).reshape(-1, 3)
        print("unique colors sample:", arr[::1000], file=sys.stderr)
        image = QImage(data, width, height, width * 3, QImage.Format_RGB888).mirrored(
            False, True
        )
        return image.copy()
