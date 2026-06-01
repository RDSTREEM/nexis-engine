import math
from typing import Literal

import numpy as np

from utils.math_helpers import look_at, normalize, orthographic, perspective

CameraMode = Literal["3d", "2d"]


class EditorCamera:
    """
    Unified editor camera supporting 3D (perspective + orbit/fly) and
    2D (orthographic + pan/zoom) modes.

    3D controls (driven by ViewportWidget):
        Right-drag only          → orbit around target
        Right-hold + WASD/QE     → fly (move camera position)
        Middle-drag              → pan (shift target)
        Scroll                   → dolly zoom
        F                        → focus / reset to origin

    2D controls:
        Middle-drag / Right-drag → pan
        Scroll                   → zoom (changes ortho size)
        F                        → reset to origin
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, console, mode: CameraMode = "3d"):
        self.console = console
        self.mode: CameraMode = mode

        # --- shared state ---
        self.target = np.array([0.0, 0.0, 0.0], dtype="f4")
        self.world_up = np.array([0.0, 1.0, 0.0], dtype="f4")

        # --- 3D state ---
        self.distance = 8.0
        self.yaw = math.radians(45.0)
        self.pitch = math.radians(25.0)

        # --- 2D state ---
        self.ortho_size = 5.0  # half-height in world units
        self.pan_2d = np.array([0.0, 0.0], dtype="f4")  # world offset

        # --- sensitivity ---
        self.ORBIT_SENS = 0.005
        self.PAN_SENS = 0.003
        self.FLY_SPEED = 4.0  # world units per second
        self.ZOOM_SENS = 0.12
        self.ZOOM_2D = 0.10

        # --- cached matrices (updated on demand) ---
        self._view = np.eye(4, dtype="f4")
        self._proj = np.eye(4, dtype="f4")
        self._dirty = True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_mode(self, mode: CameraMode) -> None:
        self.mode = mode
        self._dirty = True
        self.console.info(f"Camera mode → {mode}")

    def get_matrices(self, width: int, height: int):
        """Return (view, proj) as f4 numpy arrays, recomputing if dirty."""
        self._recompute(width, height)
        return self._view, self._proj

    # --- 3D operations ---

    def orbit(self, dx: float, dy: float) -> None:
        self.yaw += dx * self.ORBIT_SENS
        self.pitch -= dy * self.ORBIT_SENS
        self.pitch = max(math.radians(-89.0), min(math.radians(89.0), self.pitch))
        self._dirty = True

    def pan(self, dx: float, dy: float) -> None:
        if self.mode == "2d":
            # 2D pan: just shift the 2D offset directly
            self.pan_2d[0] -= dx * self.ortho_size * self.PAN_SENS * 2
            self.pan_2d[1] += dy * self.ortho_size * self.PAN_SENS * 2
        else:
            eye = self._eye_position()
            forward = normalize(self.target - eye)
            right = normalize(np.cross(forward, self.world_up))
            up = np.cross(right, forward)
            scale = self.distance * self.PAN_SENS
            self.target -= right * dx * scale
            self.target += up * dy * scale
        self._dirty = True

    def zoom(self, delta: float) -> None:
        if self.mode == "2d":
            self.ortho_size *= 1.0 - delta * self.ZOOM_2D
            self.ortho_size = max(0.01, min(10000.0, self.ortho_size))
        else:
            self.distance *= 1.0 - delta * self.ZOOM_SENS
            self.distance = max(0.1, min(10000.0, self.distance))
        self._dirty = True

    def fly(self, pressed_keys: set, delta_time: float) -> None:
        """Called every frame while right mouse button is held in 3D mode."""
        if self.mode != "3d":
            return

        from PySide6.QtCore import Qt

        eye = self._eye_position()
        forward = normalize(self.target - eye)
        # keep fly movement purely horizontal unless Q/E used
        fwd_h = normalize(np.array([forward[0], 0, forward[2]], dtype="f4"))
        right = normalize(np.cross(forward, self.world_up))
        up = self.world_up

        move = np.zeros(3, dtype="f4")
        if Qt.Key_W in pressed_keys:
            move += fwd_h
        if Qt.Key_S in pressed_keys:
            move -= fwd_h
        if Qt.Key_A in pressed_keys:
            move -= right
        if Qt.Key_D in pressed_keys:
            move += right
        if Qt.Key_E in pressed_keys:
            move += up
        if Qt.Key_Q in pressed_keys:
            move -= up

        if np.linalg.norm(move) > 1e-6:
            move = normalize(move) * self.FLY_SPEED * delta_time
            self.target += move
            self._dirty = True

    def focus_reset(self) -> None:
        """F key — reset camera to look at origin."""
        self.target = np.zeros(3, dtype="f4")
        self.pan_2d = np.zeros(2, dtype="f4")
        self.distance = 8.0
        self.yaw = math.radians(45.0)
        self.pitch = math.radians(25.0)
        self.ortho_size = 5.0
        self._dirty = True
        self.console.info("Camera reset to origin.")

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _eye_position(self) -> np.ndarray:
        cp = math.cos(self.cam_pitch if hasattr(self, "cam_pitch") else self.pitch)
        pitch = self.pitch
        cp = math.cos(pitch)
        return self.target + self.distance * np.array(
            [
                cp * math.sin(self.yaw),
                math.sin(pitch),
                cp * math.cos(self.yaw),
            ],
            dtype="f4",
        )

    def _recompute(self, width: int, height: int) -> None:
        if not self._dirty:
            return
        aspect = width / max(1, height)

        if self.mode == "3d":
            eye = self._eye_position()
            self._view = look_at(eye, self.target, self.world_up)
            self._proj = perspective(45.0, aspect, 0.1, 10000.0)

        else:  # 2d
            half_h = self.ortho_size
            half_w = half_h * aspect
            ox, oy = self.pan_2d
            self._view = np.eye(4, dtype="f4")
            # place view camera far above looking down (Z-up 2D plane)
            eye_2d = np.array([ox, oy, 100.0], dtype="f4")
            tgt_2d = np.array([ox, oy, 0.0], dtype="f4")
            up_2d = np.array([0.0, 1.0, 0.0], dtype="f4")
            self._view = look_at(eye_2d, tgt_2d, up_2d)
            self._proj = orthographic(
                ox - half_w,
                ox + half_w,
                oy - half_h,
                oy + half_h,
                -1000.0,
                1000.0,
            )

        self._dirty = False
