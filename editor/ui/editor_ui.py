class EditorUI:
    def __init__(self, engine):
        self.engine = engine
        self.imgui = engine.imgui
        self.imgui_renderer = engine.imgui_renderer
        self.show_ui = True

    def render(self):
        if not self.imgui:
            return

        self.imgui.new_frame()

        if self.show_ui:
            self.render_main_ui()

        self.imgui.end_frame()
        self.imgui.render()
        self.imgui_renderer.render(self.imgui.get_draw_data())

    def render_main_ui(self):
        self.imgui.begin("Nexis Engine Editor", True)

        # Performance info
        self.imgui.text(f"FPS: {self.engine.clock.get_fps():.1f}")
        scene = self.engine.scene_manager.current_scene
        if scene:
            self.imgui.text(f"Objects: {len(scene.game_objects)}")

            # Selected object info
            selected = scene.get_selected_object()
            if selected:
                self.imgui.text(f"Selected: {selected.name}")
                pos = selected.transform.position
                rot = selected.transform.rotation
                scl = selected.transform.scale
                self.imgui.text(f"Position: {pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}")
                self.imgui.text(f"Rotation: {rot[0]:.2f}, {rot[1]:.2f}, {rot[2]:.2f}")
                self.imgui.text(f"Scale: {scl[0]:.2f}, {scl[1]:.2f}, {scl[2]:.2f}")

                if self.imgui.button("Delete Selected"):
                    scene.remove_object(selected)
                    scene.set_selected_object(None)

            # Spawn buttons
            if self.imgui.button("Spawn Cube"):
                camera = scene.get_active_camera()
                if camera:
                    spawn_pos = camera.game_object.transform.position + [0, 0, -5]
                    colors = ["default_blue", "default_red", "default_green"]
                    material_name = colors[len(scene.game_objects) % len(colors)]
                    scene.place_object(
                        spawn_pos,
                        mesh_name="cube",
                        material_name=material_name,
                    )

        self.imgui.end()

    def toggle_ui(self):
        self.show_ui = not self.show_ui
