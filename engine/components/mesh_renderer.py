import moderngl
import numpy as np
from engine.components.component import Component


class MeshRenderer(Component):
    def __init__(self, game_object, ctx):
        super().__init__(game_object)

        self.ctx = ctx

        self.program = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec3 in_position;

                void main() {
                    gl_Position = vec4(in_position, 1.0);
                }
            """,
            fragment_shader="""
                #version 330
                out vec4 fragColor;

                void main() {
                    fragColor = vec4(0.2, 0.6, 1.0, 1.0);
                }
            """
        )

        vertices = np.array([
            -0.6, -0.4, 0.0,
             0.6, -0.4, 0.0,
             0.0,  0.6, 0.0,
        ], dtype="f4")

        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.simple_vertex_array(
            self.program,
            self.vbo,
            "in_position"
        )

    def render(self):
        self.vao.render()