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
from engine.utils.math_utils import forward_vector


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

        material = Material(shader)

        AssetManager.register_mesh("cube", cube_mesh)
        AssetManager.register_mesh("plane", plane_mesh)
        AssetManager.register_mesh("quad", quad_mesh)
        AssetManager.register_mesh("triangle", mesh)
        AssetManager.register_material("default_blue", material)

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
                    hit = self._get_ground_intersection(screen_pos, camera)
                    if hit is not None:
                        self._place_object(scene, hit)

        self.scene_manager.update()

    def render(self):
        if self.scene_manager.current_scene:
            self.renderer.render(self.scene_manager.current_scene)

    def _screen_point_to_ray(self, mouse_pos, camera):
        x, y = mouse_pos
        ndc_x = (2.0 * x) / self.width - 1.0
        ndc_y = 1.0 - (2.0 * y) / self.height

        projection = camera.get_projection_matrix(
            self.renderer.ctx.screen.width / self.renderer.ctx.screen.height
        )
        view = camera.get_view_matrix()

        inv_proj = np.linalg.inv(projection)
        inv_view = np.linalg.inv(view)

        near_point = np.array([ndc_x, ndc_y, -1.0, 1.0], dtype="f4")
        far_point = np.array([ndc_x, ndc_y, 1.0, 1.0], dtype="f4")

        world_near = inv_view @ (inv_proj @ near_point)
        world_far = inv_view @ (inv_proj @ far_point)

        if world_near[3] != 0:
            world_near /= world_near[3]
        if world_far[3] != 0:
            world_far /= world_far[3]

        origin = world_near[0:3]
        direction = world_far[0:3] - origin
        norm = np.linalg.norm(direction)
        if norm != 0:
            direction = direction / norm

        return origin, direction

    def _get_ground_intersection(self, mouse_pos, camera, plane_y=0.0):
        origin, direction = self._screen_point_to_ray(mouse_pos, camera)

        if abs(direction[1]) < 1e-6:
            return None

        t = (plane_y - origin[1]) / direction[1]
        if t < 0:
            return None

        return origin + direction * t

    def _place_object(self, scene, position):
        from engine.components.mesh_renderer import MeshRenderer

        mesh = AssetManager.get_mesh("cube")
        material = AssetManager.get_material("default_blue")

        if mesh is None or material is None:
            self.logger.warning(
                "Cannot place object: cube mesh or default_blue material not found"
            )
            return

        count = len(scene.game_objects)
        obj = scene.create_object(f"PlacedCube_{count}")
        obj.transform.position = np.array(
            [position[0], position[1], position[2]], dtype="f4"
        )
        obj.transform.rotation = np.array([0.0, 0.0, 0.0], dtype="f4")
        obj.transform.scale = np.array([1.0, 1.0, 1.0], dtype="f4")
        obj.add_component(
            MeshRenderer, mesh, material, mesh_name="cube", material_name="default_blue"
        )
