import math

import numpy as np
from PySide6.QtCore import Qt


def normalize(v: np.ndarray) -> np.ndarray:
    length = np.linalg.norm(v)
    if length < 1e-6:
        return v
    return v / length


def perspective(
    fov_radians: float, aspect: float, near: float, far: float
) -> np.ndarray:
    f = 1.0 / math.tan(fov_radians / 2.0)
    proj = np.zeros((4, 4), dtype="f4")
    proj[0, 0] = f / aspect
    proj[1, 1] = f
    proj[2, 2] = (far + near) / (near - far)
    proj[3, 2] = (2.0 * far * near) / (near - far)
    proj[2, 3] = -1.0
    return proj


def look_at(eye: np.ndarray, target: np.ndarray, up: np.ndarray) -> np.ndarray:
    forward = normalize(target - eye)
    right = normalize(np.cross(forward, normalize(up)))
    true_up = np.cross(right, forward)

    view = np.eye(4, dtype="f4")
    view[0, :3] = right
    view[1, :3] = true_up
    view[2, :3] = -forward
    view[:3, 3] = -np.dot(view[:3, :3], eye)
    return view


class EditorCamera:
    def __init__(self, console):
        self.console = console
        self.target = np.array([0.0, 0.0, 0.0], dtype="f4")
        self.distance = 6.0
        self.yaw = math.radians(45.0)
        self.pitch = math.radians(25.0)
        self.min_distance = 2.0
        self.max_distance = 30.0
        self.zoom_sensitivity = 0.15
        self.orbit_sensitivity = 0.004
        self.pan_sensitivity = 0.004
        self.current_aspect = 16.0 / 9.0
        self.position = np.array([0.0, 0.0, 0.0], dtype="f4")
        self.up = np.array([0.0, 1.0, 0.0], dtype="f4")
        self.view_matrix = np.eye(4, dtype="f4")
        self.projection_matrix = np.eye(4, dtype="f4")
        self.update_matrices(self.current_aspect)

    def update_matrices(self, aspect: float) -> None:
        self.current_aspect = aspect
        sin_pitch = math.sin(self.pitch)
        cos_pitch = math.cos(self.pitch)
        sin_yaw = math.sin(self.yaw)
        cos_yaw = math.cos(self.yaw)

        self.position = np.array(
            [
                self.target[0] + self.distance * cos_pitch * sin_yaw,
                self.target[1] + self.distance * sin_pitch,
                self.target[2] + self.distance * cos_pitch * cos_yaw,
            ],
            dtype="f4",
        )
        self.view_matrix = look_at(self.position, self.target, self.up)
        self.projection_matrix = perspective(math.radians(45.0), aspect, 0.1, 100.0)

    def orbit(self, delta_x: float, delta_y: float) -> None:
        self.yaw += delta_x * self.orbit_sensitivity
        self.pitch += -delta_y * self.orbit_sensitivity
        self.pitch = max(min(self.pitch, math.radians(89.0)), math.radians(-89.0))
        self.console.info(
            f"Camera orbit updated: yaw={math.degrees(self.yaw):.1f}, pitch={math.degrees(self.pitch):.1f}"
        )
        self.update_matrices(self.current_aspect)

    def pan(self, delta_x: float, delta_y: float) -> None:
        forward = normalize(self.target - self.position)
        right = normalize(np.cross(forward, self.up))
        up = normalize(np.cross(right, forward))
        offset = (
            (-right * delta_x + up * delta_y) * self.pan_sensitivity * self.distance
        )
        self.target += offset
        self.console.info(f"Camera panned by x={delta_x:.1f}, y={delta_y:.1f}")
        self.update_matrices(self.current_aspect)

    def zoom(self, delta: float) -> None:
        self.distance = max(
            self.min_distance,
            min(
                self.max_distance, self.distance * (1.0 - delta * self.zoom_sensitivity)
            ),
        )
        self.console.info(f"Camera zoom updated: distance={self.distance:.2f}")
        self.update_matrices(self.current_aspect)

    def process_keyboard(self, pressed_keys: set[int], delta_time: float) -> None:
        direction = np.zeros(3, dtype="f4")
        forward = normalize(self.target - self.position)
        right = normalize(np.cross(forward, self.up))

        if Qt.Key_W in pressed_keys or Qt.Key_Up in pressed_keys:
            direction += forward
        if Qt.Key_S in pressed_keys or Qt.Key_Down in pressed_keys:
            direction -= forward
        if Qt.Key_A in pressed_keys or Qt.Key_Left in pressed_keys:
            direction -= right
        if Qt.Key_D in pressed_keys or Qt.Key_Right in pressed_keys:
            direction += right

        if np.linalg.norm(direction) > 1e-6:
            direction = normalize(direction)
            travel = direction * delta_time * 4.0
            self.target += travel
            self.console.info(
                f"Camera keyboard move: {travel[0]:.2f}, {travel[1]:.2f}, {travel[2]:.2f}"
            )
            self.update_matrices(self.current_aspect)

    def update(self, pressed_keys: set[int], delta_time: float) -> None:
        self.process_keyboard(pressed_keys, delta_time)
