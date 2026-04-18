import numpy as np
from engine.utils.math_utils import screen_point_to_ray


class ObjectPicker:
    def __init__(self, engine):
        self.engine = engine

    def pick_object(self, scene, camera, mouse_screen_pos, radius=0.75):
        origin, direction = screen_point_to_ray(
            mouse_screen_pos, camera, self.engine.width, self.engine.height
        )

        closest = None
        closest_t = float("inf")

        for obj in scene.game_objects:
            center = obj.transform.position
            oc = origin - center
            b = np.dot(oc, direction)
            c = np.dot(oc, oc) - radius * radius
            discriminant = b * b - c
            if discriminant < 0:
                continue
            t = -b - np.sqrt(discriminant)
            if 0 < t < closest_t:
                closest_t = t
                closest = obj

        return closest
