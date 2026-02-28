import numpy as np


def create_translation(position):
    mat = np.identity(4, dtype="f4")
    mat[0:3, 3] = position[0:3]
    return mat


def create_scale(scale):
    mat = np.identity(4, dtype="f4")
    mat[0][0] = scale[0]
    mat[1][1] = scale[1]
    mat[2][2] = scale[2]
    return mat


def create_perspective(fov, aspect, near, far):
    f = 1.0 / np.tan(np.radians(fov) / 2)
    mat = np.zeros((4, 4), dtype="f4")

    mat[0][0] = f / aspect
    mat[1][1] = f
    mat[2][2] = (far + near) / (near - far)
    mat[2][3] = (2 * far * near) / (near - far)
    mat[3][2] = -1

    return mat