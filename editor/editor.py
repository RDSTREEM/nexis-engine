class Editor:
    def __init__(self, app):
        self.app = app
        self.project_loaded = False

    def set_project_loaded(self, loaded: bool) -> None:
        self.project_loaded = loaded

    def is_project_loaded(self) -> bool:
        return self.project_loaded
