import json
import os
from engine.scene.game_object import GameObject


class Scene:
    def __init__(self, name="New Scene"):
        self.name = name
        self.game_objects = []

    def add_object(self, game_object):
        self.game_objects.append(game_object)

    def create_object(self, name="GameObject"):
        obj = GameObject(name)
        self.game_objects.append(obj)
        return obj

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
