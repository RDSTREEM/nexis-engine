import pygame


class Input:

    _keys = None
    _prev_keys = None

    _mouse_buttons = None
    _prev_mouse_buttons = None

    _mouse_pos = (0, 0)

    @classmethod
    def update(cls):

        cls._prev_keys = cls._keys
        cls._prev_mouse_buttons = cls._mouse_buttons

        cls._keys = pygame.key.get_pressed()
        cls._mouse_buttons = pygame.mouse.get_pressed()

        cls._mouse_pos = pygame.mouse.get_pos()

    @classmethod
    def get_key(cls, key):
        return cls._keys and cls._keys[key]

    @classmethod
    def get_key_down(cls, key):
        if cls._keys and cls._prev_keys:
            return cls._keys[key] and not cls._prev_keys[key]
        return False

    @classmethod
    def get_key_up(cls, key):
        if cls._keys and cls._prev_keys:
            return not cls._keys[key] and cls._prev_keys[key]
        return False

    @classmethod
    def get_mouse_button(cls, button):
        return cls._mouse_buttons and cls._mouse_buttons[button]

    @classmethod
    def get_mouse_position(cls):
        return cls._mouse_pos
