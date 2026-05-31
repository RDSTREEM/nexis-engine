class ScriptManager:
    def __init__(self, app):
        self.app = app
        self.app.console.info("Scripting subsystem initialized.")

    def execute_startup_scripts(self) -> None:
        self.app.console.info("Executing startup scripts...")
