class SceneManager:
    def __init__(self):
        self.current_scene = None

    def load_scene(self, scene):
        self.current_scene = scene

    def update(self):
        if self.current_scene:
            self.current_scene.update()