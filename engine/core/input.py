import pygame


class Input:
    _keys = None
    _mouse_pos = (0, 0)

    @classmethod
    def update(cls):
        cls._keys = pygame.key.get_pressed()
        cls._mouse_pos = pygame.mouse.get_pos()

    @classmethod
    def get_key(cls, key):
        if cls._keys:
            return cls._keys[key]
        return False

    @classmethod
    def get_mouse_position(cls):
        return cls._mouse_pos
