from __future__ import annotations

import math
import numpy as np

from core.component import Component


def _rotation_matrix(rx: float, ry: float, rz: float) -> np.ndarray:
    """Euler angles in degrees → 4x4 rotation matrix (YXZ order)."""
    rx = math.radians(rx)
    ry = math.radians(ry)
    rz = math.radians(rz)

    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)

    # Y * X * Z
    Ry = np.array(
        [[cy, 0, sy, 0], [0, 1, 0, 0], [-sy, 0, cy, 0], [0, 0, 0, 1]], dtype="f4"
    )
    Rx = np.array(
        [[1, 0, 0, 0], [0, cx, -sx, 0], [0, sx, cx, 0], [0, 0, 0, 1]], dtype="f4"
    )
    Rz = np.array(
        [[cz, -sz, 0, 0], [sz, cz, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], dtype="f4"
    )
    return Ry @ Rx @ Rz


class Transform(Component):
    """
    Every Entity has exactly one Transform.
    Stores position / rotation (Euler degrees) / scale and builds the model matrix.
    """

    def __init__(
        self,
        position: tuple = (0.0, 0.0, 0.0),
        rotation: tuple = (0.0, 0.0, 0.0),
        scale: tuple = (1.0, 1.0, 1.0),
    ):
        super().__init__()
        self.position = np.array(position, dtype="f4")
        self.rotation = np.array(rotation, dtype="f4")  # Euler degrees XYZ
        self.scale = np.array(scale, dtype="f4")
        self._matrix: np.ndarray = np.eye(4, dtype="f4")
        self._dirty: bool = True

    # ------------------------------------------------------------------

    def set_position(self, x: float, y: float, z: float) -> None:
        self.position[:] = (x, y, z)
        self._dirty = True

    def set_rotation(self, x: float, y: float, z: float) -> None:
        self.rotation[:] = (x, y, z)
        self._dirty = True

    def set_scale(self, x: float, y: float, z: float) -> None:
        self.scale[:] = (x, y, z)
        self._dirty = True

    def translate(self, dx: float, dy: float, dz: float) -> None:
        self.position += np.array([dx, dy, dz], dtype="f4")
        self._dirty = True

    def rotate(self, dx: float, dy: float, dz: float) -> None:
        self.rotation += np.array([dx, dy, dz], dtype="f4")
        self._dirty = True

    @property
    def matrix(self) -> np.ndarray:
        if self._dirty:
            self._recompute()
        return self._matrix

    def _recompute(self) -> None:
        T = np.eye(4, dtype="f4")
        T[:3, 3] = self.position

        R = _rotation_matrix(*self.rotation)

        S = np.eye(4, dtype="f4")
        S[0, 0] = self.scale[0]
        S[1, 1] = self.scale[1]
        S[2, 2] = self.scale[2]

        self._matrix = T @ R @ S
        self._dirty = False

    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update(
            {
                "position": self.position.tolist(),
                "rotation": self.rotation.tolist(),
                "scale": self.scale.tolist(),
            }
        )
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Transform":
        t = cls(
            position=data.get("position", [0, 0, 0]),
            rotation=data.get("rotation", [0, 0, 0]),
            scale=data.get("scale", [1, 1, 1]),
        )
        t.enabled = data.get("enabled", True)
        return t
