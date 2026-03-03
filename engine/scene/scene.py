import json
from engine.scene.game_object import GameObject

class Scene:
    def __init__(self, name="New Scene"):
        self.name = name
        self.game_objects = []

    def add_object(self, game_object):
        self.game_objects.append(game_object)

    def update(self):
        for obj in self.game_objects:
            obj.update()
    def save(self, path):
        data = {
            "game_objects": [obj.to_dict() for obj in self.game_objects]
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=4)


    def load(self, path):
        with open(path, "r") as f:
            data = json.load(f)

        self.game_objects.clear()

        for obj_data in data["game_objects"]:
            obj = GameObject.from_dict(obj_data)
            self.add_game_object(obj)