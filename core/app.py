from editor.editor import Editor
from renderer.renderer import Renderer
from scenes.scene import SceneManager
from scripting.script_manager import ScriptManager
from ui.main_window import MainWindow
from core.console import EngineConsole


class NEXISApplication:
    def __init__(self):
        self.console = EngineConsole()
        self.scene_manager = SceneManager(self)
        self.renderer = Renderer(self)
        self.script_manager = ScriptManager(self)
        self.editor = Editor(self)
        self.main_window = MainWindow(self)

    def run(self) -> None:
        self.main_window.show()
        self.console.info("NEXIS engine started.")

    def create_project(self, scene_type: str) -> None:
        self.console.info(f"Creating new {scene_type} project...")
        self.scene_manager.create_new_scene(scene_type)
        self.editor.set_project_loaded(True)
        self.main_window.on_project_loaded(scene_type)
        from core.scene import Scene
        from core.mesh_renderer import MeshRenderer

        scene = Scene("Test Scene", "3D")
        cube = scene.create_entity("Cube")
        cube.add_component(MeshRenderer("cube"))
        cube.transform.set_position(0, 0, 0)
        self.active_scene = scene

    def open_project(self, path: str) -> None:
        if not path:
            self.console.warning("Open project cancelled.")
            return
        self.console.info(f"Opening project: {path}")
        self.scene_manager.load_scene(path)
        self.editor.set_project_loaded(True)
        self.main_window.on_project_loaded(self.scene_manager.current_scene_type)

    def close_project(self) -> None:
        self.console.info("Closing current project and returning to the start screen.")
        self.editor.set_project_loaded(False)
        self.scene_manager.current_scene_type = "None"
        self.main_window.show_start_screen()
