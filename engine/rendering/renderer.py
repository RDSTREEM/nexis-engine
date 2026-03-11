import moderngl
from engine.components.mesh_renderer import MeshRenderer
from engine.rendering.shader import Shader
from engine.rendering.debug_rendering import DebugDraw


class Renderer:
    def __init__(self):
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST)

        self.shader = Shader(
            self.ctx,
            "./engine/shaders/basic.vert",
            "./engine/shaders/basic.frag",
        )

        DebugDraw.init(self.ctx)

    def render(self, scene):
        self.ctx.clear(0.1, 0.1, 0.1)
        self.render_scene(scene)
        self.render_debug(scene)

    def render_scene(self, scene):
        camera = scene.get_active_camera()
        if camera is None:
            return

        aspect = self.ctx.screen.width / self.ctx.screen.height
        projection = camera.get_projection_matrix(aspect)
        view = camera.get_view_matrix()

        for renderer in scene.get_components(MeshRenderer):
            obj = renderer.game_object
            model = obj.transform.get_model_matrix()
            mvp = projection @ view @ model
            renderer.render(mvp)

    def render_debug(self, scene):
        camera = scene.get_active_camera()
        if camera is None:
            return

        aspect = self.ctx.screen.width / self.ctx.screen.height
        projection = camera.get_projection_matrix(aspect)
        view = camera.get_view_matrix()

        DebugDraw.clear()

        DebugDraw.grid()
        DebugDraw.axis()

        DebugDraw.render(self.shader, projection, view)
