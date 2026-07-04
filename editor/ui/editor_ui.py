from imgui_bundle import imgui


class EditorUI:
    def __init__(self, engine):
        self.engine = engine
        self.imgui = imgui  # Use imgui_bundle directly
        self.show_ui = True
        self.tool_mode = "select"

        # UI layout state
        self.scene_tree_expanded = True

    def set_tool_mode(self, mode):
        self.tool_mode = mode

    def render(self):
        """
        Render the editor UI.
        Note: imgui.new_frame() is called by ImGuiLayer before this.
        Rendering is handled by ModernGLImGuiRenderer after this.
        """
        if not self.imgui:
            return

        # Note: We don't call new_frame() or render() here anymore.
        # The ImGuiLayer handles frame management in the Engine.
        # We just call the UI rendering functions.

        if self.show_ui:
            self.render_toolbar()
            self.render_scene_hierarchy()
            self.render_properties()
            self.render_status_bar()

    def render_toolbar(self):
        # Use window-relative positioning that adjusts on resize
        self.imgui.set_next_window_pos(self.imgui.ImVec2(0, 0))
        self.imgui.set_next_window_size(self.imgui.ImVec2(self.engine.width, 40))
        self.imgui.begin("Toolbar", True)
        self.imgui.set_window_pos((0, 0))
        self.imgui.set_window_size((self.engine.width, 40))

        self.imgui.text("  Tools:  ")

        # Tool buttons
        if self.tool_mode == "select":
            self.imgui.push_style_color(
                self.imgui.Col_.button, self.imgui.ImVec4(0.3, 0.5, 0.8, 1.0)
            )
        if self.imgui.button("Select##tool_select"):
            self.tool_mode = "select"
        if self.tool_mode == "select":
            self.imgui.pop_style_color()

        self.imgui.same_line()

        if self.tool_mode == "move":
            self.imgui.push_style_color(
                self.imgui.Col_.button, self.imgui.ImVec4(0.3, 0.5, 0.8, 1.0)
            )
        if self.imgui.button("Move##tool_move"):
            self.tool_mode = "move"
        if self.tool_mode == "move":
            self.imgui.pop_style_color()

        self.imgui.same_line()

        if self.tool_mode == "hand":
            self.imgui.push_style_color(
                self.imgui.Col_.button, self.imgui.ImVec4(0.3, 0.5, 0.8, 1.0)
            )
        if self.imgui.button("Hand##tool_hand"):
            self.tool_mode = "hand"
        if self.tool_mode == "hand":
            self.imgui.pop_style_color()

        self.imgui.same_line()

        if self.tool_mode == "place":
            self.imgui.push_style_color(
                self.imgui.Col_.button, self.imgui.ImVec4(0.3, 0.5, 0.8, 1.0)
            )
        if self.imgui.button("Place##tool_place"):
            self.tool_mode = "place"
        if self.tool_mode == "place":
            self.imgui.pop_style_color()

        self.imgui.same_line()
        self.imgui.text("  |  ")
        self.imgui.same_line()

        # Help text
        if self.tool_mode == "hand":
            self.imgui.text(
                "Hand: Right-drag to pan, Scroll to zoom, Alt+Left-drag to orbit"
            )
        elif self.tool_mode == "place":
            self.imgui.text("Place: Left-click to place cube")
        elif self.tool_mode == "select":
            self.imgui.text("Select: Left-click to select objects")
        elif self.tool_mode == "move":
            self.imgui.text("Move: WASD to fly, Right-drag to orbit, Scroll to zoom")

        self.imgui.end()

    def render_scene_hierarchy(self):
        self.imgui.set_next_window_pos(self.imgui.ImVec2(0, 40))
        self.imgui.set_next_window_size(self.imgui.ImVec2(250, self.engine.height - 40))
        self.imgui.begin("Scene Hierarchy", True)

        scene = self.engine.scene_manager.current_scene
        if scene:
            # Toggle scene tree
            if self.imgui.tree_node_ex(
                "Game Objects", self.imgui.TreeNodeFlags_.default_open
            ):
                for obj in scene.game_objects:
                    is_selected = scene.get_selected_object() == obj
                    if is_selected:
                        self.imgui.push_style_color(
                            self.imgui.Col_.text, 1.0, 0.8, 0.4, 1.0
                        )

                    # Object node with icon
                    self.imgui.text(f"  [ ] {obj.name}")

                    if is_selected:
                        self.imgui.pop_style_color()

                self.imgui.tree_pop()

            # Stats
            self.imgui.separator()
            self.imgui.text(f"Total Objects: {len(scene.game_objects)}")

        self.imgui.end()

    def render_properties(self):
        props_height = self.engine.height - 40
        self.imgui.set_next_window_pos(
            self.imgui.ImVec2(0, 40 + (self.engine.height - 40) // 2)
        )
        self.imgui.set_next_window_size(self.imgui.ImVec2(300, props_height // 2))
        self.imgui.begin("Properties", True)

        scene = self.engine.scene_manager.current_scene
        if scene:
            selected = scene.get_selected_object()
            if selected:
                self.imgui.text(f"Object: {selected.name}")
                self.imgui.separator()

                # Transform section
                if self.imgui.tree_node_ex(
                    "Transform", self.imgui.TreeNodeFlags_.default_open
                ):
                    pos = selected.transform.position
                    rot = selected.transform.rotation
                    scl = selected.transform.scale

                    self.imgui.text("Position")
                    self.imgui.same_line(80)
                    self.imgui.text(f"X: {pos[0]:.2f}")
                    self.imgui.same_line()
                    self.imgui.text(f"Y: {pos[1]:.2f}")
                    self.imgui.same_line()
                    self.imgui.text(f"Z: {pos[2]:.2f}")

                    self.imgui.text("Rotation")
                    self.imgui.same_line(80)
                    self.imgui.text(f"X: {rot[0]:.2f}")
                    self.imgui.same_line()
                    self.imgui.text(f"Y: {rot[1]:.2f}")
                    self.imgui.same_line()
                    self.imgui.text(f"Z: {rot[2]:.2f}")

                    self.imgui.text("Scale")
                    self.imgui.same_line(80)
                    self.imgui.text(f"X: {scl[0]:.2f}")
                    self.imgui.same_line()
                    self.imgui.text(f"Y: {scl[1]:.2f}")
                    self.imgui.same_line()
                    self.imgui.text(f"Z: {scl[2]:.2f}")

                    self.imgui.tree_pop()

                # Components section
                if self.imgui.tree_node("Components"):
                    for comp in selected.components:
                        self.imgui.text(f"  > {comp.__class__.__name__}")
                    self.imgui.tree_pop()

                # Actions
                self.imgui.separator()
                if self.imgui.button("Delete Object"):
                    scene.remove_object(selected)
                    scene.set_selected_object(None)
            else:
                self.imgui.text("No object selected")
                self.imgui.text("Use Select tool and click")
                self.imgui.text("an object to edit properties")

        self.imgui.end()

    def render_status_bar(self):
        self.imgui.set_next_window_pos(self.imgui.ImVec2(0, self.engine.height - 25))
        self.imgui.set_next_window_size(self.imgui.ImVec2(self.engine.width, 25))
        self.imgui.begin("Status", True)

        scene = self.engine.scene_manager.current_scene
        selected = scene.get_selected_object() if scene else None

        self.imgui.text(
            f"FPS: {self.engine.clock.get_fps():.1f} | Tool: {self.tool_mode.upper()} | Objects: {len(scene.game_objects) if scene else 0}"
        )
        if selected:
            self.imgui.same_line()
            self.imgui.text(f" | Selected: {selected.name}")

        self.imgui.end()

    def toggle_ui(self):
        self.show_ui = not self.show_ui
