from __future__ import annotations
from typing import Set, Tuple
import numpy as np


class _InputManager:
    def __init__(self):
        self._keys_held: Set[int] = set()
        self._keys_pressed: Set[int] = set()  # only true for one frame
        self._keys_released: Set[int] = set()  # only true for one frame
        self._mouse_pos: Tuple[float, float] = (0.0, 0.0)
        self._mouse_delta: Tuple[float, float] = (0.0, 0.0)
        self._mouse_buttons: Set[int] = set()
        self._mouse_pressed: Set[int] = set()
        self._mouse_released: Set[int] = set()
        self._scroll_delta: float = 0.0

    # ------------------------------------------------------------------
    # Called by ViewportWidget at the START of each frame
    # ------------------------------------------------------------------

    def begin_frame(self) -> None:
        """Clear single-frame sets. Call before processing Qt events."""
        self._keys_pressed.clear()
        self._keys_released.clear()
        self._mouse_pressed.clear()
        self._mouse_released.clear()
        self._mouse_delta = (0.0, 0.0)
        self._scroll_delta = 0.0

    # ------------------------------------------------------------------
    # Called by ViewportWidget event handlers
    # ------------------------------------------------------------------

    def on_key_press(self, key: int) -> None:
        if key not in self._keys_held:
            self._keys_pressed.add(key)
        self._keys_held.add(key)

    def on_key_release(self, key: int) -> None:
        self._keys_held.discard(key)
        self._keys_released.add(key)

    def on_mouse_move(self, x: float, y: float) -> None:
        ox, oy = self._mouse_pos
        self._mouse_delta = (x - ox, y - oy)
        self._mouse_pos = (x, y)

    def on_mouse_press(self, button: int) -> None:
        if button not in self._mouse_buttons:
            self._mouse_pressed.add(button)
        self._mouse_buttons.add(button)

    def on_mouse_release(self, button: int) -> None:
        self._mouse_buttons.discard(button)
        self._mouse_released.add(button)

    def on_scroll(self, delta: float) -> None:
        self._scroll_delta += delta

    # ------------------------------------------------------------------
    # Script API
    # ------------------------------------------------------------------

    def get_key(self, key: int) -> bool:
        """True every frame the key is held."""
        return key in self._keys_held

    def get_key_down(self, key: int) -> bool:
        """True only on the frame the key was first pressed."""
        return key in self._keys_pressed

    def get_key_up(self, key: int) -> bool:
        """True only on the frame the key was released."""
        return key in self._keys_released

    def get_mouse_button(self, button: int) -> bool:
        return button in self._mouse_buttons

    def get_mouse_button_down(self, button: int) -> bool:
        return button in self._mouse_pressed

    def get_mouse_button_up(self, button: int) -> bool:
        return button in self._mouse_released

    def get_mouse_position(self) -> Tuple[float, float]:
        return self._mouse_pos

    def get_mouse_delta(self) -> Tuple[float, float]:
        return self._mouse_delta

    def get_scroll(self) -> float:
        return self._scroll_delta

    def get_axis(self, negative_key: int, positive_key: int) -> float:
        """Returns -1, 0, or 1. Useful for movement: get_axis(Key_A, Key_D)."""
        v = 0.0
        if self.get_key(negative_key):
            v -= 1.0
        if self.get_key(positive_key):
            v += 1.0
        return v


# Singleton
Input = _InputManager()
