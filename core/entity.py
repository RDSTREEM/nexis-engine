"""
entity.py
Entity with parent/child hierarchy support (nesting/grouping).
Every entity can have children. Transform is relative to parent.
"""
from __future__ import annotations
import uuid
from typing import Type, TypeVar, List, Optional, TYPE_CHECKING

import numpy as np
from core.component import Component
from core.transform import Transform

if TYPE_CHECKING:
    from core.scene import Scene

T = TypeVar("T", bound=Component)


class Entity:
    def __init__(self, name: str = "Entity", scene: "Scene | None" = None):
        self.id:       str   = str(uuid.uuid4())
        self.name:     str   = name
        self.scene:    "Scene | None" = scene
        self.enabled:  bool  = True
        self.tags:     List[str] = []
        self._components: List[Component] = []
        self._children:   List["Entity"]  = []
        self._parent:     Optional["Entity"] = None

        self._transform = Transform()
        self._attach(self._transform)

    # ------------------------------------------------------------------
    # Transform
    # ------------------------------------------------------------------

    @property
    def transform(self) -> Transform:
        return self._transform

    def world_matrix(self) -> "np.ndarray":
        """Combines parent chain matrices for world-space transform."""
        if self._parent is None:
            return self._transform.matrix
        return self._parent.world_matrix() @ self._transform.matrix

    # ------------------------------------------------------------------
    # Parent / child hierarchy
    # ------------------------------------------------------------------

    @property
    def parent(self) -> Optional["Entity"]:
        return self._parent

    @property
    def children(self) -> List["Entity"]:
        return list(self._children)

    def add_child(self, child: "Entity") -> None:
        if child is self:
            raise ValueError("Entity cannot be its own child.")
        if child._parent is not None:
            child._parent.remove_child(child)
        child._parent = self
        child.scene   = self.scene
        self._children.append(child)
        # remove from scene top-level if it was there
        if self.scene and child in self.scene._entities:
            self.scene._entities.remove(child)

    def remove_child(self, child: "Entity") -> None:
        if child in self._children:
            child._parent = None
            self._children.remove(child)

    def detach_from_parent(self) -> None:
        if self._parent:
            self._parent.remove_child(self)
            if self.scene:
                self.scene._entities.append(self)

    def all_children_recursive(self) -> List["Entity"]:
        result = []
        for child in self._children:
            result.append(child)
            result.extend(child.all_children_recursive())
        return result

    def is_ancestor_of(self, other: "Entity") -> bool:
        current = other._parent
        while current is not None:
            if current is self:
                return True
            current = current._parent
        return False

    # ------------------------------------------------------------------
    # Component management
    # ------------------------------------------------------------------

    @property
    def transform(self) -> Transform:
        return self._transform

    def add_component(self, component: Component) -> Component:
        if isinstance(component, Transform):
            raise ValueError("Entity already has a Transform.")
        self._attach(component)
        return component

    def get_component(self, t: Type[T]) -> Optional[T]:
        for c in self._components:
            if isinstance(c, t):
                return c
        return None

    def get_components(self, t: Type[T]) -> List[T]:
        return [c for c in self._components if isinstance(c, t)]

    def get_component_in_children(self, t: Type[T]) -> Optional[T]:
        comp = self.get_component(t)
        if comp:
            return comp
        for child in self._children:
            comp = child.get_component_in_children(t)
            if comp:
                return comp
        return None

    def remove_component(self, component: Component) -> None:
        if isinstance(component, Transform):
            raise ValueError("Cannot remove Transform.")
        if component in self._components:
            component.on_detach()
            component.entity = None
            self._components.remove(component)

    def has_component(self, t: Type[T]) -> bool:
        return any(isinstance(c, t) for c in self._components)

    @property
    def components(self) -> List[Component]:
        return list(self._components)

    def _attach(self, component: Component) -> None:
        component.entity = self
        self._components.append(component)
        component.on_attach()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_start(self) -> None:
        for c in self._components:
            if c.enabled: c.on_start()
        for child in self._children:
            if child.enabled: child.on_start()

    def on_update(self, dt: float) -> None:
        if not self.enabled: return
        for c in self._components:
            if c.enabled: c.on_update(dt)
        for child in self._children:
            if child.enabled: child.on_update(dt)

    def on_stop(self) -> None:
        for c in self._components: c.on_stop()
        for child in self._children: child.on_stop()

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "name":       self.name,
            "enabled":    self.enabled,
            "tags":       self.tags,
            "components": [c.to_dict() for c in self._components],
            "children":   [c.to_dict() for c in self._children],
        }

    @classmethod
    def from_dict(cls, data: dict,
                  scene: "Scene | None" = None) -> "Entity":
        from core.component_registry import deserialize_component
        e        = cls.__new__(cls)
        e.id     = data.get("id", str(uuid.uuid4()))
        e.name   = data.get("name", "Entity")
        e.scene  = scene
        e.enabled= data.get("enabled", True)
        e.tags   = data.get("tags", [])
        e._components = []
        e._children   = []
        e._parent     = None

        for comp_data in data.get("components", []):
            comp = deserialize_component(comp_data)
            if comp: e._attach(comp)

        if not e.has_component(Transform):
            e._transform = Transform()
            e._attach(e._transform)
        else:
            e._transform = e.get_component(Transform)

        for child_data in data.get("children", []):
            child = Entity.from_dict(child_data, scene=scene)
            child._parent = e
            e._children.append(child)

        return e

    def __repr__(self) -> str:
        return f"<Entity '{self.name}' id={self.id[:8]}>"