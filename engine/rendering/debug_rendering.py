import numpy as np


class DebugRenderer:

    def __init__(self, ctx):
        self.ctx = ctx
        self.lines = []

    def draw_line(self, start, end):
        self.lines.append((*start, *end))

    def clear(self):
        self.lines.clear()

    def render(self, shader):
        if not self.lines:
            return

        vertices = []
        for line in self.lines:
            vertices.extend(line[:3])
            vertices.extend(line[3:])

        vertices = np.array(vertices, dtype="f4")

        vbo = self.ctx.buffer(vertices.tobytes())

        vao = self.ctx.simple_vertex_array(shader.program, vbo, "in_position")

        vao.render(mode=self.ctx.LINES)

        vbo.release()
        vao.release()
