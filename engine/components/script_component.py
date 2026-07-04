import os
from engine.components.component import Component
from engine.core.component_registry import ComponentRegistry


class ScriptComponent(Component):
    def __init__(self, game_object, script_path=None, script_code=None):
        super().__init__(game_object)
        self.script_path = script_path
        self.script_code = script_code
        self._globals = {
            "game_object": self.game_object,
            "transform": self.game_object.transform,
            "Input": __import__("engine.core.input", fromlist=["Input"]).Input,
            "Time": __import__("engine.core.time", fromlist=["Time"]).Time,
            "SceneManager": __import__(
                "engine.scene.scene_manager", fromlist=["SceneManager"]
            ).SceneManager,
        }
        self._locals = {}
        self._loaded = False

        self.load_script()

    def load_script(self):
        if self.script_path and os.path.isfile(self.script_path):
            with open(self.script_path, "r", encoding="utf-8") as f:
                code = f.read()
        elif self.script_code:
            code = self.script_code
        else:
            code = ""

        if code:
            try:
                exec(
                    compile(code, self.script_path or "<script>", "exec"),
                    self._globals,
                    self._locals,
                )
                self._loaded = True
            except Exception as e:
                print(
                    f"[ScriptComponent] Error loading script {self.script_path or '<inline>'}: {e}"
                )

    def start(self):
        if not self._loaded:
            return
        on_start = self._locals.get("on_start") or self._globals.get("on_start")
        if callable(on_start):
            try:
                on_start()
            except Exception as e:
                print(
                    f"[ScriptComponent] on_start error in {self.script_path or '<inline>'}: {e}"
                )

    def update(self):
        if not self._loaded:
            return
        on_update = self._locals.get("on_update") or self._globals.get("on_update")
        if callable(on_update):
            try:
                on_update()
            except Exception as e:
                print(
                    f"[ScriptComponent] on_update error in {self.script_path or '<inline>'}: {e}"
                )

    def to_dict(self):
        return {
            "type": "ScriptComponent",
            "script_path": self.script_path,
            "script_code": self.script_code,
        }


ComponentRegistry.register("ScriptComponent", ScriptComponent)
