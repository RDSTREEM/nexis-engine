import numpy as np
import pygame
from engine.core.input import Input
from engine.core.time import Time
from engine.utils.math_utils import forward_vector


class EditorCameraController:
    def __init__(self, camera_component):
        self.camera = camera_component
        self.move_speed = 8.0
        self.rotation_speed = 0.3
        self.zoom_speed = 15.0
        self.pan_speed = 0.5

        # For smooth panning
        self._is_panning = False
        self._last_mouse_pos = (0, 0)

    def update(self, tool_mode):
        if not self.camera:
            return

        transform = self.camera.game_object.transform
        delta_time = Time.delta_time
        forward = forward_vector(transform.rotation)
        right = np.array([-forward[2], 0, -forward[0]], dtype="f4")
        up = np.array([0, 1, 0], dtype="f4")

        # Hand tool: Mouse-only navigation
        if tool_mode == "hand":
            mouse_pos = Input.get_mouse_position()

            # Right click - Pan
            if Input.get_mouse_button(2):
                if not self._is_panning:
                    self._is_panning = True
                    self._last_mouse_pos = mouse_pos

                dx = mouse_pos[0] - self._last_mouse_pos[0]
                dy = mouse_pos[1] - self._last_mouse_pos[1]

                # Pan in screen space
                transform.position -= right * dx * self.pan_speed * delta_time
                transform.position += up * dy * self.pan_speed * delta_time

                self._last_mouse_pos = mouse_pos
                pygame.mouse.set_visible(False)
                pygame.event.set_grab(True)
            else:
                self._is_panning = False
                pygame.mouse.set_visible(True)
                pygame.event.set_grab(False)

            # Scroll wheel - Zoom (dolly)
            scroll_y = Input.get_mouse_scroll()
            if scroll_y != 0:
                zoom_amount = scroll_y * self.zoom_speed * delta_time
                transform.position += forward * zoom_amount

            # Alt + Left click - Orbit rotation
            if Input.get_key(pygame.K_LALT) and Input.get_mouse_button_down(0):
                mx, my = Input.get_mouse_delta()
                transform.rotation[1] -= mx * self.rotation_speed
                transform.rotation[0] += my * self.rotation_speed
                pygame.mouse.set_visible(False)
                pygame.event.set_grab(True)

            # Release grab when alt is released
            if not Input.get_key(pygame.K_LALT):
                pygame.mouse.set_visible(True)
                pygame.event.set_grab(False)

        # Move tool: WASD for fly-through
        elif tool_mode == "move":
            speed = self.move_speed * delta_time

            if Input.get_key(pygame.K_w):
                transform.position += forward * speed
            if Input.get_key(pygame.K_s):
                transform.position -= forward * speed
            if Input.get_key(pygame.K_a):
                transform.position -= right * speed
            if Input.get_key(pygame.K_d):
                transform.position += right * speed
            if Input.get_key(pygame.K_q):
                transform.position -= up * speed
            if Input.get_key(pygame.K_e):
                transform.position += up * speed

            # Right click to orbit
            if Input.get_mouse_button(2):
                mx, my = Input.get_mouse_delta()
                transform.rotation[1] -= mx * self.rotation_speed * delta_time
                transform.rotation[0] += my * self.rotation_speed * delta_time
                pygame.mouse.set_visible(False)
                pygame.event.set_grab(True)
            else:
                pygame.mouse.set_visible(True)
                pygame.event.set_grab(False)

            # Scroll to zoom
            scroll_y = Input.get_mouse_scroll()
            if scroll_y != 0:
                zoom_amount = scroll_y * self.zoom_speed * delta_time
                transform.position += forward * zoom_amount
