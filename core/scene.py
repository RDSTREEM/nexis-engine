from __future__ import annotations
from typing import List, Optional
import moderngl
import numpy as np

from core.entity import Entity
from core.mesh_renderer import MeshRenderer
from core.sprite_renderer import SpriteRenderer, Shape2DRenderer
from core.camera_component import CameraComponent


class Scene:
    def __init__(self, name: str = "Untitled Scene", scene_type: str = "3D"):
        self.name: str = name
        self.scene_type: str = scene_type
        self._entities: List[Entity] = []

    # ------------------------------------------------------------------
    # Entity management
    # ------------------------------------------------------------------

    def create_entity(self, name: str = "Entity") -> Entity:
        e = Entity(name=name, scene=self)
        self._entities.append(e)
        return e

    def add_entity(self, entity: Entity) -> None:
        entity.scene = self
        self._entities.append(entity)

    def remove_entity(self, entity: Entity) -> None:
        if entity in self._entities:
            self._entities.remove(entity)
            entity.scene = None

    def get_entity(self, name: str) -> Optional[Entity]:
        for e in self._entities:
            if e.name == name:
                return e
        return None

    def get_entity_by_id(self, entity_id: str) -> Optional[Entity]:
        for e in self._entities:
            if e.id == entity_id:
                return e
        return None

    @property
    def entities(self) -> List[Entity]:
        return list(self._entities)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        for e in self._entities:
            if e.enabled:
                e.on_start()

    def update(self, delta_time: float) -> None:
        for e in self._entities:
            if e.enabled:
                e.on_update(delta_time)

    def stop(self) -> None:
        for e in self._entities:
            e.on_stop()

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render_editor(
        self, ctx: moderngl.Context, view: np.ndarray, proj: np.ndarray
    ) -> None:
        for entity in self._entities:
            if not entity.enabled:
                continue
            for comp_type in (MeshRenderer, SpriteRenderer, Shape2DRenderer):
                comp = entity.get_component(comp_type)
                if comp:
                    comp.render(ctx, view, proj)

    def render_play(self, ctx: moderngl.Context, width: int, height: int) -> bool:
        cam = self._find_main_camera()
        if cam is None:
            return False
        view = cam.get_view_matrix()
        proj = cam.get_projection_matrix(width, height)
        self.render_editor(ctx, view, proj)
        return True

    def _find_main_camera(self) -> Optional[CameraComponent]:
        for entity in self._entities:
            if not entity.enabled:
                continue
            cam = entity.get_component(CameraComponent)
            if cam and cam.enabled and cam.is_main:
                return cam
        return None

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "scene_type": self.scene_type,
            "entities": [e.to_dict() for e in self._entities],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Scene":
        scene = cls(
            name=data.get("name", "Untitled"), scene_type=data.get("scene_type", "3D")
        )
        for e_data in data.get("entities", []):
            entity = Entity.from_dict(e_data, scene=scene)
            scene._entities.append(entity)
        return scene

    def __repr__(self) -> str:
        return f"<Scene '{self.name}' ({len(self._entities)} entities)>"
