import importlib.util
import sys
from engine.components.component import Component


class ScriptComponent(Component):
    def __init__(self, game_object, script_path):
        super().__init__(game_object)

        self.script_path = script_path
        self.script_instance = None

        self.load_script()

    def load_script(self):
        spec = importlib.util.spec_from_file_location(
            "user_script", self.script_path
        )

        module = importlib.util.module_from_spec(spec)
        sys.modules["user_script"] = module
        spec.loader.exec_module(module)

        # Expect user script to define class Script
        self.script_instance = module.Script()

        # Inject engine references
        self.script_instance.game_object = self.game_object
        self.script_instance.transform = self.game_object.transform

        from engine.core.time import Time
        from engine.core.input import Input

        self.script_instance.Time = Time
        self.script_instance.Input = Input

        if hasattr(self.script_instance, "start"):
            self.script_instance.start()

    def update(self):
        if self.script_instance and hasattr(self.script_instance, "update"):
            self.script_instance.update()