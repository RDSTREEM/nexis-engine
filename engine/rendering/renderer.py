import moderngl
from engine.components.mesh_renderer import MeshRenderer
from engine.components.camera import Camera
from engine.rendering.debug_rendering import DebugRenderer
from engine.rendering.debug_shapes import draw_grid, draw_axis
from engine.rendering.debug_shapes import draw_grid, draw_axis


class Renderer:
    def __init__(self):
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST)

    def render(self, scene):
        self.ctx.clear(0.1, 0.1, 0.1)
        self.render_scene(scene)
        self.render_debug()

    def render_scene(self, scene):
        camera = None
        for obj in scene.game_objects:
            for comp in obj.components:
                if isinstance(comp, Camera):
                    camera = comp

        if camera is None:
            return

        aspect = self.ctx.screen.width / self.ctx.screen.height
        projection = camera.get_projection_matrix(aspect)
        view = camera.get_view_matrix()

        for obj in scene.game_objects:
            model = obj.transform.get_model_matrix()

            for comp in obj.components:
                if isinstance(comp, MeshRenderer):
                    mvp = projection @ view @ model
                    comp.render(mvp)

    def render_debug(self):
        self.debug_renderer.clear()

        draw_grid(self.debug_renderer)
        draw_axis(self.debug_renderer)

        self.debug_renderer.render(self.shader)
