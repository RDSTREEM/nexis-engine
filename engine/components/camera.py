import numpy as np
from engine.components.component import Component
from engine.core.component_registry import ComponentRegistry
from engine.utils.math_utils import (
    create_perspective,
    create_orthographic,
    create_rotation_x,
    create_rotation_y,
    create_rotation_z,
)


class Camera(Component):
    def __init__(
        self,
        game_object,
        mode="perspective",
        fov=60,
        near=0.1,
        far=100.0,
        left=0,
        right=800,
        bottom=0,
        top=600,
    ):
        super().__init__(game_object)

        self.mode = mode
        self.fov = fov
        self.near = near
        self.far = far

        # Used only for orthographic
        self.left = left
        self.right = right
        self.bottom = bottom
        self.top = top

    def get_projection_matrix(self, aspect_ratio):
        if self.mode == "perspective":
            return create_perspective(self.fov, aspect_ratio, self.near, self.far)

        elif self.mode == "orthographic":
            return create_orthographic(
                self.left, self.right, self.bottom, self.top, self.near, self.far
            )

    def get_view_matrix(self):
        transform = self.game_object.transform

        position = transform.position
        rotation = transform.rotation

        rx = create_rotation_x(rotation[0])
        ry = create_rotation_y(rotation[1])
        rz = create_rotation_z(rotation[2])

        rotation_matrix = rz @ ry @ rx

        translation = np.identity(4, dtype="f4")
        translation[0:3, 3] = -position

        return rotation_matrix @ translation

    def to_dict(self):
        return {
            "type": "Camera",
            "mode": self.mode,
            "fov": self.fov,
            "near": self.near,
            "far": self.far,
            "left": self.left,
            "right": self.right,
            "bottom": self.bottom,
            "top": self.top,
        }


ComponentRegistry.register("Camera", Camera)
