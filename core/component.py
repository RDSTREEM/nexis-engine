from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.entity import Entity


class Component:
    """Base class for all components attached to an Entity."""

    def __init__(self):
        self.entity: "Entity | None" = None
        self.enabled: bool = True

    # -- lifecycle hooks (overridden by subclasses) --

    def on_attach(self) -> None:
        """Called when this component is added to an entity."""

    def on_detach(self) -> None:
        """Called when this component is removed from an entity."""

    def on_start(self) -> None:
        """Called once when play mode begins."""

    def on_update(self, delta_time: float) -> None:
        """Called every frame in play mode."""

    def on_stop(self) -> None:
        """Called when play mode ends."""

    def to_dict(self) -> dict:
        """Serialize component state for scene saving."""
        return {"type": self.__class__.__name__, "enabled": self.enabled}

    @classmethod
    def from_dict(cls, data: dict) -> "Component":
        """Deserialize component — subclasses override this."""
        instance = cls()
        instance.enabled = data.get("enabled", True)
        return instance

    def __repr__(self) -> str:
        entity_name = self.entity.name if self.entity else "unattached"
        return f"<{self.__class__.__name__} on '{entity_name}'>"
