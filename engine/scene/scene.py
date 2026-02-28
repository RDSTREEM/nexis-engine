class Scene:
    def __init__(self, name="New Scene"):
        self.name = name
        self.game_objects = []

    def add_object(self, game_object):
        self.game_objects.append(game_object)

    def update(self):
        for obj in self.game_objects:
            obj.update()