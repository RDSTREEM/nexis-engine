"""
ImGui Layer

A helper class that wraps ImGui frame management for clean integration
with the engine's render loop.
"""

from imgui_bundle import imgui


class ImGuiLayer:
    """
    Handles ImGui frame begin/end and provides a clean interface for UI rendering.

    Responsibilities:
    - Manage begin_frame() and end_frame() calls
    - Wrap imgui calls cleanly
    - Provide utility methods for common UI operations
    """

    def __init__(self, engine):
        """
        Initialize the ImGui layer.

        Args:
            engine: The main Engine instance
        """
        self.engine = engine
        self.imgui = imgui
        self._initialized = False

    def initialize(self):
        """Initialize the ImGui layer."""
        if self._initialized:
            return

        # Configure ImGui IO
        io = imgui.get_io()

        # Set display size (will be updated each frame)
        io.display_size = (self.engine.width, self.engine.height)

        # Set backend flag to indicate we handle font texture ourselves
        # This prevents the "font atlas not built" assertion
        io.backend_flags = imgui.BackendFlags_.renderer_has_textures

        # Configure style
        self._configure_style()

        self._initialized = True

    def _configure_style(self):
        """Configure ImGui default style."""
        style = imgui.get_style()

        # Window settings
        style.window_padding = (8, 8)
        style.window_min_size = (300, 100)
        style.window_rounding = 4.0
        style.window_title_align = (0.0, 0.5)

        # Widget settings
        style.item_spacing = (8, 4)
        style.item_inner_spacing = (4, 4)
        style.indent_spacing = 21

        # Frame settings
        style.frame_padding = (4, 3)
        style.frame_rounding = 2.0
        style.frame_border_size = 1.0

        # Colors (dark theme) - use set_color_ with ImVec4 for imgui_bundle
        def set_color(col, r, g, b, a):
            style.set_color_(col, imgui.ImVec4(r, g, b, a))

        set_color(imgui.Col_.window_bg, 0.15, 0.15, 0.15, 0.95)
        set_color(imgui.Col_.title_bg, 0.1, 0.1, 0.15, 0.95)
        set_color(imgui.Col_.title_bg_active, 0.2, 0.2, 0.3, 0.95)
        set_color(imgui.Col_.header, 0.2, 0.2, 0.3, 0.95)
        set_color(imgui.Col_.header_hovered, 0.3, 0.3, 0.4, 0.95)
        set_color(imgui.Col_.header_active, 0.4, 0.4, 0.5, 0.95)
        set_color(imgui.Col_.button, 0.25, 0.25, 0.35, 0.95)
        set_color(imgui.Col_.button_hovered, 0.35, 0.35, 0.45, 0.95)
        set_color(imgui.Col_.button_active, 0.45, 0.45, 0.55, 0.95)
        set_color(imgui.Col_.frame_bg, 0.2, 0.2, 0.25, 0.95)
        set_color(imgui.Col_.frame_bg_hovered, 0.3, 0.3, 0.35, 0.95)
        set_color(imgui.Col_.frame_bg_active, 0.4, 0.4, 0.45, 0.95)
        set_color(imgui.Col_.text, 0.9, 0.9, 0.9, 1.0)
        set_color(imgui.Col_.text_disabled, 0.5, 0.5, 0.5, 1.0)
        set_color(imgui.Col_.border, 0.3, 0.3, 0.35, 0.95)
        set_color(imgui.Col_.separator, 0.4, 0.4, 0.45, 0.95)
        set_color(imgui.Col_.scrollbar_bg, 0.1, 0.1, 0.15, 0.95)
        set_color(imgui.Col_.scrollbar_grab, 0.3, 0.3, 0.4, 0.95)
        set_color(imgui.Col_.scrollbar_grab_hovered, 0.4, 0.4, 0.5, 0.95)
        set_color(imgui.Col_.scrollbar_grab_active, 0.5, 0.5, 0.6, 0.95)

    def begin_frame(self):
        """
        Begin a new ImGui frame.
        Call this at the start of the render loop.
        """
        if not self._initialized:
            self.initialize()

        # Update display size
        io = imgui.get_io()
        io.display_size = (self.engine.width, self.engine.height)

        # Begin ImGui frame
        imgui.new_frame()

    def end_frame(self):
        """
        End the current ImGui frame and get draw data.
        Call this after all UI rendering is complete.

        Returns:
            ImGui draw data to be passed to the renderer
        """
        imgui.render()
        return imgui.get_draw_data()

    def process_event(self, event):
        """
        Process a pygame event and forward it to ImGui.

        Args:
            event: pygame event

        Returns:
            True if the event was consumed by ImGui, False otherwise
        """
        io = imgui.get_io()
        consumed = False

        event_type = event.type

        # Mouse motion
        if event_type == pygame.MOUSEMOTION:
            io.mouse_pos = (event.pos[0], event.pos[1])
            consumed = True

        # Mouse buttons
        elif event_type == pygame.MOUSEBUTTONDOWN:
            button = event.button
            if button == 1:  # Left button
                io.mouse_down[0] = True
            elif button == 2:  # Right button
                io.mouse_down[1] = True
            elif button == 3:  # Middle button
                io.mouse_down[2] = True
            consumed = True

        elif event_type == pygame.MOUSEBUTTONUP:
            button = event.button
            if button == 1:
                io.mouse_down[0] = False
            elif button == 2:
                io.mouse_down[1] = False
            elif button == 3:
                io.mouse_down[2] = False
            consumed = True

        # Mouse wheel
        elif event_type == pygame.MOUSEWHEEL:
            io.mouse_wheel += event.y
            io.mouse_wheel_h += event.x
            consumed = True

        # Keyboard
        elif event_type == pygame.KEYDOWN:
            key = self._map_key(event.key)
            if key is not None:
                io.keys_down[key] = True
            consumed = True

        elif event_type == pygame.KEYUP:
            key = self._map_key(event.key)
            if key is not None:
                io.keys_down[key] = False
            consumed = True

        # Text input
        elif event_type == pygame.TEXTINPUT:
            for char in event.text:
                io.input_queue.push_back(ord(char))
            consumed = True

        return consumed

    def _map_key(self, pygame_key):
        """
        Map pygame key codes to ImGui key codes.

        Args:
            pygame_key: pygame key code

        Returns:
            ImGui key code or None if not mapped
        """
        # Pygame key to ImGui key mapping
        key_map = {
            pygame.K_TAB: imgui.Key.tab,
            pygame.K_LEFT: imgui.Key.left_arrow,
            pygame.K_RIGHT: imgui.Key.right_arrow,
            pygame.K_UP: imgui.Key.up_arrow,
            pygame.K_DOWN: imgui.Key.down_arrow,
            pygame.K_PAGEUP: imgui.Key.page_up,
            pygame.K_PAGEDOWN: imgui.Key.page_down,
            pygame.K_HOME: imgui.Key.home,
            pygame.K_END: imgui.Key.end,
            pygame.K_INSERT: imgui.Key.insert,
            pygame.K_DELETE: imgui.Key.delete,
            pygame.K_BACKSPACE: imgui.Key.backspace,
            pygame.K_SPACE: imgui.Key.space,
            pygame.K_RETURN: imgui.Key.enter,
            pygame.K_ESCAPE: imgui.Key.escape,
            pygame.K_a: imgui.Key.a,
            pygame.K_c: imgui.Key.c,
            pygame.K_v: imgui.Key.v,
            pygame.K_x: imgui.Key.x,
            pygame.K_y: imgui.Key.y,
            pygame.K_z: imgui.Key.z,
        }

        return key_map.get(pygame_key)


# Import pygame for event types
import pygame
