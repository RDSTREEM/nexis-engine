import numpy as np
from engine.components.component import Component
from engine.utils.math_utils import (
    create_perspective,
    create_orthographic
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
        top=600
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
            return create_perspective(
                self.fov,
                aspect_ratio,
                self.near,
                self.far
            )

        elif self.mode == "orthographic":
            return create_orthographic(
                self.left,
                self.right,
                self.bottom,
                self.top,
                self.near,
                self.far
            )

    def get_view_matrix(self):
        position = self.game_object.transform.position

        view = np.identity(4, dtype="f4")
        view[0:3, 3] = -position[0:3]

        return view