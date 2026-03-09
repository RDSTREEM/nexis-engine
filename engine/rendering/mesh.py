class Mesh:
    def __init__(self, ctx, vertices, indices=None):
        self.ctx = ctx

        self.vbo = ctx.buffer(vertices.astype("f4").tobytes())

        self.ibo = None
        if indices is not None:
            self.ibo = ctx.buffer(indices.astype("i4").tobytes())

    def build_vao(self, program):
        if self.ibo:
            return self.ctx.vertex_array(
                program,
                [
                    (
                        self.vbo,
                        "3f",
                        "in_position",
                    )
                ],
                self.ibo,
            )

        return self.ctx.simple_vertex_array(
            program,
            self.vbo,
            "in_position",
        )

    def render(self):
        if not self.vao:
            return

        if self.ibo:
            self.vao.render()
        else:
            self.vao.render()
