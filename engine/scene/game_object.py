import uuid
import numpy as np
from engine.components.transform import Transform
from engine.core.component_registry import ComponentRegistry


class GameObject:
    def __init__(self, name="GameObject"):
        self.id = str(uuid.uuid4())
        self.name = name
        self.active = True

        self.components = []

        # Every object automatically gets Transform
        self.transform = Transform(self)

    def add_component(self, component_class, *args, **kwargs):
        component = component_class(self, *args, **kwargs)
        self.components.append(component)
        return component

    def get_component(self, component_class):
        for comp in self.components:
            if isinstance(comp, component_class):
                return comp
        return None

    def remove_component(self, component_class):
        for comp in self.components:
            if isinstance(comp, component_class):
                self.components.remove(comp)
                return

    def has_component(self, component_class):
        return self.get_component(component_class) is not None

    def update(self):
        if not self.active:
            return

        for component in self.components:
            if component.enabled:
                component.update()

    def to_dict(self):
        return {
            "name": self.name,
            "transform": self.transform.to_dict(),
            "components": [comp.to_dict() for comp in self.components],
        }

    @staticmethod
    def from_dict(data):
        obj = GameObject(data["name"])

        # Restore transform
        transform_data = data["transform"]
        obj.transform.position = np.array(transform_data["position"], dtype="f4")
        obj.transform.rotation = np.array(transform_data["rotation"], dtype="f4")
        obj.transform.scale = np.array(transform_data["scale"], dtype="f4")

        # Restore components
        for comp_data in data.get("components", []):
            comp_type = comp_data["type"]
            comp_class = ComponentRegistry.get(comp_type)

            if comp_class:
                if comp_type == "MeshRenderer":
                    from engine.core.asset_manager import AssetManager

                    mesh = AssetManager.get_mesh(comp_data["mesh"])
                    material = AssetManager.get_material(comp_data["material"])

                    obj.add_component(
                        comp_class,
                        mesh,
                        material,
                        mesh_name=comp_data["mesh"],
                        material_name=comp_data["material"],
                    )
                else:
                    obj.add_component(comp_class)

        return obj
