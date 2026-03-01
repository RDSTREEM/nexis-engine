import pygame
from engine.core.time import Time
from engine.core.logger import setup_logger
from engine.rendering.renderer import Renderer
from engine.scene.scene_manager import SceneManager
from engine.scene.scene import Scene
from engine.scene.game_object import GameObject
from engine.components.mesh_renderer import MeshRenderer
from engine.components.camera import Camera
from engine.core.input import Input

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
            (self.width, self.height),
            pygame.OPENGL | pygame.DOUBLEBUF
        )

        self.clock = pygame.time.Clock()

        self.logger.info("Engine initialized.")

        self.renderer = Renderer()
        self.scene_manager = SceneManager()

        scene = Scene("Main Scene")

        triangle_object = GameObject("Triangle")
        triangle_object.add_component(MeshRenderer, self.renderer.ctx)
        triangle_object.transform.rotation = [45.0, 0.0, 0.0]
        scene.add_object(triangle_object)

        camera_object = GameObject("Main Camera")
        camera_object.add_component(Camera)
        camera_object.transform.position = [0.0, 0.0, 3.0]
        scene.add_object(camera_object)

        self.scene_manager.load_scene(scene)

    def run(self):
        self.running = True
        self.logger.info("Engine started.")

        while self.running:
            current_time = pygame.time.get_ticks() / 1000.0
            Time.update(current_time)

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