class SceneManager:
    def __init__(self, app):
        self.app = app
        self.current_scene_type = "None"
        self.current_project_path = ""

    def create_new_scene(self, scene_type: str) -> None:
        self.current_scene_type = scene_type
        self.current_project_path = ""
        self.app.console.info(f"Initialized a new {scene_type} scene.")

    def load_scene(self, path: str) -> None:
        self.current_project_path = path
        if path.lower().endswith(".3d"):
            self.current_scene_type = "3D"
        elif path.lower().endswith(".2d"):
            self.current_scene_type = "2D"
        else:
            self.current_scene_type = "Unknown"
        self.app.console.info(
            f"Scene loaded from {path}. Detected type: {self.current_scene_type}."
        )
