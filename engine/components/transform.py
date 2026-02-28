import numpy as np
from engine.components.component import Component


class Transform(Component):
    def __init__(self, game_object):
        super().__init__(game_object)

        self.position = np.array([0.0, 0.0, 0.0], dtype="f4")
        self.rotation = np.array([0.0, 0.0, 0.0], dtype="f4")
        self.scale = np.array([1.0, 1.0, 1.0], dtype="f4")