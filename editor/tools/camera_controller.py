import numpy as np
import pygame
from engine.core.input import Input
from engine.core.time import Time
from engine.utils.math_utils import forward_vector


class EditorCameraController:
    def __init__(self, camera_component):
        self.camera = camera_component
        self.move_speed = 5.0
        self.fast_move_multiplier = 2.0
        self.rotation_speed = 0.2
        self.zoom_speed = 10.0

    def update(self):
        if not self.camera:
            return

        transform = self.camera.game_object.transform
        delta_time = Time.delta_time

        # Movement
        speed = self.move_speed * delta_time
        if Input.get_key(pygame.K_LSHIFT) or Input.get_key(pygame.K_RSHIFT):
            speed *= self.fast_move_multiplier

        forward = forward_vector(transform.rotation)
        right = np.array([-forward[2], 0, -forward[0]], dtype="f4")
        up = np.array([0, 1, 0], dtype="f4")

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

        # Rotation with right mouse button
        if Input.get_mouse_button(2):
            mx, my = Input.get_mouse_delta()
            transform.rotation[1] -= mx * self.rotation_speed * delta_time
            transform.rotation[0] += my * self.rotation_speed * delta_time
            pygame.mouse.set_visible(False)
            pygame.event.set_grab(True)
        else:
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)

        # Zooming with scroll wheel - move camera along forward vector
        scroll_y = Input.get_mouse_scroll()
        if scroll_y != 0:
            zoom_amount = scroll_y * self.zoom_speed * delta_time
            transform.position += forward * zoom_amount
            return
