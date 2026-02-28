class Component:
    def __init__(self, game_object):
        self.game_object = game_object
        self.enabled = True

    def start(self):
        pass

    def update(self):
        pass

    def on_destroy(self):
        pass