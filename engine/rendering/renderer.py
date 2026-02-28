import moderngl
from engine.components.mesh_renderer import MeshRenderer


class Renderer:
    def __init__(self):
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST)

    def render(self, scene):
        self.ctx.clear(0.1, 0.1, 0.1)

        for obj in scene.game_objects:
            for comp in obj.components:
                if isinstance(comp, MeshRenderer):
                    comp.render()