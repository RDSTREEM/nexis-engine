import numpy as np


class Mesh:
    def __init__(self, ctx, vertices):
        self.vbo = ctx.buffer(vertices.astype("f4").tobytes())
        self.ctx = ctx
        self.vao = None

    def build_vao(self, shader):
        self.vao = self.ctx.simple_vertex_array(
            shader.program,
            self.vbo,
            "in_position"
        )

    def render(self):
        if self.vao:
            self.vao.render()