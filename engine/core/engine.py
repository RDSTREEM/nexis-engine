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
from engine.core.input import Input
from engine.rendering.primitives import create_cube, create_plane, create_quad
from engine.utils.math_utils import (
    forward_vector,
    screen_point_to_ray,
    get_ground_intersection,
)


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
        scene = self.scene_manager.current_scene
        if scene:
            camera = scene.get_active_camera()
            if camera:
                speed = 3.0 * Time.delta_time
                rot_speed = 0.2
                transform = camera.game_object.transform
                forward = forward_vector(transform.rotation)
                right = np.array([-forward[2], 0, -forward[0]], dtype="f4")
                up = np.array([0, 1, 0], dtype="f4")
                # Movement controls
                if Input.get_key(pygame.K_w):
                    transform.position += forward * speed
                if Input.get_key(pygame.K_s):
                    transform.position -= forward * speed
                if Input.get_key(pygame.K_a):
                    transform.position -= right * speed
                if Input.get_key(pygame.K_d):
                    transform.position += right * speed
                if Input.get_key(pygame.K_SPACE):
                    transform.position += up * speed
                if Input.get_key(pygame.K_LSHIFT):
                    transform.position -= up * speed

                mx, my = Input.get_mouse_delta()
                if Input.get_mouse_button(2):
                    transform.rotation[1] -= mx * rot_speed
                    transform.rotation[0] += my * rot_speed
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)
                else:
                    pygame.mouse.set_visible(True)
                    pygame.event.set_grab(False)

                if Input.get_mouse_button_down(0):
                    screen_pos = Input.get_mouse_position()
                    if Input.get_key(pygame.K_LCTRL) or Input.get_key(pygame.K_RCTRL):
                        picked = self.pick_object(scene, camera, screen_pos)
                        scene.set_selected_object(picked)
                    else:
                        hit = get_ground_intersection(
                            screen_pos, camera, self.width, self.height
                        )
                        if hit is not None:
                            colors = [
                                "default_blue",
                                "default_red",
                                "default_green",
                            ]
                            material_name = colors[len(scene.game_objects) % len(colors)]
                            scene.place_object(
                                np.array([hit[0], hit[1], hit[2]], dtype="f4"),
                                mesh_name="cube",
                                material_name=material_name,
                            )

                if Input.get_mouse_button_down(2):
                    screen_pos = Input.get_mouse_position()
                    picked = self.pick_object(scene, camera, screen_pos)
                    scene.set_selected_object(picked)

        self.scene_manager.update()

    def pick_object(self, scene, camera, mouse_screen_pos, radius=0.75):
        origin, direction = screen_point_to_ray(
            mouse_screen_pos, camera, self.width, self.height
        )

        closest = None
        closest_t = float("inf")

        for obj in scene.game_objects:
            center = obj.transform.position
            oc = origin - center
            b = np.dot(oc, direction)
            c = np.dot(oc, oc) - radius * radius
            discriminant = b * b - c
            if discriminant < 0:
                continue
            t = -b - np.sqrt(discriminant)
            if 0 < t < closest_t:
                closest_t = t
                closest = obj

        return closest

    def render(self):
        if self.scene_manager.current_scene:
            self.renderer.render(self.scene_manager.current_scene)
