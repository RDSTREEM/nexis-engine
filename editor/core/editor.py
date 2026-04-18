import pygame
from engine.core.input import Input
from engine.utils.math_utils import get_ground_intersection
from editor.tools.camera_controller import EditorCameraController
from editor.tools.object_picker import ObjectPicker
from editor.ui.editor_ui import EditorUI


class Editor:
    def __init__(self, engine):
        self.engine = engine
        self.camera_controller = None
        self.object_picker = ObjectPicker(engine)
        self.ui = EditorUI(engine)

        # Register editor input actions
        Input.register_action("toggle_ui", pygame.K_TAB)

    def initialize(self, camera_component):
        self.camera_controller = EditorCameraController(camera_component)

    def update(self):
        scene = self.engine.scene_manager.current_scene
        if not scene:
            return

        # Update camera controller
        if self.camera_controller:
            self.camera_controller.update()

        # Handle input actions
        if Input.get_action_down("toggle_ui"):
            self.ui.toggle_ui()

        # Handle mouse interactions
        camera = scene.get_active_camera()
        if camera:
            if Input.get_mouse_button_down(0):
                screen_pos = Input.get_mouse_position()
                if Input.get_key(pygame.K_LCTRL) or Input.get_key(pygame.K_RCTRL):
                    # Pick object
                    picked = self.object_picker.pick_object(scene, camera, screen_pos)
                    scene.set_selected_object(picked)
                else:
                    # Place object on ground
                    hit = get_ground_intersection(
                        screen_pos, camera, self.engine.width, self.engine.height
                    )
                    if hit is not None:
                        colors = ["default_blue", "default_red", "default_green"]
                        material_name = colors[len(scene.game_objects) % len(colors)]
                        scene.place_object(
                            hit,
                            mesh_name="cube",
                            material_name=material_name,
                        )

            if Input.get_mouse_button_down(2):
                # Pick object with right click
                screen_pos = Input.get_mouse_position()
                picked = self.object_picker.pick_object(scene, camera, screen_pos)
                scene.set_selected_object(picked)

    def render_ui(self):
        self.ui.render()
