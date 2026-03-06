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


def create_orthographic(left, right, bottom, top, near, far):
    mat = np.identity(4, dtype="f4")

    mat[0][0] = 2.0 / (right - left)
    mat[1][1] = 2.0 / (top - bottom)
    mat[2][2] = -2.0 / (far - near)

    mat[0][3] = -(right + left) / (right - left)
    mat[1][3] = -(top + bottom) / (top - bottom)
    mat[2][3] = -(far + near) / (far - near)

    return mat


def create_rotation_x(angle):
    rad = np.radians(angle)
    c = np.cos(rad)
    s = np.sin(rad)

    mat = np.identity(4, dtype="f4")
    mat[1][1] = c
    mat[1][2] = -s
    mat[2][1] = s
    mat[2][2] = c
    return mat


def create_rotation_y(angle):
    rad = np.radians(angle)
    c = np.cos(rad)
    s = np.sin(rad)

    mat = np.identity(4, dtype="f4")
    mat[0][0] = c
    mat[0][2] = s
    mat[2][0] = -s
    mat[2][2] = c
    return mat


def create_rotation_z(angle):
    rad = np.radians(angle)
    c = np.cos(rad)
    s = np.sin(rad)

    mat = np.identity(4, dtype="f4")
    mat[0][0] = c
    mat[0][1] = -s
    mat[1][0] = s
    mat[1][1] = c
    return mat
