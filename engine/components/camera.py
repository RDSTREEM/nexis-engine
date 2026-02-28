import numpy as np
from engine.components.component import Component
from engine.utils.math_utils import create_perspective


class Camera(Component):
    def __init__(self, game_object, fov=60, near=0.1, far=100.0):
        super().__init__(game_object)

        self.fov = fov
        self.near = near
        self.far = far

    def get_projection_matrix(self, aspect_ratio):
        return create_perspective(
            self.fov,
            aspect_ratio,
            self.near,
            self.far
        )

    def get_view_matrix(self):
        position = self.game_object.transform.position

        view = np.identity(4, dtype="f4")
        view[0:3, 3] = -position[0:3]

        return view