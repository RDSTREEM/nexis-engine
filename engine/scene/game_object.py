import uuid
import numpy as np
from engine.components.transform import Transform


class GameObject:
    def __init__(self, name="GameObject"):
        self.id = str(uuid.uuid4())
        self.name = name
        self.active = True

        self.components = []

        # Every object automatically gets Transform
        self.transform = Transform(self)
        self.components.append(self.transform)

    def add_component(self, component_class, *args, **kwargs):
        component = component_class(self, *args, **kwargs)
        self.components.append(component)
        return component

    def get_component(self, component_class):
        for comp in self.components:
            if isinstance(comp, component_class):
                return comp
        return None

    def update(self):
        if not self.active:
            return

        for component in self.components:
            if component.enabled:
                component.update()

    def to_dict(self):
        return {
            "name": self.name,
            "transform": self.transform.to_dict()
        }

    @staticmethod
    def from_dict(data):
        obj = GameObject(data["name"])

        transform_data = data["transform"]

        obj.transform.position = np.array(transform_data["position"], dtype=float)
        obj.transform.rotation = np.array(transform_data["rotation"], dtype=float)
        obj.transform.scale = np.array(transform_data["scale"], dtype=float)

        return obj