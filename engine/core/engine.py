import pygame
import numpy as np

from engine.core.time import Time
from engine.core.logger import setup_logger
from engine.core.asset_manager import AssetManager
from engine.core.input import Input

from engine.rendering.renderer import Renderer
from engine.rendering.material import Material
from engine.rendering.mesh import Mesh
from engine.rendering.shader import Shader
from engine.rendering.primitives import create_cube, create_plane, create_quad

from engine.scene.scene_manager import SceneManager
from engine.scene.scene import Scene

from editor.core.editor import Editor

# ImGui integration
from imgui_bundle import imgui
from engine.editor.imgui_renderer import ModernGLImGuiRenderer
from engine.editor.imgui_layer import ImGuiLayer


class Engine:
    def __init__(self, width=1280, height=720, title="Nexis Engine"):
        self.width = width
        self.height = height
        self.title = title
        self.running = False

        self.logger = setup_logger()

        # ImGui components
        self.imgui = None
        self.imgui_renderer = None
        self.imgui_layer = None

    def initialize(self):
        pygame.init()
        pygame.display.set_caption(self.title)

        self.window = pygame.display.set_mode(
            (self.width, self.height), pygame.OPENGL | pygame.DOUBLEBUF
        )

        self.clock = pygame.time.Clock()

        self.logger.info("Engine initialized.")

        self.renderer = Renderer()
        self.scene_manager = SceneManager()

        # Setup ImGui with ModernGL renderer
        # try:
        imgui.create_context()
        self.imgui = imgui
        self.imgui_renderer = ModernGLImGuiRenderer(self.renderer.ctx)
        self.imgui_layer = ImGuiLayer(self)
        self.imgui_layer.initialize()
        self.logger.info("ImGui initialized with ModernGL renderer")
        # except Exception as e:
        #     self.logger.warning(f"ImGui unavailable: {e}")
        #     self.imgui = None
        #     self.imgui_renderer = None
        #     self.imgui_layer = None

        scene = Scene("Main Scene")

        shader = Shader(
            self.renderer.ctx,
            "./engine/shaders/basic.vert",
            "./engine/shaders/basic.frag",
        )
        vertices = np.array(
            [
                [-0.6, -0.4, 0.0],
                [0.6, -0.4, 0.0],
                [0.0, 0.6, 0.0],
            ]
        )

        mesh = Mesh(self.renderer.ctx, vertices)
        cube_mesh = create_cube(self.renderer.ctx)
        plane_mesh = create_plane(self.renderer.ctx)
        quad_mesh = create_quad(self.renderer.ctx)

        blue_material = Material(shader, (0.2, 0.6, 1.0, 1.0))
        red_material = Material(shader, (1.0, 0.2, 0.2, 1.0))
        green_material = Material(shader, (0.2, 1.0, 0.2, 1.0))

        AssetManager.register_mesh("cube", cube_mesh)
        AssetManager.register_mesh("plane", plane_mesh)
        AssetManager.register_mesh("quad", quad_mesh)
        AssetManager.register_mesh("triangle", mesh)
        AssetManager.register_material("default_blue", blue_material)
        AssetManager.register_material("default_red", red_material)
        AssetManager.register_material("default_green", green_material)

        scene.load("./assets/scenes/cubes.scene")
        self.scene_manager.load_scene(scene)

        # Initialize editor
        self.editor = Editor(self)
        camera = scene.get_active_camera()
        if camera:
            self.editor.initialize(camera)

    def run(self):
        self.running = True
        self.logger.info("Engine started.")

        while self.running:

            Time.update()

            self.handle_events()
            Input.update()
            self.update()
            self.render()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        self.logger.info("Engine stopped.")

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # Forward events to Input system
            Input.process_event(event)

            # Forward events to ImGui
            if self.imgui_layer is not None:
                self.imgui_layer.process_event(event)

    def update(self):
        # Update editor (handles camera controls, object picking, etc.)
        self.editor.update()

        self.scene_manager.update()

    def render(self):
        # Render 3D scene first (ModernGL)
        if self.scene_manager.current_scene:
            self.renderer.render(self.scene_manager.current_scene)

        # Render ImGui UI on top
        if self.imgui_layer is not None and self.imgui_renderer is not None:
            # Begin ImGui frame
            self.imgui_layer.begin_frame()

            # Render editor UI (this will call imgui functions)
            self.editor.render_ui()

            # End ImGui frame and render
            draw_data = self.imgui_layer.end_frame()
            self.imgui_renderer.render(draw_data)
