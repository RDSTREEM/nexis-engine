from __future__ import annotations
from typing import Optional

from core.component import Component

# Registry maps type name string → class
# Add new component types here as the engine grows
_REGISTRY: dict = {}


def register(cls):
    """Decorator — registers a component class by its name."""
    _REGISTRY[cls.__name__] = cls
    return cls


def _build_registry():
    """Lazily import and register all known component types."""
    if _REGISTRY:
        return
    from core.transform import Transform
    from core.mesh_renderer import MeshRenderer
    from core.sprite_renderer import SpriteRenderer
    from core.camera_component import CameraComponent

    for cls in [Transform, MeshRenderer, SpriteRenderer, CameraComponent]:
        _REGISTRY[cls.__name__] = cls


def deserialize_component(data: dict) -> Optional[Component]:
    _build_registry()
    type_name = data.get("type")
    cls = _REGISTRY.get(type_name)
    if cls is None:
        print(f"[ComponentRegistry] Unknown component type '{type_name}' — skipping.")
        return None
    return cls.from_dict(data)
