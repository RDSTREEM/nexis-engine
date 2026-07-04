import pygame


class Input:

    _keys = None
    _prev_keys = None

    _mouse_buttons = None
    _prev_mouse_buttons = None

    _mouse_pos = (0, 0)
    _prev_mouse_pos = (0, 0)
    _mouse_delta = (0, 0)

    _mouse_scroll = 0
    _prev_mouse_scroll = 0

    _actions = {}

    @classmethod
    def register_action(cls, name, key):
        cls._actions[name] = key

    @classmethod
    def unregister_action(cls, name):
        cls._actions.pop(name, None)

    @classmethod
    def get_action(cls, name):
        key = cls._actions.get(name)
        if key is None:
            return False
        return cls.get_key(key)

    @classmethod
    def get_action_down(cls, name):
        key = cls._actions.get(name)
        if key is None:
            return False
        return cls.get_key_down(key)

    @classmethod
    def get_action_up(cls, name):
        key = cls._actions.get(name)
        if key is None:
            return False
        return cls.get_key_up(key)

    @classmethod
    def update(cls):

        cls._prev_keys = cls._keys
        cls._prev_mouse_buttons = cls._mouse_buttons

        cls._keys = pygame.key.get_pressed()
        cls._mouse_buttons = pygame.mouse.get_pressed()

        pos = pygame.mouse.get_pos()
        if cls._prev_mouse_pos:
            cls._mouse_delta = (
                pos[0] - cls._prev_mouse_pos[0],
                pos[1] - cls._prev_mouse_pos[1],
            )

        cls._prev_mouse_pos = pos
        cls._mouse_pos = pos

        cls._prev_mouse_scroll = cls._mouse_scroll
        cls._mouse_scroll = 0

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
    def get_mouse_button_down(cls, button):
        if cls._mouse_buttons is not None and cls._prev_mouse_buttons is not None:
            return cls._mouse_buttons[button] and not cls._prev_mouse_buttons[button]
        return False

    @classmethod
    def get_mouse_button_up(cls, button):
        if cls._mouse_buttons is not None and cls._prev_mouse_buttons is not None:
            return not cls._mouse_buttons[button] and cls._prev_mouse_buttons[button]
        return False

    @classmethod
    def get_mouse_position(cls):
        return cls._mouse_pos

    @classmethod
    def get_mouse_delta(cls):
        return cls._mouse_delta

    @classmethod
    def process_event(cls, event):
        if event.type == pygame.MOUSEWHEEL:
            cls._mouse_scroll = event.y

    @classmethod
    def get_mouse_scroll(cls):
        return cls._mouse_scroll
