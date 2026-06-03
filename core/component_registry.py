from __future__ import annotations
from typing import Optional
from core.component import Component

_REGISTRY: dict = {}


def _build():
    if _REGISTRY:
        return
    from core.transform import Transform
    from core.mesh_renderer import MeshRenderer
    from core.sprite_renderer import SpriteRenderer, Shape2DRenderer
    from core.camera_component import CameraComponent
    from core.physics_2d import BoxCollider2D, CircleCollider2D, Rigidbody2D
    from core.script_component import ScriptComponent

    for cls in [
        Transform,
        MeshRenderer,
        SpriteRenderer,
        Shape2DRenderer,
        CameraComponent,
        BoxCollider2D,
        CircleCollider2D,
        Rigidbody2D,
        ScriptComponent,
    ]:
        _REGISTRY[cls.__name__] = cls


def deserialize_component(data: dict) -> Optional[Component]:
    _build()
    cls = _REGISTRY.get(data.get("type", ""))
    if cls is None:
        print(f"[ComponentRegistry] Unknown type '{data.get('type')}' — skipping.")
        return None
    return cls.from_dict(data)
