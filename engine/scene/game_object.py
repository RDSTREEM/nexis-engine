import uuid
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

    def add_component(self, component_class):
        component = component_class(self)
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