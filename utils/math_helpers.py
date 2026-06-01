import math
import numpy as np


def normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v if n < 1e-8 else v / n


def look_at(eye: np.ndarray, target: np.ndarray, up: np.ndarray) -> np.ndarray:
    eye = np.array(eye, dtype="f4")
    target = np.array(target, dtype="f4")
    up = np.array(up, dtype="f4")
    f = normalize(target - eye)
    r = normalize(np.cross(f, up))
    u = np.cross(r, f)
    m = np.eye(4, dtype="f4")
    m[0, :3] = r
    m[1, :3] = u
    m[2, :3] = -f
    m[:3, 3] = [-np.dot(r, eye), -np.dot(u, eye), np.dot(f, eye)]
    return m


def perspective(fov_deg: float, aspect: float, near: float, far: float) -> np.ndarray:
    f = 1.0 / math.tan(math.radians(fov_deg) / 2)
    m = np.zeros((4, 4), dtype="f4")
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = (2 * far * near) / (near - far)
    m[3, 2] = -1.0
    return m


def orthographic(
    left: float, right: float, bottom: float, top: float, near: float, far: float
) -> np.ndarray:
    m = np.zeros((4, 4), dtype="f4")
    m[0, 0] = 2.0 / (right - left)
    m[1, 1] = 2.0 / (top - bottom)
    m[2, 2] = -2.0 / (far - near)
    m[0, 3] = -(right + left) / (right - left)
    m[1, 3] = -(top + bottom) / (top - bottom)
    m[2, 3] = -(far + near) / (far - near)
    m[3, 3] = 1.0
    return m
