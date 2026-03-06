import numpy as np
from engine.components.component import Component
from engine.utils.math_utils import (
    create_translation,
    create_scale,
    create_rotation_x,
    create_rotation_y,
    create_rotation_z
)


class Transform(Component):
    def __init__(self, game_object):
        super().__init__(game_object)

        self.position = np.array([0.0, 0.0, 0.0], dtype="f4")
        self.rotation = np.array([0.0, 0.0, 0.0], dtype="f4")
        self.scale = np.array([1.0, 1.0, 1.0], dtype="f4")
    
    def get_model_matrix(self):
        translation = create_translation(self.position)
        scale = create_scale(self.scale)

        rx = create_rotation_x(self.rotation[0])
        ry = create_rotation_y(self.rotation[1])
        rz = create_rotation_z(self.rotation[2])
        
        rotation = rx @ ry @ rz

        return translation @ rotation @ scale

    def to_dict(self):
        return {
            "position": self.position.tolist(),
            "rotation": self.rotation.tolist(),
            "scale": self.scale.tolist()
        }
    
    @staticmethod
    def from_dict(game_object, data):
        t = Transform(game_object)
        t.position = np.array(data["position"], dtype="f4")
        t.rotation= np.array(data["rotation"], dtype="f4")
        t.scale = np.array(data["scale"], dtype="f4")
        
        return t