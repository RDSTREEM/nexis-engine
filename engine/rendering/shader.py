class Shader:
    def __init__(self, ctx, vert_path, frag_path):
        with open(vert_path) as f:
            vertex_src = f.read()

        with open(frag_path) as f:
            fragment_src = f.read()

        self.program = ctx.program(
            vertex_shader=vertex_src, fragment_shader=fragment_src
        )

    def set_uniform_matrix(self, name, matrix):
        self.program[name].write(matrix.T.astype("f4").tobytes())
