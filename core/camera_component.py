from __future__ import annotations

import numpy as np
from typing import Literal

from core.component import Component
from utils.math_helpers import look_at, perspective, orthographic

ProjectionType = Literal["perspective", "orthographic"]


class CameraComponent(Component):
    """
    Makes an Entity act as a camera during play mode.
    The scene's active camera is the first enabled CameraComponent found.

    In play mode the viewport renders from this entity's Transform position/rotation.
    """

    def __init__(
        self,
        projection: ProjectionType = "perspective",
        fov: float = 45.0,
        near: float = 0.1,
        far: float = 1000.0,
        ortho_size: float = 5.0,
        is_main: bool = True,
    ):
        super().__init__()
        self.projection: ProjectionType = projection
        self.fov: float = fov
        self.near: float = near
        self.far: float = far
        self.ortho_size: float = ortho_size
        self.is_main: bool = is_main  # hint: use this as play-mode cam
        self.clear_color: np.ndarray = np.array([0.1, 0.12, 0.18, 1.0], dtype="f4")

    # ------------------------------------------------------------------

    def get_view_matrix(self) -> np.ndarray:
        """Compute view matrix from the entity's Transform."""
        if self.entity is None:
            return np.eye(4, dtype="f4")

        transform = self.entity.transform
        pos = transform.position.copy()

        # derive forward from rotation (simplified: use -Z as forward rotated by euler)
        import math

        rx = math.radians(transform.rotation[0])
        ry = math.radians(transform.rotation[1])

        forward = np.array(
            [
                math.cos(rx) * math.sin(ry),
                -math.sin(rx),
                math.cos(rx) * math.cos(ry),
            ],
            dtype="f4",
        )

        target = pos + forward
        up = np.array([0.0, 1.0, 0.0], dtype="f4")
        return look_at(pos, target, up)

    def get_projection_matrix(self, width: int, height: int) -> np.ndarray:
        aspect = width / max(1, height)
        if self.projection == "perspective":
            return perspective(self.fov, aspect, self.near, self.far)
        else:
            h = self.ortho_size
            w = h * aspect
            return orthographic(-w, w, -h, h, self.near, self.far)

    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update(
            {
                "projection": self.projection,
                "fov": self.fov,
                "near": self.near,
                "far": self.far,
                "ortho_size": self.ortho_size,
                "is_main": self.is_main,
                "clear_color": self.clear_color.tolist(),
            }
        )
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "CameraComponent":
        c = cls(
            projection=data.get("projection", "perspective"),
            fov=data.get("fov", 45.0),
            near=data.get("near", 0.1),
            far=data.get("far", 1000.0),
            ortho_size=data.get("ortho_size", 5.0),
            is_main=data.get("is_main", True),
        )
        c.enabled = data.get("enabled", True)
        c.clear_color = np.array(
            data.get("clear_color", [0.1, 0.12, 0.18, 1.0]), dtype="f4"
        )
        return c
