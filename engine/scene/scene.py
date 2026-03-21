import json
import os
from engine.scene.game_object import GameObject
from engine.components.camera import Camera


class Scene:
    def __init__(self, name="New Scene"):
        self.name = name
        self.game_objects = []
        self.active_camera = None
        self.selected_object = None

    def add_object(self, game_object):
        self.game_objects.append(game_object)

    def create_object(self, name="GameObject"):
        obj = GameObject(name)
        self.game_objects.append(obj)
        return obj

    def place_object(self, position, mesh_name="cube", material_name="default_blue"):
        from engine.components.mesh_renderer import MeshRenderer
        from engine.core.asset_manager import AssetManager

        mesh = AssetManager.get_mesh(mesh_name)
        material = AssetManager.get_material(material_name)

        if mesh is None or material is None:
            return None

        count = len(self.game_objects)
        obj = self.create_object(f"Placed_{mesh_name}_{count}")
        obj.transform.position = position
        obj.transform.rotation = [0.0, 0.0, 0.0]
        obj.transform.scale = [1.0, 1.0, 1.0]

        obj.add_component(
            MeshRenderer,
            mesh,
            material,
            mesh_name=mesh_name,
            material_name=material_name,
        )

        return obj

    def set_active_camera(self, camera):
        self.active_camera = camera

    def get_active_camera(self):
        return self.active_camera

    def get_selected_object(self):
        return self.selected_object

    def set_selected_object(self, obj):
        self.selected_object = obj

    def remove_object(self, obj):
        if obj in self.game_objects:
            self.game_objects.remove(obj)

    def find(self, name):
        for obj in self.game_objects:
            if obj.name == name:
                return obj
        return None

    def get_components(self, component_type):
        for obj in self.game_objects:
            comp = obj.get_component(component_type)
            if comp:
                yield comp

    def clear(self):
        self.game_objects.clear()

    def update(self):
        for obj in self.game_objects:
            obj.update()

    def save(self, path):
        directory = os.path.dirname(path)

        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        data = {"game_objects": [obj.to_dict() for obj in self.game_objects]}
        with open(path, "w") as f:
            json.dump(data, f, indent=4)

    def load(self, path):
        with open(path, "r") as f:
            data = json.load(f)

        self.game_objects.clear()

        for obj_data in data["game_objects"]:
            obj = GameObject.from_dict(obj_data)
            self.add_object(obj)

        self.name = os.path.basename(path)
        main_camera = self.find("Main Camera")
        if main_camera and main_camera.has_component(Camera):
            self.set_active_camera(main_camera.get_component(Camera))
        else:
            # Fallback to first camera found
            for cam in self.get_components(Camera):
                self.set_active_camera(cam)
                break
