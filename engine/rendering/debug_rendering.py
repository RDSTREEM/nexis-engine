import numpy as np


class DebugDraw:
    ctx = None
    lines = []

    @classmethod
    def init(cls, ctx):
        cls.ctx = ctx

    @classmethod
    def line(cls, start, end):
        cls.lines.append((*start, *end))

    @classmethod
    def clear(cls):
        cls.lines.clear()

    @classmethod
    def render(cls, shader, projection=None, view=None):
        if not cls.lines:
            return

        # Set MVP matrix for debug rendering (world space)
        if projection is not None and view is not None:
            mvp = projection @ view
            shader.set_uniform_matrix("mvp", mvp)

        vertices = []
        for line in cls.lines:
            vertices.extend(line[:3])
            vertices.extend(line[3:])

        vertices = np.array(vertices, dtype="f4")

        vbo = cls.ctx.buffer(vertices.tobytes())

        vao = cls.ctx.simple_vertex_array(shader.program, vbo, "in_position")

        vao.render(mode=cls.ctx.LINES)

        vbo.release()
        vao.release()

    @classmethod
    def grid(cls, size=10, step=1):
        for i in range(-size, size + 1, step):
            cls.line((i, 0, -size), (i, 0, size))
            cls.line((-size, 0, i), (size, 0, i))

    @classmethod
    def box(cls, center, size):
        x, y, z = center
        if isinstance(size, (list, tuple)):
            sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
        else:
            sx = sy = sz = size / 2

        # Bottom face
        cls.line((x - sx, y - sy, z - sz), (x + sx, y - sy, z - sz))
        cls.line((x + sx, y - sy, z - sz), (x + sx, y - sy, z + sz))
        cls.line((x + sx, y - sy, z + sz), (x - sx, y - sy, z + sz))
        cls.line((x - sx, y - sy, z + sz), (x - sx, y - sy, z - sz))

        # Top face
        cls.line((x - sx, y + sy, z - sz), (x + sx, y + sy, z - sz))
        cls.line((x + sx, y + sy, z - sz), (x + sx, y + sy, z + sz))
        cls.line((x + sx, y + sy, z + sz), (x - sx, y + sy, z + sz))
        cls.line((x - sx, y + sy, z + sz), (x - sx, y + sy, z - sz))

        # Vertical edges
        cls.line((x - sx, y - sy, z - sz), (x - sx, y + sy, z - sz))
        cls.line((x + sx, y - sy, z - sz), (x + sx, y + sy, z - sz))
        cls.line((x + sx, y - sy, z + sz), (x + sx, y + sy, z + sz))
        cls.line((x - sx, y - sy, z + sz), (x - sx, y + sy, z + sz))

    @classmethod
    def axis(cls, length=5):
        cls.line((0, 0, 0), (length, 0, 0))
        cls.line((0, 0, 0), (0, length, 0))
        cls.line((0, 0, 0), (0, 0, length))

    @classmethod
    def grid_2d(cls, size=10, step=1):
        for i in range(-size, size + 1, step):
            cls.line((i, -size, 0), (i, size, 0))
            cls.line((-size, i, 0), (size, i, 0))
