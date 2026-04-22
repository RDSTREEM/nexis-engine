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

        # Tool modes: "select", "move", "hand", "place"
        self.tool_mode = "select"

        # Register editor input actions
        Input.register_action("toggle_ui", pygame.K_TAB)
        Input.register_action("tool_select", pygame.K_1)
        Input.register_action("tool_move", pygame.K_2)
        Input.register_action("tool_hand", pygame.K_3)
        Input.register_action("tool_place", pygame.K_4)

    def initialize(self, camera_component):
        self.camera_controller = EditorCameraController(camera_component)

    def update(self):
        scene = self.engine.scene_manager.current_scene
        if not scene:
            return

        # Handle tool switching
        if Input.get_action_down("tool_select"):
            self.tool_mode = "select"
            self.ui.set_tool_mode("select")
        elif Input.get_action_down("tool_move"):
            self.tool_mode = "move"
            self.ui.set_tool_mode("move")
        elif Input.get_action_down("tool_hand"):
            self.tool_mode = "hand"
            self.ui.set_tool_mode("hand")
        elif Input.get_action_down("tool_place"):
            self.tool_mode = "place"
            self.ui.set_tool_mode("place")

        # Update camera controller with current tool mode
        if self.camera_controller:
            self.camera_controller.update(self.tool_mode)

        # Handle input actions
        if Input.get_action_down("toggle_ui"):
            self.ui.toggle_ui()

        # Handle mouse interactions based on tool mode
        camera = scene.get_active_camera()
        if camera:
            screen_pos = Input.get_mouse_position()

            if self.tool_mode == "select":
                # Left click to select objects
                if Input.get_mouse_button_down(0):
                    picked = self.object_picker.pick_object(scene, camera, screen_pos)
                    scene.set_selected_object(picked)

            elif self.tool_mode == "move":
                # Left click to select, can move selected objects
                if Input.get_mouse_button_down(0):
                    picked = self.object_picker.pick_object(scene, camera, screen_pos)
                    scene.set_selected_object(picked)

            elif self.tool_mode == "hand":
                # Hand tool - camera navigation only, no object interaction
                pass

            elif self.tool_mode == "place":
                # Place objects on ground
                if Input.get_mouse_button_down(0):
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

    def render_ui(self):
        self.ui.render()
