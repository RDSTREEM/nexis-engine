import pygame
import numpy as np
from engine.core.time import Time
from engine.core.logger import setup_logger
from engine.core.asset_manager import AssetManager
from engine.rendering.renderer import Renderer
from engine.rendering.material import Material
from engine.rendering.mesh import Mesh
from engine.rendering.shader import Shader
from engine.scene.scene_manager import SceneManager
from engine.scene.scene import Scene
from engine.scene.game_object import GameObject
from engine.components.mesh_renderer import MeshRenderer
from engine.components.camera import Camera
from engine.core.input import Input
from engine.rendering.primitives import create_cube, create_plane


class Engine:
    def __init__(self, width=1280, height=720, title="Nexis Engine"):
        self.width = width
        self.height = height
        self.title = title
        self.running = False

        self.logger = setup_logger()

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

        scene = Scene("Main Scene")

        vertex_shader = """
        #version 330
        uniform mat4 mvp;
        in vec3 in_position;

        void main() {
            gl_Position = mvp * vec4(in_position, 1.0);
        }
        """

        fragment_shader = """
        #version 330
        out vec4 fragColor;

        void main() {
            fragColor = vec4(0.2, 0.6, 1.0, 1.0);
        }
        """

        shader = Shader(self.renderer.ctx, vertex_shader, fragment_shader)
        vertices = np.array(
            [
                -0.6,
                -0.4,
                0.0,
                0.6,
                -0.4,
                0.0,
                0.0,
                0.6,
                0.0,
            ]
        )

        mesh = Mesh(self.renderer.ctx, vertices)
        mesh.build_vao(shader)

        cube_mesh = create_cube(self.renderer.ctx)
        cube_mesh.build_vao(shader)

        plane_mesh = create_plane(self.renderer.ctx)
        plane_mesh.build_vao(shader)
        material = Material(shader)

        AssetManager.register_mesh("cube", cube_mesh)
        AssetManager.register_mesh("plane", plane_mesh)
        AssetManager.register_mesh("triangle", mesh)
        AssetManager.register_material("default_blue", material)

        for i in range(5):
            cube = GameObject(f"Cube_{i}")

            cube.transform.position[0] = i * 2

            cube.add_component(
                MeshRenderer,
                AssetManager.get_mesh("cube"),
                AssetManager.get_material("default_blue"),
                mesh_name="cube",
                material_name="default_blue",
            )

            scene.add_object(cube)

        camera = GameObject("Main Camera")
        camera.add_component(Camera)

        scene.add_object(camera)
        # scene.load("./assets/scenes/test.scene")
        self.scene_manager.load_scene(scene)

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

    def update(self):
        self.scene_manager.update()

        scene = self.scene_manager.current_scene
        if scene:
            for obj in scene.game_objects:
                if obj.name == "Main Camera":
                    speed = 3.0 * Time.delta_time

                    if Input.get_key(pygame.K_w):
                        obj.transform.position[2] -= speed

                    if Input.get_key(pygame.K_s):
                        obj.transform.position[2] += speed

                    if Input.get_key(pygame.K_a):
                        obj.transform.position[0] -= speed

                    if Input.get_key(pygame.K_d):
                        obj.transform.position[0] += speed

    def render(self):
        if self.scene_manager.current_scene:
            self.renderer.render(self.scene_manager.current_scene)
