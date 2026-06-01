from __future__ import annotations
import uuid
from typing import Type, TypeVar, List, Optional, TYPE_CHECKING

from core.component import Component
from core.transform import Transform

if TYPE_CHECKING:
    from core.scene import Scene

T = TypeVar("T", bound=Component)


class Entity:
    """
    A named object in the scene. Always has a Transform.
    All other behaviour comes from attached Components.
    """

    def __init__(self, name: str = "Entity", scene: "Scene | None" = None):
        self.id: str = str(uuid.uuid4())
        self.name: str = name
        self.scene: "Scene | None" = scene
        self.enabled: bool = True
        self.tags: List[str] = []
        self._components: List[Component] = []

        # every entity always has a transform
        self._transform = Transform()
        self._attach(self._transform)

    # ------------------------------------------------------------------
    # Transform shortcut
    # ------------------------------------------------------------------

    @property
    def transform(self) -> Transform:
        return self._transform

    # ------------------------------------------------------------------
    # Component management
    # ------------------------------------------------------------------

    def add_component(self, component: Component) -> Component:
        if isinstance(component, Transform):
            raise ValueError("Entity already has a Transform — cannot add another.")
        self._attach(component)
        return component

    def get_component(self, component_type: Type[T]) -> Optional[T]:
        for c in self._components:
            if isinstance(c, component_type):
                return c
        return None

    def get_components(self, component_type: Type[T]) -> List[T]:
        return [c for c in self._components if isinstance(c, component_type)]

    def remove_component(self, component: Component) -> None:
        if isinstance(component, Transform):
            raise ValueError("Cannot remove Transform from an Entity.")
        if component in self._components:
            component.on_detach()
            component.entity = None
            self._components.remove(component)

    def has_component(self, component_type: Type[T]) -> bool:
        return any(isinstance(c, component_type) for c in self._components)

    @property
    def components(self) -> List[Component]:
        return list(self._components)

    def _attach(self, component: Component) -> None:
        component.entity = self
        self._components.append(component)
        component.on_attach()

    # ------------------------------------------------------------------
    # Lifecycle (forwarded from Scene)
    # ------------------------------------------------------------------

    def on_start(self) -> None:
        for c in self._components:
            if c.enabled:
                c.on_start()

    def on_update(self, delta_time: float) -> None:
        if not self.enabled:
            return
        for c in self._components:
            if c.enabled:
                c.on_update(delta_time)

    def on_stop(self) -> None:
        for c in self._components:
            c.on_stop()

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "enabled": self.enabled,
            "tags": self.tags,
            "components": [c.to_dict() for c in self._components],
        }

    @classmethod
    def from_dict(cls, data: dict, scene: "Scene | None" = None) -> "Entity":
        from core.component_registry import deserialize_component

        e = cls.__new__(cls)
        e.id = data.get("id", str(uuid.uuid4()))
        e.name = data.get("name", "Entity")
        e.scene = scene
        e.enabled = data.get("enabled", True)
        e.tags = data.get("tags", [])
        e._components = []

        for comp_data in data.get("components", []):
            comp = deserialize_component(comp_data)
            if comp:
                e._attach(comp)

        # ensure transform exists
        if not e.has_component(Transform):
            e._transform = Transform()
            e._attach(e._transform)
        else:
            e._transform = e.get_component(Transform)
        return e

    def __repr__(self) -> str:
        return f"<Entity '{self.name}' id={self.id[:8]}>"
