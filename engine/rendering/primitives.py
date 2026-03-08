import numpy as np
from engine.rendering.mesh import Mesh


def create_cube(ctx):
    vertices = np.array(
        [
            # front
            [-0.5, -0.5, 0.5],
            [0.5, -0.5, 0.5],
            [0.5, 0.5, 0.5],
            [-0.5, 0.5, 0.5],
            # back
            [-0.5, -0.5, -0.5],
            [0.5, -0.5, -0.5],
            [0.5, 0.5, -0.5],
            [-0.5, 0.5, -0.5],
        ],
        dtype="f4",
    ).flatten()

    indices = np.array(
        [
            [0, 1, 2, 2, 3, 0],  # front
            [1, 5, 6, 6, 2, 1],  # right
            [5, 4, 7, 7, 6, 5],  # back
            [4, 0, 3, 3, 7, 4],  # left
            [3, 2, 6, 6, 7, 3],  # top
            [4, 5, 1, 1, 0, 4],  # bottom
        ]
    ).flatten()

    mesh = Mesh(ctx, vertices, indices)
    return mesh


def create_plane(ctx):
    vertices = np.array(
        [
            [-1, 0, -1],
            [1, 0, -1],
            [1, 0, 1],
            [-1, 0, 1],
        ],
        dtype="f4",
    ).flatten()

    indices = np.array(
        [
            [0, 1, 2],
            [2, 3, 0],
        ]
    ).flatten()

    mesh = Mesh(ctx, vertices, indices)
    return mesh


def create_quad(ctx):
    import numpy as np
    from engine.rendering.mesh import Mesh

    vertices = np.array(
        [
            [-0.5, -0.5, 0],
            [0.5, -0.5, 0],
            [0.5, 0.5, 0],
            [-0.5, 0.5, 0],
        ],
        dtype="f4",
    ).flatten()

    indices = np.array(
        [
            [0, 1, 2],
            [2, 3, 0],
        ],
        dtype="i4",
    ).flatten()

    return Mesh(ctx, vertices, indices)
