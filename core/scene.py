"""
scene.py
FIX: _render_entity uses try/finally so transform is always restored.
FIX: _find_main_camera is public (used by viewport play mode render).
"""

from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    import moderngl
    from core.entity import Entity
    from core.camera_component import CameraComponent


class Scene:
    def __init__(self, name: str = "Untitled Scene", scene_type: str = "3D"):
        self.name: str = name
        self.scene_type: str = scene_type
        self._entities: list = []
        self._physics_world = None  # set by PlayMode._init_physics

    # ── Entity management ─────────────────────────────────────────────

    def create_entity(self, name: str = "Entity", template_fn=None):
        from core.entity import Entity

        if template_fn:
            e = template_fn(self, name)
        else:
            e = Entity(name=name, scene=self)
        self._entities.append(e)
        return e

    def add_entity(self, entity) -> None:
        entity.scene = self
        if entity not in self._entities:
            self._entities.append(entity)

    def remove_entity(self, entity) -> None:
        if entity in self._entities:
            self._entities.remove(entity)
            entity.scene = None
        for top in self._entities:
            if entity in top.children:
                top.remove_child(entity)

    def get_entity(self, name: str):
        for e in self._all_entities():
            if e.name == name:
                return e
        return None

    def get_entity_by_id(self, eid: str):
        for e in self._all_entities():
            if e.id == eid:
                return e
        return None

    def get_entities_by_tag(self, tag: str) -> list:
        return [e for e in self._all_entities() if tag in e.tags]

    @property
    def entities(self) -> list:
        return list(self._entities)

    def all_entities(self) -> list:
        return list(self._all_entities())

    def _all_entities(self):
        for e in self._entities:
            yield e
            yield from e.all_children_recursive()

    # ── Lifecycle ─────────────────────────────────────────────────────

    def start(self) -> None:
        for e in self._entities:
            if e.enabled:
                e.on_start()

    def update(self, dt: float) -> None:
        for e in self._entities:
            if e.enabled:
                e.on_update(dt)

    def stop(self) -> None:
        for e in self._entities:
            e.on_stop()

    # ── Rendering ─────────────────────────────────────────────────────

    def render_editor(self, ctx, view: np.ndarray, proj: np.ndarray) -> None:
        for entity in self._all_entities():
            if not entity.enabled:
                continue
            self._render_entity(ctx, entity, view, proj)

    def _render_entity(self, ctx, entity, view, proj) -> None:
        from core.mesh_renderer import MeshRenderer
        from core.sprite_renderer import SpriteRenderer, Shape2DRenderer

        for comp_cls in (MeshRenderer, SpriteRenderer, Shape2DRenderer):
            comp = entity.get_component(comp_cls)
            if comp and comp.enabled:
                orig_mat = entity.transform._matrix.copy()
                orig_dirty = entity.transform._dirty
                try:
                    entity.transform._matrix = entity.world_matrix()
                    entity.transform._dirty = False
                    comp.render(ctx, view, proj)
                finally:
                    # Always restore — even if render() throws
                    entity.transform._matrix = orig_mat
                    entity.transform._dirty = orig_dirty

    def render_play(self, ctx, width: int, height: int) -> bool:
        """Render from the scene's main camera. Returns False if no camera."""
        cam = self._find_main_camera()
        if cam is None:
            return False
        view = cam.get_view_matrix()
        proj = cam.get_projection_matrix(width, height)
        self.render_editor(ctx, view, proj)
        return True

    def _find_main_camera(self):
        from core.camera_component import CameraComponent

        for entity in self._all_entities():
            if not entity.enabled:
                continue
            cam = entity.get_component(CameraComponent)
            if cam and cam.enabled and cam.is_main:
                return cam
        return None

    # ── Serialisation ─────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "scene_type": self.scene_type,
            "entities": [e.to_dict() for e in self._entities],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Scene":
        from core.entity import Entity

        scene = cls(
            name=data.get("name", "Untitled"),
            scene_type=data.get("scene_type", "3D"),
        )
        for e_data in data.get("entities", []):
            entity = Entity.from_dict(e_data, scene=scene)
            scene._entities.append(entity)
        return scene

    def __repr__(self) -> str:
        return f"<Scene '{self.name}' ({len(self._entities)} root entities)>"
